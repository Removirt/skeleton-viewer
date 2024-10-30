from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
import nibabel as nib
from skimage.morphology import skeletonize

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

# Dash app initialization
app = Dash(__name__)

# Load the labels and skeleton data
LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
labels = load_labels(LABELS_FILEPATH)
scatter_volume = plot_volume(labels)
skeleton_points = load_thinning(labels)

# Plot the skeleton in 3D
scatter_skeleton_3d = go.Scatter3d(
    x=skeleton_points[:, 0], y=skeleton_points[:, 1], z=skeleton_points[:, 2],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.2),
    name="Skeleton"
)

# Skeletonization results dictionary
skeletonization_results = {
    'labels': labels,
    'scatter_volume': scatter_volume,
    'scatter_skeleton': scatter_skeleton_3d,
    'skeleton_points': skeleton_points
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
    )
])

# Callback to update the 2D Z-slice plot with both the volume and the skeleton
@app.callback(
    Output('2d-slice-plot', 'figure'),
    Input('z-slider', 'value')
)
def update_slice_plot(slider_value):
    global z_slice
    z_slice = slider_value

    # Plot the 2D slice of the volume
    scatter_slice = plot_z_slice(labels, slider_value)

    # Filter skeleton points to show only those in the current Z slice
    slice_skeleton_points = skeleton_points[skeleton_points[:, 2]
                                            == slider_value]
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

# Callback to handle click data (currently only logs the click data)
@app.callback(
    # Output('output', 'children'),
    Input('2d-slice-plot', 'clickData')
)
def display_click_data(clickData):
    if clickData:
        point_data = clickData['points'][0]
        x = point_data['x']
        y = point_data['y']
        z = z_slice
        point = np.array((x, y, z))

        # Check if clicked point is in the skeleton
        is_in_skeleton = np.any(
            np.all(skeletonization_results['skeleton_points'] == point, axis=1))
        if is_in_skeleton:
            print("Clicked point is in the skeleton.")
        else:
            print("Clicked point is NOT in the skeleton.")

if __name__ == '__main__':
    app.run_server(debug=True)
