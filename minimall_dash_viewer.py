import os
from dash import Dash, dcc, html, Input, Output, State, no_update
import plotly.graph_objects as go
import numpy as np
import nibabel as nib
from skimage.morphology import skeletonize
import json
import argparse  # <-- Nuevo import para argumentos

# Procesar argumentos de línea de comandos
parser = argparse.ArgumentParser(description="Dash app for vessel skeleton visualization")
parser.add_argument("labels_filepath", help="Path to the labels NIfTI file (mandatory).")
parser.add_argument("--skeleton_filepath", help="Optional path to the skeleton JSON file.")
args = parser.parse_args()

labels_filepath = args.labels_filepath  # <-- Usamos el argumento obligatorio
if args.skeleton_filepath:
    skeleton_filepath = args.skeleton_filepath  # <-- Si se especifica, se usa directamente
else:
    try:
        base = os.path.basename(labels_filepath)
        # Eliminar extensiones conocidas de NIfTI
        if base.endswith('.nii.gz'):
            base = base[:-7]  # <-- Elimina '.nii.gz'
        elif base.endswith('.nii'):
            base = base[:-4]  # <-- Elimina '.nii'
        parts = base.split('_')
        # Intentar obtener un número del nombre del archivo
        if parts[-1].isdigit():
            number = parts[-1]
        else:
            number = "default"
        skeleton_basename = f"modified_skeleton_{number}.json"
        skeleton_filepath = os.path.join(os.path.dirname(labels_filepath), skeleton_basename)
    except Exception as e:
        skeleton_filepath = "../data/default_modified_skeleton.json"

# Función para cargar los datos de labels desde un archivo NIfTI
def load_labels(filepath):
    labels_nib = nib.load(filepath)
    labels = labels_nib.get_fdata().astype(np.uint8)
    return labels

# Representa el volumen original en un gráfico 3D de dispersión
def plot_volume(labels, alpha=0.05):
    volume = np.where(labels)
    scatter_volume = go.Scatter3d(
        x=volume[0], y=volume[1], z=volume[2],
        mode='markers',
        marker=dict(size=2, color='black', opacity=alpha),
        name="Volume"
    )
    return scatter_volume

# Representa una porción 2D de los labels a lo largo del eje Z
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

# Realiza la esqueletonización y devuelve la estructura reducida como un conjunto de puntos
def load_thinning(labels):
    skeleton = skeletonize(labels)
    skeleton_points = np.array(np.where(skeleton)).T
    return skeleton_points

# Guarda los puntos del esqueleto en un archivo JSON
def save_skeleton(skeleton_points, filename):
    with open(filename, 'w') as f:
        json.dump(skeleton_points, f)
    print(f"Skeleton saved to {filename}")

# Función para generar la figura de la porción 2D
def generate_slice_figure(slice_index, labels, skeleton_points):
    scatter_slice = plot_z_slice(labels, slice_index)
    # Filtra los puntos del esqueleto para mostrar solo los de la porción actual en Z
    slice_skeleton_points = np.array(skeleton_points)
    slice_skeleton_points = slice_skeleton_points[slice_skeleton_points[:, 2] == slice_index]

    # Crea el gráfico de dispersión para los puntos del esqueleto en la porción Z
    data = [scatter_slice]
    if len(slice_skeleton_points) > 0:
        scatter_skeleton_slice = go.Scatter(
            x=slice_skeleton_points[:, 0],
            y=slice_skeleton_points[:, 1],
            mode='markers',
            marker=dict(size=2, color='red'),
            name="Skeleton Slice"
        )
        data.append(scatter_skeleton_slice)

    return {
        'data': data,
        'layout': go.Layout(
            title=f'2D Slice at Z={slice_index}',
            width=800
        )
    }

# Inicialización de la app Dash
app = Dash(__name__, prevent_initial_callbacks=True)

