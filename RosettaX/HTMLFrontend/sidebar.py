import dash_bootstrap_components as dbc
from dash import html
from utils import generate_file_list_for_sidebar

def sidebar():
    list_of_files = generate_file_list_for_sidebar()
    return [
        html.H2("Rosetta X", className="display-4"),
        html.Hr(),
        html.P("Navigation bar", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Fluorescent Calibration", href="/page-1", active="exact"),
                dbc.NavLink("Other Calibration", href="/page-2", active="exact"),
                dbc.Button(
                    "Show / Hide Saved Configurations",
                    id="collapse-button",
                    className="mb-3",
                    color="primary",
                    n_clicks=0,
                ),  
                dbc.Collapse(
                    dbc.Card(
                        dbc.CardBody(
                            html.Div([
                                html.Div([
                                    html.H5(folder),
                                    html.Ul([
                                        html.Li(
                                            html.A(file, id={"type": "start-calibration", "index": f"{folder}/{file}"}, href="/start-calibration", n_clicks=0)
                                        ) for file in files]
                                    )]
                                ) for folder, files in list_of_files.items()]
                            ),
                            style={"maxHeight": "60vh", "overflowY": "auto"}
                        )
                    ),
                    id="collapse-card",
                    is_open=True,
                )
            ],
            vertical=True,
            pills=True,
        ),
    ]