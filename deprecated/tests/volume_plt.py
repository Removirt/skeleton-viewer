import re

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import nibabel as nib

def from_swc(swcstr): # from cloudvolume/skeleton.py
# def from_swc(self, swcstr): # from cloudvolume/skeleton.py
    """
    The SWC format was first defined in 
    
    R.C Cannona, D.A Turner, G.K Pyapali, H.V Wheal. 
    "An on-line archive of reconstructed hippocampal neurons".
    Journal of Neuroscience Methods
    Volume 84, Issues 1-2, 1 October 1998, Pages 49-54
    doi: 10.1016/S0165-0270(98)00091-0

    This website is also helpful for understanding the format:

    https://web.archive.org/web/20180423163403/http://research.mssm.edu/cnic/swc.html

    Returns: Skeleton
    """
    lines = swcstr.split("\n")
    while len(lines) and (lines[0] == '' or re.match(r'[#\s]', lines[0][0])):
      l = lines.pop(0)

    if len(lines) == 0:
      return []
    #   return Skeleton()

    vertices = []
    edges = []
    radii = []
    vertex_types = []

    label_index = {}
    
    N = 0

    for line in lines:
      if line.replace(r"\s", '') == '':
        continue
      (vid, vtype, x, y, z, radius, parent_id) = line.split(" ")
      
      coord = tuple([ float(_) for _ in (x,y,z) ])
      vid = int(vid)
      parent_id = int(parent_id)

      label_index[vid] = N

      if parent_id >= 0:
        if vid < parent_id:
          edge = [vid, parent_id]
        else:
          edge = [parent_id, vid]

        edges.append(edge)

      vertices.append(coord)
      vertex_types.append(int(vtype))

      try:
        radius = float(radius)
      except ValueError:
        radius = -1 # e.g. radius = NA or N/A

      radii.append(radius)

      N += 1

    for edge in edges:
      edge[0] = label_index[edge[0]]
      edge[1] = label_index[edge[1]]

    return vertices, edges, radii, vertex_types


vol = nib.load("/home/lkipo/Codigo/removirt/Task08_HepaticVessel/Task08_HepaticVessel/labelsTr/hepaticvessel_001.nii.gz").get_fdata()

with open("/home/lkipo/Codigo/removirt/kimimaro_out/1.swc", "rt") as swc:
    vertices, _, _, _ = from_swc(swc.read())

vertices = np.array(vertices)
# print(vertices.shape)

shape = vol.shape
X, Y, Z = np.mgrid[:shape[0], :shape[1], :shape[2]]

vol /= vol.max()

fig = go.Figure(data=go.Volume(
    x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
    value=vol.flatten(),
    isomin=0.2,
    isomax=0.7,
    opacity=0.01,
    surface_count=25,
    ))

# fig.add_trace(go.Scatter3d(
#     x=vertices[:,0], y=vertices[:,1], z=vertices[:,2],
#     mode='markers',
#     marker=dict(
#         size=1,
#         color='red',
#         opacity=0.8
#     )
# ))
fig.update_layout(scene_xaxis_showticklabels=False,
                  scene_yaxis_showticklabels=False,
                  scene_zaxis_showticklabels=False)
fig.show()