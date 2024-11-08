import os
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
import nibabel as nib
from skimage.morphology import skeletonize
import json

# Function to load label data from a NIfTI file
def load_labels(filepath):
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)
    return labels

# Plot the original volume in a 3D scatter plot
def plot_volume(labels, alpha=0.05):
    volume = np.where(labels)
    scatter_volume = go.Scatter3d(
        x=volume[0], y=volume[1], z=volume[2],
        mode='markers',
        marker=dict(size=2, color='black', opacity=alpha),
        name="Volume"
    )
    return scatter_volume

# Plot a 2D slice of the labels along the Z-axis
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

# Perform skeletonization and return the thinned structure as a set of points
def load_thinning(labels):
    skeleton = skeletonize(labels)
    skeleton_points = np.array(np.where(skeleton)).T
    return skeleton_points

# Save skeleton points to a JSON file
def save_skeleton(skeleton_points, filename="modified_skeleton.json"):
    with open(filename, 'w') as f:
        json.dump(skeleton_points, f)
    print(f"Skeleton saved to {filename}")

# Dash app initialization
app = Dash(__name__)

# Load the labels and skeleton data
LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
labels = load_labels(LABELS_FILEPATH)
scatter_volume = plot_volume(labels)

# Load skeleton from json file if it exists
if os.path.exists("modified_skeleton.json"):
    skeleton_points = np.array(json.load(open("modified_skeleton.json")))
else:
    skeleton_points = load_thinning(labels)

# Store skeleton points in a mutable list
skeleton_points_list = skeleton_points.tolist()

# Plot the skeleton in 3D
scatter_skeleton_3d = go.Scatter3d(
    x=skeleton_points[:, 0], y=skeleton_points[:, 1], z=skeleton_points[:, 2],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.5),
    name="Skeleton"
)

# Skeletonization results dictionary
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

# Combined callback to update the 2D Z-slice plot and handle click interactions
@app.callback(
    Output('2d-slice-plot', 'figure'),
    [Input('z-slider', 'value'), Input('2d-slice-plot', 'clickData')]
)
def update_slice_and_handle_click(slider_value, clickData):
    global z_slice
    z_slice = slider_value

    # Update the Z slice plot
    scatter_slice = plot_z_slice(labels, slider_value)

    # Filter skeleton points to show only those in the current Z slice
    slice_skeleton_points = np.array(
        skeletonization_results['skeleton_points'])
    slice_skeleton_points = slice_skeleton_points[slice_skeleton_points[:, 2] == slider_value]

    # Create scatter plot of skeleton points in the Z slice
    if len(slice_skeleton_points) > 0:
        scatter_skeleton_slice = go.Scatter(
            x=slice_skeleton_points[:, 0],
            y=slice_skeleton_points[:, 1],
            mode='markers',
            marker=dict(size=2, color='red'),
            name="Skeleton Slice"
        )
        data = [scatter_slice, scatter_skeleton_slice]
    else:
        data = [scatter_slice]

    # Check if a click event occurred and process it
    if clickData:
        point_data = clickData['points'][0]
        x = int(point_data['x'])
        y = int(point_data['y'])
        z = slider_value
        point = [x, y, z]

        # Check if the point is already in the skeleton
        if point in skeletonization_results['skeleton_points']:
            # Remove point if it exists
            skeletonization_results['skeleton_points'].remove(point)
            print(f"Removed point from skeleton: {point}")
        else:
            # Add point if it doesn't exist
            skeletonization_results['skeleton_points'].append(point)
            print(f"Added point to skeleton: {point}")

        # Update skeleton points in the current Z slice after modification
        slice_skeleton_points = np.array(
            skeletonization_results['skeleton_points'])
        slice_skeleton_points = slice_skeleton_points[slice_skeleton_points[:, 2] == slider_value]

        # Update the plot with modified skeleton points
        if len(slice_skeleton_points) > 0:
            scatter_skeleton_slice = go.Scatter(
                x=slice_skeleton_points[:, 0],
                y=slice_skeleton_points[:, 1],
                mode='markers',
                marker=dict(size=2, color='red'),
                name="Skeleton Slice"
            )
            data = [scatter_slice, scatter_skeleton_slice]
        else:
            data = [scatter_slice]

    return {
        'data': data,
        'layout': go.Layout(
            title=f'2D Slice at Z={slider_value}',
            width=800
        )
    }

# Callback to save modified skeleton when Save button is clicked
@app.callback(
    Output("save-message", "children"),
    Input("save-button", "n_clicks")
)
def save_skeleton_points(n_clicks):
    if n_clicks > 0:
        save_skeleton(skeletonization_results['skeleton_points'])
        return "Skeleton saved successfully!"
    return ""

if __name__ == '__main__':
    app.run_server(debug=True)
