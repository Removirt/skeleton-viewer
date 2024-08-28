import numpy as np
import nibabel as nib
import kimimaro
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from skimage.morphology import skeletonize

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
        print(f"Plotting skeleton component: {label}")
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
        name=f"Z Slice at Z={slice_index}"
    )
    
    return scatter_slice

# Main function to handle visualization
def visualize_skeletonization(labels_filepath, anisotropy):
    """Main function to handle the entire skeletonization visualization with an interactive Z slice."""
    labels = load_labels(labels_filepath)

    # Generate the scatter plots for thinning, volume, and skeleton
    scatter_thinning = plot_thinning(labels)
    scatter_volume = plot_volume(labels)

    skeleton_list = skeletonize_labels(labels, anisotropy)
    skeleton_traces = draw_skeleton(skeleton_list, anisotropy)

    # Define the number of slices along the Z-axis
    z_slices = labels.shape[2]

    # Create a subplot with two columns (3D view and 2D Z slice view)
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}]],
        subplot_titles=("3D Skeletonization", "2D Z Slice")
    )

    # Add the 3D skeletonization and volume plots to the first column
    fig.add_trace(scatter_thinning, row=1, col=1)
    fig.add_trace(scatter_volume, row=1, col=1)
    for trace in skeleton_traces:
        fig.add_trace(trace, row=1, col=1)
    
    # Initialize with the first Z slice
    scatter_z_slice = plot_z_slice(labels, 0)
    fig.add_trace(scatter_z_slice, row=1, col=2)

    # Update layout to add a slider
    steps = []
    for z in range(z_slices):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)}],  # Hide all traces initially
            label=f"Z={z}"
        )
        
        # Make the relevant 3D plots visible
        step["args"][0]["visible"][0] = True  # Thinning plot
        step["args"][0]["visible"][1] = True  # Volume plot
        for i in range(2, len(skeleton_traces) + 2):
            step["args"][0]["visible"][i] = True  # Skeleton traces
        
        # Make only the current Z slice visible
        step["args"][0]["visible"][len(skeleton_traces) + 2] = (z == 0)

        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Z Slice: "},
        pad={"b": 10},
        steps=steps
    )]

    # Update layout with sliders
    fig.update_layout(
        sliders=sliders,
        title="3D Skeletonization and Interactive 2D Z Slice",
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z'),
        ),
        margin=dict(l=0, r=0, b=50, t=50),
        height=1200
    )

    # Show the plot
    fig.show()

if __name__ == '__main__':
    # Set parameters and file paths
    LABELS_FILEPATH = '../skeletonization/labelsTr/hepaticvessel_001.nii.gz'
    ANISOTROPY = (900, 900, 5000)

    # Run the visualization with an interactive Z slice
    visualize_skeletonization(LABELS_FILEPATH, ANISOTROPY)
