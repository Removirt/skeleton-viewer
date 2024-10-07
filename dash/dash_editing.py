import dash
from dash import Dash, dcc, html, Input, Output
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import nibabel as nib
import kimimaro
from skimage.morphology import skeletonize

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='skeleton-graph'),
    dcc.Slider(id='z-slider', min=0, max=100, step=1, value=50),
    html.Div([
        html.Button('Add Point', id='add-point-btn'),
        html.Button('Move Point', id='move-point-btn'),
        html.Button('Delete Point', id='delete-point-btn'),
        dcc.Input(id='point-coordinates', type='text', placeholder='x,y,z'),
        dcc.Input(id='new-coordinates', type='text', placeholder='new x,y,z')
    ])
])

# Function to load labels
def load_labels(filepath):
    """Load the label data from a NIfTI file."""
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)
    return labels

# Function to plot thinning result
def plot_thinning(labels):
    """Plot the thinning result in a 3D Plotly scatter plot."""
    thinning = np.where(skeletonize(labels))
    
    scatter_thinning = go.Scatter3d(
        x=thinning[0],
        y=thinning[1],
        z=thinning[2],
        mode='markers',
        marker=dict(
            size=2,
            color='red',
            opacity=0.6
        ),
        name="Thinning"
    )
    
    return scatter_thinning

# Function to plot original volume
def plot_volume(labels):
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
            opacity=0.1
        ),
        name="Volume"
    )
    
    return scatter_volume

# Function to perform skeletonization using Kimimaro
def skeletonize_labels(labels, anisotropy):
    """Perform skeletonization using Kimimaro."""
    skeleton_list = kimimaro.skeletonize(
        labels,
        teasar_params={
            "scale": 1.5,
            "const": 300,
            "pdrf_scale": 100000,
            "pdrf_exponent": 4,
            "soma_acceptance_threshold": 3500,
            "soma_detection_threshold": 750,
            "soma_invalidation_const": 300,
            "soma_invalidation_scale": 2,
            "max_paths": 3000,
        },
        dust_threshold=10,
        anisotropy=anisotropy,
        fix_branching=True,
        fix_borders=True,
        fill_holes=False,
        progress=True,
        parallel=1,
    )
    return skeleton_list

# Function to draw the skeleton
def draw_skeleton(skeleton_list, anisotropy):
    """Plot skeletons with edges and vertices in a 3D Plotly scatter plot."""
    skeleton_traces = []
    
    for label, skeleton in skeleton_list.items():
        # Adjust the vertices for anisotropy
        skeleton.vertices[:, 0] /= anisotropy[0]
        skeleton.vertices[:, 1] /= anisotropy[1]
        skeleton.vertices[:, 2] /= anisotropy[2]
        
        # Add both vertex and edge plots for the skeleton component
        skeleton_traces.extend(draw_component(skeleton))
    
    return skeleton_traces

# Function to draw a single skeleton component
def draw_component(skel):
    """Draw a single skeleton component as a 3D scatter plot and line plot."""
    # Plot vertices
    scatter_skeleton_vertices = go.Scatter3d(
        x=skel.vertices[:, 0],
        y=skel.vertices[:, 1],
        z=skel.vertices[:, 2],
        mode='markers',
        marker=dict(
            size=2,
            color=skel.radii,  # Color vertices by radii
            colorscale='Viridis',
            opacity=0.8
        ),
        name="Skeleton Vertices"
    )
    
    # Plot edges
    x_edges = []
    y_edges = []
    z_edges = []
    
    for e1, e2 in skel.edges:
        pt1, pt2 = skel.vertices[e1], skel.vertices[e2]
        x_edges += [pt1[0], pt2[0], None]
        y_edges += [pt1[1], pt2[1], None]
        z_edges += [pt1[2], pt2[2], None]
    
    scatter_skeleton_edges = go.Scatter3d(
        x=x_edges,
        y=y_edges,
        z=z_edges,
        mode='lines',
        line=dict(
            color='silver',
            width=1
        ),
        name="Skeleton Edges"
    )
    
    return [scatter_skeleton_vertices, scatter_skeleton_edges]

