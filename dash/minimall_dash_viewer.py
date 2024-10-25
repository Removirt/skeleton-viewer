from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
import nibabel as nib

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
        name=f"Z Slice {slice_index}"
    )

    return scatter_slice


# Dash app
app = Dash(__name__)

# Load labels and set anisotropy parameters
LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
labels = load_labels(LABELS_FILEPATH)
scatter_volume = plot_volume(labels)

# Skeletonization
skeletonization_results = {
    'labels': labels,
    'scatter_volume': scatter_volume,
}

# App layout
app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='3d-scatter-plot',
            figure={
                'data': [scatter_volume],
                'layout': go.Layout(
                    title='3D Scatter Plot of Volume',
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


@app.callback(
    # Output('output', 'children'),
    Input('2d-slice-plot', 'clickData')
)
def display_click_data(clickData):
    if clickData:
        point = clickData['points'][0]
        x = point['x']
        y = point['y']
        # print(f"Clicked point: x={x}, y={y}")
        print(point)
        # print(clickData['points'])
    # return ""

if __name__ == '__main__':
    app.run_server(debug=True)
