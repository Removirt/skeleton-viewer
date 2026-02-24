"""
multi_viewer.py – Multi-volume 3D skeleton / segmentation viewer.

Features
--------
* Display multiple volumes (segmentations) and annotations (skeletons)
  simultaneously in a single 3D scatter plot.
* Dynamically load / remove NIfTI segmentations and skeleton files
  (JSON or NIfTI) from the web UI without restarting the server.
* Toggle visibility per layer through a checklist.
* No 2D-slice view or editing – pure 3D visualisation.
* Importable: use ``from multi_viewer import MultiViewer`` in any script.

Usage from the command line
---------------------------
    python multi_viewer.py                          # empty viewer
    python multi_viewer.py seg.nii.gz               # open with one volume
    python multi_viewer.py seg.nii.gz --skeleton sk.json  # volume + skeleton

Usage as a library
------------------
    from multi_viewer import MultiViewer

    viewer = MultiViewer()
    viewer.add_volume("path/to/seg.nii.gz")
    viewer.add_skeleton("path/to/skeleton.json")
    viewer.run()                       # blocking – opens browser
    # or
    viewer.run(port=8051, open_browser=False)
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
import webbrowser
from threading import Timer
from typing import Optional

import nibabel as nib
import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback_context, dcc, html, no_update

# ---------------------------------------------------------------------------
# Colour palette for auto-assigning colours to layers
# ---------------------------------------------------------------------------
_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
]

# ---------------------------------------------------------------------------
# Data-loading helpers (reused from the original viewer)
# ---------------------------------------------------------------------------


def _load_nifti_volume(filepath: str) -> np.ndarray:
    """Load a NIfTI segmentation and return a binary uint8 array."""
    data = nib.load(filepath).get_fdata().astype(np.uint8)
    data[data > 1] = 0
    return data


def _load_skeleton(filepath: str) -> np.ndarray:
    """Load skeleton points from a JSON or NIfTI file.

    Returns an (N, 3) int array of coordinates.
    """
    if filepath.endswith(".json"):
        with open(filepath) as f:
            pts = json.load(f)
        return np.array(pts, dtype=int)

    # Assume NIfTI
    data = nib.load(filepath).get_fdata()
    coords = np.argwhere(data != 0).astype(int)
    return coords


# ---------------------------------------------------------------------------
# Layer dataclass-like dict helpers
# ---------------------------------------------------------------------------

def _make_layer(
    name: str,
    kind: str,           # "volume" or "skeleton"
    filepath: str,
    colour: str,
    opacity: float,
    marker_size: int,
    points: np.ndarray,  # (N, 3)
) -> dict:
    return dict(
        id=uuid.uuid4().hex[:8],
        name=name,
        kind=kind,
        filepath=filepath,
        colour=colour,
        opacity=opacity,
        marker_size=marker_size,
        points=points,
    )


# ---------------------------------------------------------------------------
# MultiViewer class
# ---------------------------------------------------------------------------

class MultiViewer:
    """Dash-based 3D viewer that can hold many volumes and skeletons."""

    def __init__(self):
        self._layers: list[dict] = []
        self._colour_idx = 0
        self._app: Optional[Dash] = None

    # -- public API for adding data before or after .run() ----------------

    def add_volume(
        self,
        filepath: str,
        name: str | None = None,
        colour: str | None = None,
        opacity: float = 0.05,
        marker_size: int = 2,
    ) -> str:
        """Load a NIfTI segmentation and add it as a volume layer.

        Returns the layer id.
        """
        data = _load_nifti_volume(filepath)
        pts = np.column_stack(np.where(data == 1))
        if name is None:
            name = os.path.basename(filepath)
        if colour is None:
            colour = self._next_colour()
        layer = _make_layer(name, "volume", filepath, colour, opacity, marker_size, pts)
        self._layers.append(layer)
        return layer["id"]

    def add_skeleton(
        self,
        filepath: str,
        name: str | None = None,
        colour: str | None = None,
        opacity: float = 0.8,
        marker_size: int = 2,
    ) -> str:
        """Load a skeleton (JSON or NIfTI) and add it as a skeleton layer.

        Returns the layer id.
        """
        pts = _load_skeleton(filepath)
        if name is None:
            name = os.path.basename(filepath)
        if colour is None:
            colour = self._next_colour()
        layer = _make_layer(name, "skeleton", filepath, colour, opacity, marker_size, pts)
        self._layers.append(layer)
        return layer["id"]

    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer by its id. Returns True if found."""
        before = len(self._layers)
        self._layers = [l for l in self._layers if l["id"] != layer_id]
        return len(self._layers) < before

    def list_layers(self) -> list[dict]:
        """Return a summary list of current layers (without heavy point data)."""
        return [
            {k: v for k, v in l.items() if k != "points"}
            for l in self._layers
        ]

    # -- Dash app construction --------------------------------------------

    def _build_app(self) -> Dash:
        app = Dash(__name__, suppress_callback_exceptions=True)

        app.layout = html.Div(
            style={"fontFamily": "Arial, sans-serif"},
            children=[
                # ---- Header ----
                html.H2("Multi-Volume 3D Viewer",
                         style={"textAlign": "center", "margin": "10px"}),

                # ---- Controls row ----
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "10px",
                        "padding": "10px",
                        "alignItems": "flex-end",
                        "flexWrap": "wrap",
                    },
                    children=[
                        # File path input
                        html.Div([
                            html.Label("File path"),
                            dcc.Input(
                                id="input-filepath",
                                type="text",
                                placeholder="/path/to/file.nii.gz or .json",
                                style={"width": "400px"},
                            ),
                        ]),
                        # Layer type selector
                        html.Div([
                            html.Label("Type"),
                            dcc.Dropdown(
                                id="input-type",
                                options=[
                                    {"label": "Volume (segmentation)", "value": "volume"},
                                    {"label": "Skeleton", "value": "skeleton"},
                                ],
                                value="volume",
                                clearable=False,
                                style={"width": "200px"},
                            ),
                        ]),
                        # Custom display name
                        html.Div([
                            html.Label("Display name (optional)"),
                            dcc.Input(
                                id="input-name",
                                type="text",
                                placeholder="auto",
                                style={"width": "160px"},
                            ),
                        ]),
                        # Colour picker
                        html.Div([
                            html.Label("Colour"),
                            dcc.Input(
                                id="input-colour",
                                type="text",
                                placeholder="auto",
                                style={"width": "100px"},
                            ),
                        ]),
                        # Opacity
                        html.Div([
                            html.Label("Opacity"),
                            dcc.Input(
                                id="input-opacity",
                                type="number",
                                min=0, max=1, step=0.01,
                                value=None,
                                placeholder="auto",
                                style={"width": "80px"},
                            ),
                        ]),
                        # Marker size
                        html.Div([
                            html.Label("Marker size"),
                            dcc.Input(
                                id="input-marker-size",
                                type="number",
                                min=1, max=20, step=1,
                                value=2,
                                style={"width": "60px"},
                            ),
                        ]),
                        # Buttons
                        html.Button("Add layer", id="btn-add",
                                    style={"height": "36px"}),
                        html.Button("Remove selected", id="btn-remove",
                                    style={"height": "36px"}),
                    ],
                ),

                # ---- Scale controls row ----
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "10px",
                        "padding": "4px 10px",
                        "alignItems": "flex-end",
                        "flexWrap": "wrap",
                    },
                    children=[
                        html.Div([
                            html.Label("Axis scale mode"),
                            dcc.Dropdown(
                                id="input-scale-mode",
                                options=[
                                    {"label": "Data (proportional to ranges)",
                                     "value": "data"},
                                    {"label": "Cube (equal size on all axes)",
                                     "value": "cube"},
                                    {"label": "Equal (same unit length)",
                                     "value": "equal"},
                                    {"label": "Manual", "value": "manual"},
                                ],
                                value="data",
                                clearable=False,
                                style={"width": "260px"},
                            ),
                        ]),
                        html.Div(
                            id="manual-scale-inputs",
                            style={"display": "flex", "gap": "6px"},
                            children=[
                                html.Div([
                                    html.Label("X ratio"),
                                    dcc.Input(id="input-scale-x", type="number",
                                              min=0.01, step=0.1, value=1,
                                              style={"width": "60px"}),
                                ]),
                                html.Div([
                                    html.Label("Y ratio"),
                                    dcc.Input(id="input-scale-y", type="number",
                                              min=0.01, step=0.1, value=1,
                                              style={"width": "60px"}),
                                ]),
                                html.Div([
                                    html.Label("Z ratio"),
                                    dcc.Input(id="input-scale-z", type="number",
                                              min=0.01, step=0.1, value=1,
                                              style={"width": "60px"}),
                                ]),
                            ],
                        ),
                    ],
                ),

                # ---- Status message ----
                html.Div(id="status-msg",
                         style={"padding": "5px 10px", "color": "#555"}),

                # ---- Main content: layer list + 3D plot ----
                html.Div(
                    style={"display": "flex", "width": "100%"},
                    children=[
                        # Layer sidebar
                        html.Div(
                            style={
                                "width": "260px",
                                "padding": "10px",
                                "borderRight": "1px solid #ccc",
                                "overflowY": "auto",
                                "maxHeight": "850px",
                            },
                            children=[
                                html.H4("Layers"),
                                dcc.Checklist(
                                    id="layer-checklist",
                                    options=[],
                                    value=[],
                                    labelStyle={"display": "block",
                                                "marginBottom": "4px"},
                                ),
                            ],
                        ),
                        # 3D plot
                        dcc.Graph(
                            id="3d-plot",
                            figure=go.Figure(
                                layout=go.Layout(
                                    title="3D View",
                                    height=850,
                                    scene=dict(aspectmode="data"),
                                )
                            ),
                            style={"flex": "1"},
                        ),
                    ],
                ),

                # Hidden store that keeps the canonical layer-id list in sync
                dcc.Store(id="layer-store", data=[]),
            ],
        )

        # ---- Callbacks ----

        @app.callback(
            Output("manual-scale-inputs", "style"),
            Input("input-scale-mode", "value"),
        )
        def _toggle_manual_inputs(mode):
            """Show manual X/Y/Z ratio inputs only when mode is 'manual'."""
            if mode == "manual":
                return {"display": "flex", "gap": "6px"}
            return {"display": "none"}

        @app.callback(
            Output("layer-store", "data"),
            Output("status-msg", "children"),
            Input("btn-add", "n_clicks"),
            Input("btn-remove", "n_clicks"),
            State("input-filepath", "value"),
            State("input-type", "value"),
            State("input-name", "value"),
            State("input-colour", "value"),
            State("input-opacity", "value"),
            State("input-marker-size", "value"),
            State("layer-checklist", "value"),
            State("layer-store", "data"),
            prevent_initial_call=True,
        )
        def _manage_layers(
            add_clicks, remove_clicks,
            filepath, kind, name, colour, opacity, marker_size,
            selected_ids, store_data,
        ):
            """Add or remove layers depending on which button was pressed."""
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update

            trigger = ctx.triggered[0]["prop_id"].split(".")[0]

            # ---- Add ----
            if trigger == "btn-add":
                if not filepath or not filepath.strip():
                    return no_update, "⚠️  Please enter a file path."
                filepath = filepath.strip()
                if not os.path.isfile(filepath):
                    return no_update, f"⚠️  File not found: {filepath}"
                try:
                    # Resolve defaults
                    if not name or not name.strip():
                        name = None
                    if not colour or not colour.strip():
                        colour = None
                    if opacity is None:
                        opacity = 0.05 if kind == "volume" else 0.8
                    if marker_size is None:
                        marker_size = 2

                    if kind == "volume":
                        lid = self.add_volume(filepath, name=name,
                                              colour=colour, opacity=opacity,
                                              marker_size=int(marker_size))
                    else:
                        lid = self.add_skeleton(filepath, name=name,
                                                colour=colour, opacity=opacity,
                                                marker_size=int(marker_size))
                    new_store = [l["id"] for l in self._layers]
                    return new_store, f"✅  Added layer '{self._layers[-1]['name']}'"
                except Exception as exc:
                    return no_update, f"❌  Error loading file: {exc}"

            # ---- Remove ----
            if trigger == "btn-remove":
                if not selected_ids:
                    return no_update, "⚠️  Select layers to remove first."
                removed = []
                for lid in list(selected_ids):
                    layer = next((l for l in self._layers if l["id"] == lid), None)
                    if layer:
                        removed.append(layer["name"])
                    self.remove_layer(lid)
                new_store = [l["id"] for l in self._layers]
                return new_store, f"🗑️  Removed: {', '.join(removed)}"

            return no_update, no_update

        @app.callback(
            Output("layer-checklist", "options"),
            Output("layer-checklist", "value"),
            Input("layer-store", "data"),
            State("layer-checklist", "value"),
        )
        def _sync_checklist(store_data, prev_selected):
            """Keep the sidebar checklist in sync with internal layer list."""
            options = []
            for layer in self._layers:
                tag = "🟦" if layer["kind"] == "volume" else "🔴"
                label = f'{tag} {layer["name"]}  [{layer["kind"]}, {layer["colour"]}]'
                options.append({"label": label, "value": layer["id"]})
            # Preserve previous selection where ids still exist
            valid = {l["id"] for l in self._layers}
            value = [v for v in (prev_selected or []) if v in valid]
            return options, value

        @app.callback(
            Output("3d-plot", "figure"),
            Input("layer-store", "data"),
            Input("layer-checklist", "value"),
            Input("input-scale-mode", "value"),
            Input("input-scale-x", "value"),
            Input("input-scale-y", "value"),
            Input("input-scale-z", "value"),
            State("3d-plot", "relayoutData"),
        )
        def _update_3d(store_data, visible_ids, scale_mode,
                       scale_x, scale_y, scale_z, relayout):
            """Rebuild the 3D figure from all layers, toggling visibility."""
            traces = []
            visible_ids = set(visible_ids or [])

            for layer in self._layers:
                pts = layer["points"]
                if pts is None or len(pts) == 0:
                    continue
                visible = layer["id"] in visible_ids
                traces.append(
                    go.Scatter3d(
                        x=pts[:, 0],
                        y=pts[:, 1],
                        z=pts[:, 2],
                        mode="markers",
                        marker=dict(
                            size=layer["marker_size"],
                            color=layer["colour"],
                            opacity=layer["opacity"],
                        ),
                        name=layer["name"],
                        visible=True if visible else "legendonly",
                    )
                )

            # Build scene dict based on scale mode
            # Plotly aspectmode: "data" | "cube" | "auto" | "manual"
            # "equal" is not a native Plotly mode; we emulate it by
            # computing the data ranges and setting manual ratios so that
            # one unit in each axis occupies the same screen length.
            scene = dict()

            if scale_mode == "manual":
                sx = max(float(scale_x or 1), 0.01)
                sy = max(float(scale_y or 1), 0.01)
                sz = max(float(scale_z or 1), 0.01)
                scene["aspectmode"] = "manual"
                scene["aspectratio"] = dict(x=sx, y=sy, z=sz)
            elif scale_mode == "cube":
                scene["aspectmode"] = "cube"
            elif scale_mode == "equal":
                # Compute ranges from all visible points and set manual
                # ratios proportional to those ranges so that one data
                # unit is the same length on every axis.
                all_pts = [l["points"] for l in self._layers
                           if l["points"] is not None and len(l["points"]) > 0]
                if all_pts:
                    combined = np.concatenate(all_pts, axis=0)
                    ranges = combined.max(axis=0) - combined.min(axis=0)
                    ranges = np.where(ranges == 0, 1, ranges)  # avoid zero
                    max_range = ranges.max()
                    scene["aspectmode"] = "manual"
                    scene["aspectratio"] = dict(
                        x=float(ranges[0] / max_range),
                        y=float(ranges[1] / max_range),
                        z=float(ranges[2] / max_range),
                    )
                else:
                    scene["aspectmode"] = "data"
            else:
                # "data" – proportional to data ranges (default)
                scene["aspectmode"] = "data"

            layout = go.Layout(
                title="3D View",
                height=850,
                scene=scene,
            )
            # Preserve camera if the user has panned / zoomed
            if relayout and "scene.camera" in relayout:
                layout.scene.camera = relayout["scene.camera"]

            return go.Figure(data=traces, layout=layout)

        self._app = app
        return app

    # -- Run --------------------------------------------------------------

    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8050,
        debug: bool = True,
        open_browser: bool = True,
    ):
        """Start the Dash server (blocking)."""
        app = self._build_app()
        if open_browser:
            Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
        app.run(host=host, port=port, debug=debug)

    # -- Internal helpers --------------------------------------------------

    _PALETTE_LEN = len(_PALETTE)

    def _next_colour(self) -> str:
        c = _PALETTE[self._colour_idx % self._PALETTE_LEN]
        self._colour_idx += 1
        return c


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Multi-volume 3D skeleton / segmentation viewer."
    )
    parser.add_argument(
        "volumes",
        nargs="*",
        help="NIfTI segmentation file(s) to display on start-up.",
    )
    parser.add_argument(
        "--skeleton", "-s",
        action="append",
        default=[],
        help="Skeleton file(s) (JSON or NIfTI) to display. Can be repeated.",
    )
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    viewer = MultiViewer()

    for vol_path in args.volumes:
        viewer.add_volume(vol_path)
        print(f"Loaded volume: {vol_path}")

    for sk_path in args.skeleton:
        viewer.add_skeleton(sk_path)
        print(f"Loaded skeleton: {sk_path}")

    viewer.run(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
