from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import numpy as np
from skimage.morphology import skeletonize
import plotly.express as px
import time
import numpy as np
import nibabel as nib
import kimimaro

# Function to load labels
def load_labels(filepath):
    """Load the label data from a NIfTI file."""
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)
    return labels

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Interactive plot with custom data source'),
    dcc.Graph(id="graph"),
    html.P("Number of bars:"),
    dcc.Slider(id="slider", min=2, max=10, value=4, step=1),
])


@app.callback(
    Output("graph", "figure"), 
    Input("slider", "value"))
def update_bar_chart(size):
    data = np.random.normal(3, 2, size=size) # replace with your own data source
    fig = go.Figure(
        data=[go.Bar(y=data)],
        layout_title_text="Native Plotly rendering in Dash"
    )
    print("Data:", data)
    return fig

app.run_server(debug=True)