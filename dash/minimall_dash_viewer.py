from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import nibabel as nib
import kimimaro
from skimage.morphology import skeletonize

# Function to load labels


def load_labels(filepath):
    """Load the label data from a NIfTI file."""
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)
    return labels


def plot_volume(labels, alpha=0.01):
    """Plot the original volume in a 3D Plotly scatter plot."""
    volume = np.where(labels)

    scatter_volume = go.Scatter3d(
        x=volume[0],
        y=volume[1],
        z=volume[2],
        mode='markers',
        marker=dict(
            size=2,
            color='black',
            opacity=alpha
        ),
        name="Volume"
    )

    return scatter_volume


def plot_z_slice(labels, slice_index):
    """Plot a 2D slice of the labels along the Z-axis."""
    z_slice = labels[:, :, slice_index]
    x, y = np.where(z_slice)

    scatter_slice = go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(
            size=2,
            color='blue'
        ),
        name=f"Z Slice at Z={slice_index}",
        # Store coordinates for click events
        customdata=np.stack([x, y], axis=-1)
    )

    return scatter_slice


# Dash app
app = Dash(__name__)

# Load labels and set anisotropy parameters
LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
ANISOTROPY = (900, 900, 5000)
labels = load_labels(LABELS_FILEPATH)
scatter_volume = plot_volume(labels)

# Skeletonization
skeletonization_results = {
    'labels': labels,
    # 'scatter_thinning': scatter_thinning,
    'scatter_volume': scatter_volume,
    # 'skeleton_traces': skeleton_traces
}

# App layout
app.layout = html.Div([
    # html.H4('3D Skeletonization with Interactive Z-Slice and Point Click'),
    dcc.Graph(id='3d-scatter-plot',
              figure={

                  'data': [scatter_volume],
                  'layout': go.Layout(
                      title='3D Scatter Plot of Volume',
                      #   width=800  # Set the width of the figure here
                      height=800,
                  )
              },
              style={'width': '45%'}  # Adjust the width of the container here
              ),
    # html.P("Z Slice:"),
    dcc.Graph(
        id='2d-slice-plot',
        style={'width': '45%'}  # Adjust the width of the container here
    ),
    # Dynamically set max value of Z-slice slider based on the loaded labels
    # TODO change. Commented out
    dcc.Slider(id="z-slider", min=0,
               max=labels.shape[2] - 1, value=0, step=1),
    # dcc.Slider(id="z-slider", min=0, max=49 - 1, value=0, step=1),
    # New Div to display the coordinates of clicked points
    # html.Div(id='click-output')
])


# @ app.callback(
#     # Output('2d-slice-plot', 'figure'),
#     Input('3d-scatter-plot', 'clickData')
# )
# # Output("skeleton-graph", "figure"),
# # Output to update the coordinates display
# # Output("click-output", "children"),
# # [Input("z-slider", "value")])
# def update_skeleton_plot(slice_index):
#     # print('called')
#     # Create subplot for 3D skeleton and 2D slice
#     fig = make_subplots(
#         rows=1, cols=2,
#         specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}]],
#         subplot_titles=("3D Skeletonization", f"Z Slice {slice_index}")
#     )

#     fig.add_trace(skeletonization_results['scatter_volume'], row=1, col=1)
#     fig.add_trace(plot_z_slice(
#         skeletonization_results['labels'], slice_index), row=1, col=2)

#     clicked_coordinates = "Click on a point to see the coordinates."
#     return fig, clicked_coordinates

@app.callback(
    Output('2d-slice-plot', 'figure'),
    Input('z-slider', 'value')
)
def update_slice_plot(slider_value):
    scatter_slice = plot_z_slice(labels, slider_value)

    return {
        'data': [scatter_slice],
        'layout': go.Layout(
            title=f'2D Slice at Z={slider_value}',
            width=800
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
