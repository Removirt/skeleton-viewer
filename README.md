# 3D Skeleton Visualization and Editing Tool

A comprehensive Dash-based web application for visualizing and interactively editing 3D skeletal structures from medical imaging data.

## Overview

This tool provides an interactive interface for viewing and modifying 3D skeletons extracted from medical imaging volumes. It supports real-time visualization of both the original volume data and derived skeletal structures, with capabilities for manual editing and refinement.

## Data Storage and Access

### Input Data Format

The application accepts NIfTI format files (`.nii` or `.nii.gz`) containing labeled voxel data as the primary input. Skeleton files in JSON format containing skeleton point coordinates are optional. When no skeleton file is provided, the application automatically generates a 3D skeleton using scikit-image's morphological skeletonization algorithm.

### Data Access Patterns

The application supports flexible data access through automatic file discovery when only a labels file is provided, searching for corresponding skeleton files using intelligent naming conventions. Alternatively, both labels and skeleton files can be specified directly via command-line arguments for explicit control over data sources.

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

The application provides interactive 3D scatter plot visualization of the original labeled volume with real-time display of skeletal structures overlaid on top of volume data. Cross-sectional views enable 2D slice visualization with synchronized skeleton points, while interactive editing allows users to click-to-add or remove skeleton points directly on 2D slices.

### User Interface

The interface features a dual-panel layout with side-by-side 3D and 2D views for comprehensive analysis. Z-axis navigation through a slider control enables browsing through volume slices, while camera persistence maintains 3D view orientation during interactions. All operations provide immediate visual feedback with real-time updates.

## Usage

### Command Line Interface

```bash
# Basic usage with labels file only
python minimall_dash_viewer.py /path/to/labels.nii.gz

# Specify both labels and skeleton files
python minimall_dash_viewer.py /path/to/labels.nii.gz --skeleton_filepath /path/to/skeleton.json
```

### Interactive Operations

Navigate through volume slices using the Z-slider control. Edit skeleton points by clicking on the 2D slice view to add or remove points. Save modifications by clicking the "Save Skeleton" button to persist changes. Explore the 3D view by rotating, zooming, and panning for detailed analysis.

## Technical Details

### Dependencies

The application requires Dash for the web application framework, Plotly for interactive plotting and visualization, NiBabel for NIfTI file format support, NumPy for numerical computations, and scikit-image for image processing and automatic skeletonization.

### File Naming Conventions

The application uses intelligent file naming with skeleton files following the pattern `modified_skeleton_{number}.json`. Automatic number extraction from input filenames provides consistent naming, with fallback to default naming when extraction fails.
