# 3D Skeleton Visualization Tools

A collection of Dash-based web applications for visualizing and working with 3D skeletal structures from medical imaging data. The repository contains two complementary tools: an interactive single-volume editor and a multi-volume read-only viewer.

## Overview

These tools provide interactive interfaces for viewing 3D skeletons extracted from medical imaging volumes. The **editing viewer** (`minimall_dash_viewer.py`) supports real-time visualization of a single volume alongside its skeletal structure, with capabilities for manual point-by-point editing and refinement. The **multi-volume viewer** (`multi_viewer.py`) supports simultaneous display of multiple segmentations and skeleton annotations in a single 3D scene, with dynamic loading and removal of layers at runtime.

## Tools

### Editing Viewer (`minimall_dash_viewer.py`)

A single-volume viewer with interactive skeleton editing capabilities. It provides a dual-panel layout with side-by-side 3D and 2D slice views, allowing users to add or remove skeleton points directly on 2D cross-sections. Edits are reflected in the 3D plot in real time, and the selected Z slice is highlighted as a darker overlay in the 3D view. Camera persistence maintains 3D view orientation across all interactions.

### Multi-Volume Viewer (`multi_viewer.py`)

A read-only 3D viewer designed for comparing multiple volumes and annotations side by side in the same scene. Each loaded file becomes an independent layer with configurable colour, opacity, and marker size. Layers can be added or removed at any time through the web UI without restarting the server. A sidebar checklist controls per-layer visibility. The viewer is also importable as a Python module, enabling programmatic construction of visualisations from other scripts.

## Data Storage and Access

### Input Data Format

Both tools accept NIfTI format files (`.nii` or `.nii.gz`) containing labeled voxel data as the primary input for segmentations. Skeleton files can be provided in JSON format or as NIfTI files where non-zero voxels indicate skeleton points. When the editing viewer receives no skeleton file, it automatically generates a 3D skeleton using scikit-image's morphological skeletonization algorithm.

### Data Access Patterns

The editing viewer supports flexible data access through automatic file discovery when only a labels file is provided, searching for corresponding skeleton files using intelligent naming conventions. Alternatively, both labels and skeleton files can be specified directly via command-line arguments for explicit control over data sources. The multi-volume viewer relies on explicit file paths, either supplied as command-line arguments at launch or entered through the web interface at runtime.

### Skeleton Data Structure

Skeleton data stored as JSON uses arrays of 3D coordinates:

```json
[
  [x1, y1, z1],
  [x2, y2, z2],
  ...
]
```

When a skeleton is provided as a NIfTI file, any non-zero voxel is treated as a skeleton point.

## Usage

### Editing Viewer – Command Line Interface

```bash
# Basic usage with labels file only
python minimall_dash_viewer.py /path/to/labels.nii.gz

# Specify both labels and skeleton files
python minimall_dash_viewer.py /path/to/labels.nii.gz --skeleton_filepath /path/to/skeleton.json
```

### Editing Viewer – Interactive Operations

Navigate through volume slices using the Z-slider control. Edit skeleton points by clicking on the 2D slice view to add or remove points. Edit skeleton points on the 3D view by clicking directly on existing skeleton markers to remove them, or on volume voxels to add new points. Save modifications by clicking the "Save Skeleton" button to persist changes. Explore the 3D view by rotating, zooming, and panning for detailed analysis. The 2D slice view preserves zoom level across edits so that focused work on a specific region is not interrupted.

### Multi-Volume Viewer – Command Line Interface

```bash
# Launch an empty viewer and add files from the web UI
python multi_viewer.py

# Pre-load one volume
python multi_viewer.py /path/to/segmentation.nii.gz

# Pre-load multiple volumes and skeletons
python multi_viewer.py vol1.nii.gz vol2.nii.gz -s skeleton1.json -s skeleton2.nii.gz

# Specify a custom port and suppress automatic browser opening
python multi_viewer.py vol.nii.gz --port 8051 --no-browser
```

### Multi-Volume Viewer – Python API

The multi-volume viewer can be imported as a module and used programmatically from any Python script:

```python
from multi_viewer import MultiViewer

viewer = MultiViewer()
viewer.add_volume("data/hepaticvessel_001.nii.gz")
viewer.add_skeleton("data/modified_skeleton_001.json", colour="red")
viewer.add_skeleton("another_skeleton.nii.gz", name="Alt skeleton", colour="green")
viewer.run(port=8051, open_browser=False)
```

The `add_volume` and `add_skeleton` methods accept optional `name`, `colour`, `opacity`, and `marker_size` parameters. The `list_layers` and `remove_layer` methods provide programmatic control over loaded data.

### Multi-Volume Viewer – Interactive Operations

Enter a file path in the input field at the top of the page and select whether it is a volume or skeleton. Click "Add layer" to load it into the scene. Control visibility of each layer through the sidebar checklist. Select layers in the checklist and click "Remove selected" to discard them. The 3D camera view is preserved across all layer additions, removals, and visibility toggles.

## Technical Details

### Dependencies

Both tools require Dash for the web application framework, Plotly for interactive plotting and visualization, NiBabel for NIfTI file format support, and NumPy for numerical computations. The editing viewer additionally requires scikit-image for image processing and automatic skeletonization.

### File Naming Conventions

The editing viewer uses intelligent file naming with skeleton files following the pattern `modified_skeleton_{number}.json`. Automatic number extraction from input filenames provides consistent naming, with fallback to default naming when extraction fails. The multi-volume viewer does not impose any naming conventions and accepts arbitrary file paths.
