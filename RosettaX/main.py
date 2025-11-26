from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import numpy as np
import base64

#!/usr/bin/env python3
# main.py - simple Dash + Plotly dashboard

import plotly.graph_objects as go
import plotly.express as px
from reader import FCSFile

# sample time series data
np.random.seed(1)
file_path = ""

app = Dash(__name__)
app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "20px"},
    children=[
        html.H2("Simple Dash Plotly Dashboard"),
        html.Div(
            style={"display": "flex", "gap": "12px", "alignItems": "center"},
            children=[
                html.Button(
                    dcc.Upload(
                        "Upload Data",
                        id="upload-data-button",
                        style={"marginLeft": "8px"},
                    ),
                ),
                html.Button(
                    "Save Image",
                    id="save-image-button",
                    n_clicks=0,
                    style={"marginLeft": "8px"},
                ),
                html.Button(
                    "Save Analysis",
                    id="save-analysis-button",
                    n_clicks=0,
                    style={"marginLeft": "8px"},
                ),
                html.Button(
                    "Run Analysis",
                    id="run-analysis-button",
                    n_clicks=0,
                    style={"marginLeft": "8px"},
                ),
            ],
        ),


            # Second graph
            dcc.Graph(
                figure=go.Figure(go.Scatter(x=[1, 2, 3, 4], y=[10, 20, 30, 40])),
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'width': '33%',
                },
            ),

            # Third graph
            dcc.Graph(
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'width': '33%',
                },
                figure=px.scatter_3d(
                    x=[1, 2, 3, 4],
                    y=[10, 20, 30, 40],
                    z=[5, 15, 25, 35],
                ),
            ),
            dcc.Graph(
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'width': '33%',
                },
                figure=px.scatter_3d(
                    x=[1, 2, 3, 4],
                    y=[10, 20, 30, 40],
                    z=[5, 15, 25, 35],
                ),
            ),
        html.Div(id="footer", children="Data: synthetic", style={"marginTop": "8px", "color": "#666"}),
    ],
)

@app.callback(
    Output("footer", "children"),
    Input("upload-data-button", "filename"),
    State("upload-data-button", "contents"),
    State("upload-data-button", "last_modified"),
    prevent_initial_call=True
)
def upload_file(file_path, contents, last_modified):
    print(file_path, contents, last_modified)
    print("sfed")
    filedata, contents = contents.split(",")
    decoded = base64.b64decode(contents)
    print(decoded)
    data = FCSFile(file_path).read_all_data()

if __name__ == "__main__":
    app.run(debug=True)