# Carga de los datos de labels y del esqueleto
# LABELS_FILEPATH = '../data/hepaticvessel_002.nii.gz'  <-- Línea original comentada
# SKELETON_FILEPATH = "../data/modified_skeleton_002.json"  <-- Línea original comentada
labels = load_labels(labels_filepath)  # <-- Usamos el argumento labels_filepath
scatter_volume = plot_volume(labels)

# Carga el esqueleto desde el archivo JSON si existe
if os.path.exists(skeleton_filepath):
    skeleton_points = np.array(json.load(open(skeleton_filepath)))
else:
    skeleton_points = load_thinning(labels)
    os.makedirs(os.path.dirname(skeleton_filepath), exist_ok=True)  # <-- Usamos skeleton_filepath

# Almacena los puntos del esqueleto en una lista mutable
skeleton_points_list = skeleton_points.tolist()

# Representa el esqueleto en 3D
scatter_skeleton_3d = go.Scatter3d(
    x=skeleton_points[:, 0], y=skeleton_points[:, 1], z=skeleton_points[:, 2],
    mode='markers',
    marker=dict(size=2, color='red', opacity=0.5),
    name="Skeleton"
)

# Diccionario con los resultados de la esqueletonización
skeletonization_results = {
    'labels': labels,
    'scatter_volume': scatter_volume,
    'scatter_skeleton': scatter_skeleton_3d,
    'skeleton_points': skeleton_points_list
}
z_slice = 0  # Porción Z inicial

# Layout de la app
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

# Callback para actualizar la porción Z 2D en función del slider
@app.callback(
    Output('2d-slice-plot', 'figure'),
    Input('z-slider', 'value')
)
def update_slice(slider_value):
    global z_slice
    z_slice = slider_value
    return generate_slice_figure(z_slice, labels, skeletonization_results['skeleton_points'])

# Callback para gestionar los clics en la porción Z 2D
@app.callback(
    Output('2d-slice-plot', 'figure', allow_duplicate=True),
    [Input('2d-slice-plot', 'clickData')],
    State('z-slider', 'value'),
)
def handle_click(clickData, slider_value):
    if clickData:
        point_data = clickData['points'][0]
        x, y = int(point_data['x']), int(point_data['y'])
        z = slider_value
        point = [x, y, z]

        # Alterna el punto en el esqueleto
        if point in skeletonization_results['skeleton_points']:
            skeletonization_results['skeleton_points'].remove(point)
        else:
            skeletonization_results['skeleton_points'].append(point)

    # Regenera el gráfico 2D con los puntos actualizados del esqueleto
    return generate_slice_figure(slider_value, labels, skeletonization_results['skeleton_points'])

# Callback para guardar el esqueleto modificado al hacer clic en el botón Save
@app.callback(
    Output("3d-scatter-plot", "figure"),
    Input("save-button", "n_clicks")
)
def save_skeleton_points(n_clicks):
    if n_clicks > 0:
        # save_skeleton(skeletonization_results['skeleton_points'], filename=SKELETON_FILEPATH)  <-- Línea original comentada
        save_skeleton(skeletonization_results['skeleton_points'], filename=skeleton_filepath)  # <-- Usamos skeleton_filepath
        # Actualiza el gráfico 3D con el esqueleto modificado
        skeleton_points = np.array(skeletonization_results['skeleton_points'])
        scatter_skeleton = go.Scatter3d(
            x=skeleton_points[:, 0], y=skeleton_points[:, 1], z=skeleton_points[:, 2],
            mode='markers',
            marker=dict(size=2, color='red', opacity=0.5),
            name="Skeleton"
        )
        skeletonization_results['scatter_skeleton'] = scatter_skeleton

        # Actualiza el gráfico 3D
        return {
            'data': [scatter_volume, scatter_skeleton],
            'layout': go.Layout(
                title='3D Scatter Plot of Volume with Modified Skeleton',
                height=800,
            )
        }
    return no_update

if __name__ == '__main__':
    app.run_server(debug=True)
