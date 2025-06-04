import os
from dash import Dash, dcc, html, Input, Output, State, no_update
import plotly.graph_objects as go
import numpy as np
import nibabel as nib
from skimage.morphology import skeletonize
import json
import argparse  # <-- New import for arguments

# Process command-line arguments
parser = argparse.ArgumentParser(
    description="Dash app for vessel skeleton visualization")
parser.add_argument("labels_filepath",
                    help="Path to the labels NIfTI file (mandatory).")
parser.add_argument("--skeleton_filepath",
                    help="Optional path to the skeleton JSON file.")
args = parser.parse_args()

labels_filepath = args.labels_filepath  # <-- Using the mandatory argument
if args.skeleton_filepath:
    skeleton_filepath = args.skeleton_filepath  # <-- If specified, use directly
else:
    try:
        base = os.path.basename(labels_filepath)
        # Remove known NIfTI extensions
        if base.endswith('.nii.gz'):
            base = base[:-7]  # <-- Removes '.nii.gz'
        elif base.endswith('.nii'):
            base = base[:-4]  # <-- Removes '.nii'
        parts = base.split('_')
        # Try to extract a number from the filename
        if parts[-1].isdigit():
            number = parts[-1]
        else:
            number = "default"
        skeleton_basename = f"modified_skeleton_{number}.json"
        skeleton_filepath = os.path.join(
            os.path.dirname(labels_filepath), skeleton_basename)
    except Exception as e:
        skeleton_filepath = "../data/default_modified_skeleton.json"

# Function to load label data from a NIfTI file


def load_labels(filepath):
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)

    # labels = np.where(labels==1)
    labels[labels > 1] = 0
    return labels

# Displays the original volume in a 3D scatter plot


def plot_volume(labels, alpha=0.05):
    volume = np.where(labels == 1)  # TODO Change to use load_index function
    scatter_volume = go.Scatter3d(
        x=volume[0], y=volume[1], z=volume[2],
        mode='markers',
        marker=dict(size=2, color='black', opacity=alpha),
        name="Volume"
    )
    return scatter_volume

# Displays a 2D slice of labels along the Z axis


def plot_z_slice(labels, slice_index):
    z_slice = labels[:, :, slice_index]
    x, y = np.where(z_slice)
    scatter_slice = go.Scatter(
        x=x, y=y,
        mode='markers',
        marker=dict(size=2, color='blue'),
        name=f"Z Slice {slice_index}"
    )
    return scatter_slice

# Performs skeletonization and returns the reduced structure as a set of points


def load_thinning(labels):
    skeleton = skeletonize(labels)
    skeleton_points = np.array(np.where(skeleton)).T
    return skeleton_points

# Saves skeleton points to a JSON file


def save_skeleton(skeleton_points, filename):
    with open(filename, 'w') as f:
        json.dump(skeleton_points, f)
    print(f"Skeleton saved to {filename}")

# Function to generate the 2D slice figure


def generate_slice_figure(slice_index, labels, skeleton_points):
    scatter_slice = plot_z_slice(labels, slice_index)
    # Filter skeleton points to show only those in the current Z slice
    slice_skeleton_points = np.array(skeleton_points)
    slice_skeleton_points = slice_skeleton_points[slice_skeleton_points[:, 2] == slice_index]

    # Create scatter plot for skeleton points in the Z slice
    data = [scatter_slice]
    if len(slice_skeleton_points) > 0:
        scatter_skeleton_slice = go.Scatter(
            x=slice_skeleton_points[:, 0],
            y=slice_skeleton_points[:, 1],
            mode='markers',
            marker=dict(size=2, color='red'),
            name="Skeleton Slice"
        )
        data.append(scatter_skeleton_slice)

    return {
        'data': data,
        'layout': go.Layout(
            title=f'2D Slice at Z={slice_index}',
            width=800
        )
    }


# Initialize the Dash app
app = Dash(__name__, prevent_initial_callbacks=True)

# Load label data and skeleton
labels = load_labels(labels_filepath)  # <-- Using the labels_filepath argument
scatter_volume = plot_volume(labels)

# Load skeleton from JSON file if it exists
if os.path.exists(skeleton_filepath):
    skeleton_points = np.array(json.load(open(skeleton_filepath)))
else:
    skeleton_points = load_thinning(labels)
    os.makedirs(os.path.dirname(skeleton_filepath),
                exist_ok=True)  # <-- Using skeleton_filepath

# Store skeleton points in a mutable list
skeleton_points_list = skeleton_points.tolist()

# Display the skeleton in 3D
scatter_skeleton_3d = go.Scatter3d(
    x=skeleton_points[:, 0], y=skeleton_points[:, 1], z=skeleton_points[:, 2],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.8),
    name="Skeleton"
)