# Function to plot a 2D slice along the Z-axis
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
        customdata=np.stack([x, y], axis=-1)  # Store coordinates for click events
    )
    
    return scatter_slice

# Global variable to store skeletonization results
skeletonization_results = None

def precompute_skeletonization():
    global skeletonization_results
    if skeletonization_results is None:
        LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
        ANISOTROPY = (900, 900, 5000)
        labels = load_labels(LABELS_FILEPATH)

        # Perform skeletonization and get the traces
        scatter_thinning = plot_thinning(labels)
        scatter_volume = plot_volume(labels)
        skeleton_list = skeletonize_labels(labels, ANISOTROPY)
        skeleton_traces = draw_skeleton(skeleton_list, ANISOTROPY)

        # Store results in the global variable
        skeletonization_results = {
            'labels': labels,
            'scatter_thinning': scatter_thinning,
            'scatter_volume': scatter_volume,
            'skeleton_traces': skeleton_traces,
            'skeleton_list': skeleton_list
        }

# Call the precompute function once at the start
precompute_skeletonization()

@app.callback(
    Output("skeleton-graph", "figure"), 
    Input("z-slider", "value"))
def update_skeleton_plot(slice_index):
    global skeletonization_results

    # Ensure skeletonization results are precomputed
    if skeletonization_results is None:
        precompute_skeletonization()

    labels = skeletonization_results['labels']
    scatter_thinning = skeletonization_results['scatter_thinning']
    scatter_volume = skeletonization_results['scatter_volume']
    skeleton_traces = skeletonization_results['skeleton_traces']

    # Create subplot for 3D skeleton and 2D slice
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}]],
        subplot_titles=("3D Skeletonization", f"Z Slice {slice_index}")
    )

    # Add thinning, volume, and skeleton traces to the 3D plot
    fig.add_trace(scatter_thinning, row=1, col=1)
    fig.add_trace(scatter_volume, row=1, col=1)
    for trace in skeleton_traces:
        fig.add_trace(trace, row=1, col=1)

    # Add the selected Z slice to the 2D plot
    scatter_z_slice = plot_z_slice(labels, slice_index)
    fig.add_trace(scatter_z_slice, row=1, col=2)

    # Update layout
    fig.update_layout(
        title="Skeletonization with Interactive Z-Slice",
        height=800,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        ),
        margin=dict(l=0, r=0, b=50, t=50)
    )
    
    return fig

@app.callback(
    Output('skeleton-graph', 'figure'),
    [Input('add-point-btn', 'n_clicks'),
     Input('move-point-btn', 'n_clicks'),
     Input('delete-point-btn', 'n_clicks')],
    [State('point-coordinates', 'value'),
     State('new-coordinates', 'value')]
)
def edit_skeleton(add_clicks, move_clicks, delete_clicks, point_coords, new_coords):
    global skeletonization_results

    if skeletonization_results is None:
        precompute_skeletonization()

    skeleton_list = skeletonization_results['skeleton_list']

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'add-point-btn' and point_coords:
        x, y, z = map(int, point_coords.split(','))
        skeleton_list.append((x, y, z))

    elif button_id == 'move-point-btn' and point_coords and new_coords:
        x, y, z = map(int, point_coords.split(','))
        new_x, new_y, new_z = map(int, new_coords.split(','))
        if (x, y, z) in skeleton_list:
            skeleton_list.remove((x, y, z))
            skeleton_list.append((new_x, new_y, new_z))

    elif button_id == 'delete-point-btn' and point_coords:
        x, y, z = map(int, point_coords.split(','))
        if (x, y, z) in skeleton_list:
            skeleton_list.remove((x, y, z))

    # Redraw skeleton
    skeleton_traces = draw_skeleton(skeleton_list, ANISOTROPY)
    skeletonization_results['skeleton_traces'] = skeleton_traces

    # Update the figure
    fig = update_skeleton_plot(slice_index=50)  # Or use the current slice index
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
