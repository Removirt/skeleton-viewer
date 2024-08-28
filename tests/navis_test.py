import plotly.express as px
import pandas as pd
import navis as nv

# pd.DataFrame(from)
nl = nv.read_swc("/home/lkipo/Codigo/removirt/kimimaro_out/1.swc")
# df = px.data.iris()
# fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", symbol="species")
# fig.show()
nv.plot3d(nl, backend="plotly").show()