# Dictionary with skeletonization results
skeletonization_results = {
    'labels': labels,
    'scatter_volume': scatter_volume,
    'scatter_skeleton': scatter_skeleton_3d,
    'skeleton_points': skeleton_points_list
}
z_slice = 0  # Initial Z slice

# App layout
app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='3d-scatter-plot',
            figure={
                'data': [scatter_volume, scatter_skeleton_3d],
                'layout': go.Layout(
                    title='3D Scatter Plot of Volume with Skeleton',
                    height=800,
                )
            },
            style={'width': '100%'}
        ),
        dcc.Graph(
            id='2d-slice-plot',
            style={'width': '100%'}
        ),
    ], style={'display': 'flex', 'width': '100%'}),
    dcc.Slider(
        id="z-slider",
        min=0,
        max=labels.shape[2] - 1,
        value=0,
        step=1
    ),
    html.Button("Save Skeleton", id="save-button", n_clicks=0),
    html.Div(id="save-message")
])


@app.callback(
    Output('2d-slice-plot', 'figure'),
    [Input('z-slider', 'value')],
    State('2d-slice-plot', 'relayoutData')
)
def update_slice(slider_value, relayoutData):
    global z_slice
    z_slice = slider_value
    figure = generate_slice_figure(
        z_slice, labels, skeletonization_results['skeleton_points'])
    if relayoutData:
        if 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
            figure['layout']['xaxis'] = {
                'range': [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]}
        if 'yaxis.range[0]' in relayoutData and 'yaxis.range[1]' in relayoutData:
            figure['layout']['yaxis'] = {
                'range': [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]}
    return figure

# Updated callback for handling clicks on the 2D slice plot


@app.callback(
    Output('2d-slice-plot', 'figure', allow_duplicate=True),
    [Input('2d-slice-plot', 'clickData')],
    [State('z-slider', 'value'),
     State('2d-slice-plot', 'relayoutData')]
)
def handle_click(clickData, slider_value, relayoutData):
    if clickData:
        point_data = clickData['points'][0]
        x, y = int(point_data['x']), int(point_data['y'])
        z = slider_value
        point = [x, y, z]
        if point in skeletonization_results['skeleton_points']:
            skeletonization_results['skeleton_points'].remove(point)
        else:
            skeletonization_results['skeleton_points'].append(point)
    figure = generate_slice_figure(
        slider_value, labels, skeletonization_results['skeleton_points'])
    if relayoutData:
        if 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
            figure['layout']['xaxis'] = {
                'range': [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]}
        if 'yaxis.range[0]' in relayoutData and 'yaxis.range[1]' in relayoutData:
            figure['layout']['yaxis'] = {
                'range': [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]}
    return figure

# Callback to save the modified skeleton points when clicking the Save button


@app.callback(
    Output("3d-scatter-plot", "figure"),
    [Input("save-button", "n_clicks"),
     Input("z-slider", "value")],
    [State("3d-scatter-plot", "relayoutData")]
)
def update_3d_plot(n_clicks, slider_value, relayoutData):
    global z_slice
    z_slice = slider_value

    # Update dark overlay for the selected slice
    slice_data = np.where(labels[:, :, slider_value] == 1)
    dark_slice = go.Scatter3d(
        x=slice_data[0],
        y=slice_data[1],
        z=np.full_like(slice_data[0], slider_value),
        mode='markers',
        marker=dict(size=2, color='blue', opacity=0.1),
        name=f"Slice {slider_value} Overlay"
    )

    # Update skeleton trace from the stored skeleton points
    skeleton_points = np.array(skeletonization_results['skeleton_points'])
    scatter_skeleton = go.Scatter3d(
        x=skeleton_points[:, 0],
        y=skeleton_points[:, 1],
        z=skeleton_points[:, 2],
        mode='markers',
        marker=dict(size=2, color='red', opacity=0.8),
        name="Skeleton"
    )
    skeletonization_results['scatter_skeleton'] = scatter_skeleton

    # If the save button was clicked, save the skeleton to file.
    if n_clicks > 0:
        save_skeleton(skeletonization_results['skeleton_points'], filename=skeleton_filepath)

    # Build the layout and preserve camera view if provided.
    layout = go.Layout(
        title='3D Scatter Plot of Volume with Modified Skeleton',
        height=800,
    )
    if relayoutData and 'scene.camera' in relayoutData:
        layout.scene = dict(camera=relayoutData['scene.camera'])

    return {
        'data': [scatter_volume, scatter_skeleton, dark_slice],
        'layout': layout
    }
    return no_update


if __name__ == '__main__':
    app.run_server(debug=True)
