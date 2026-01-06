import dash_bootstrap_components as dbc
from dash import html, dcc
import dash

def sidebar_html(sidebar):
    return [
        html.H2("Rosetta X", className="display-4"),
        html.Hr(),
        html.P("Navigation bar", className="lead"),
        dbc.Nav([
            html.Div([
                html.Div(
                    dcc.Link(f"{page['name']}", href=page["relative_path"])
                ) for page in dash.page_registry.values() if page["name"] != "Apply Calibration"
            ]),
            dbc.Collapse(
                dbc.Card([
                    dbc.CardHeader("Saved Calibrations"),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H5(folder),
                                html.Ul([
                                    html.Li(
                                        html.A(file, id={"type": "apply-calibration", "index": f"{folder}/{file}"}, href=f"/apply-calibration/{folder}/{file}", n_clicks=0)
                                    ) for file in files]
                                )]
                            ) for folder, files in sidebar.items()
                        ]),
                        html.Hr(),
                        dbc.Button(
                            "Apply Saved Calibration",
                            id="collapse-button",
                            className="mb-3",
                            color="primary",
                            n_clicks=0,
                            style={"width": "100%"}
                        ), 
                    ],style={"maxHeight": "60vh", "overflowY": "auto"})
                ]),
                id="collapse-card",
                is_open=True,
                style={"width": "100%"}
            )
        ],
        vertical=True,
        pills=True,
        ),
    ]