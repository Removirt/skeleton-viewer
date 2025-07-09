# 3D Skeleton Visualization and Editing Tool

A comprehensive Dash-based web application for visualizing and interactively editing 3D skeletal structures from medical imaging data.

## Overview

This tool provides an interactive interface for viewing and modifying 3D skeletons extracted from medical imaging volumes. It supports real-time visualization of both the original volume data and derived skeletal structures, with capabilities for manual editing and refinement.

## Data Storage and Access

### Input Data Format

- **Labels File**: NIfTI format (`.nii` or `.nii.gz`) containing labeled voxel data
- **Skeleton File**: JSON format containing skeleton point coordinates (optional)

### Data Access Patterns

1. **Automatic File Discovery**: When only a labels file is provided, the app automatically searches for corresponding skeleton files using naming conventions
2. **Explicit File Paths**: Both labels and skeleton files can be specified directly via command-line arguments

### Skeleton Data Structure

Skeleton data is stored as JSON arrays containing 3D coordinates:

```json
[
  [x1, y1, z1],
  [x2, y2, z2],
  ...
]
```

## Features

### Core Functionality

- **3D Volume Visualization**: Interactive 3D scatter plot of the original labeled volume
- **Skeleton Overlay**: Real-time display of skeletal structures on top of volume data
- **Cross-sectional Views**: 2D slice visualization with synchronized skeleton points
- **Interactive Editing**: Click-to-add/remove skeleton points directly on 2D slices

### User Interface

- **Dual-panel Layout**: Side-by-side 3D and 2D views for comprehensive analysis
- **Z-axis Navigation**: Slider control for browsing through volume slices
- **Camera Persistence**: Maintains 3D view orientation during interactions
- **Real-time Updates**: Immediate visual feedback for all editing operations

## Usage

### Command Line Interface

```bash
# Basic usage with labels file only
python minimall_dash_viewer.py /path/to/labels.nii.gz

# Specify both labels and skeleton files
python minimall_dash_viewer.py /path/to/labels.nii.gz --skeleton_filepath /path/to/skeleton.json
```

### Interactive Operations

1. **Navigation**: Use the Z-slider to navigate through volume slices
2. **Editing**: Click on the 2D slice view to add/remove skeleton points
3. **Saving**: Click "Save Skeleton" button to persist changes
4. **3D Exploration**: Rotate, zoom, and pan the 3D view for detailed analysis

## Technical Details

### Dependencies

- **Dash**: Web application framework
- **Plotly**: Interactive plotting and visualization
- **NiBabel**: NIfTI file format support
- **NumPy**: Numerical computations
- **scikit-image**: Image processing and skeletonization

### Performance Considerations

- Volume data is downsampled for display to maintain responsiveness
- Skeleton points are stored in memory for real-time editing
- 3D rendering uses optimized marker sizes and opacity levels

### File Naming Conventions

The application uses intelligent file naming:

- Skeleton files: `modified_skeleton_{number}.json`
- Automatic number extraction from input filenames
- Fallback to default naming when extraction fails
