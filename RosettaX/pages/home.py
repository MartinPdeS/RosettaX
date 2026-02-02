import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


PAGE_NAME = "home"


def _id(name: str) -> str:
    return f"{PAGE_NAME}-{name}"


dash.register_page(__name__, path="/", name="Home")


layout = dbc.Container(
    [
        html.Div(
            [
                html.H1("RosettaX", style={"marginBottom": "6px"}),
                html.P(
                    "Flow-cytometry calibration tool.",
                    style={"opacity": 0.85, "marginBottom": "0px"},
                ),
            ],
            style={"paddingTop": "24px"},
        ),
        html.Hr(),

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("New here?", style={"marginTop": "0px"}),
                                html.P(
                                    "Start with the Help page. It walks through the full workflow: "
                                    "scattering threshold, fluorescence peaks, MESF fitting, saving, and applying.",
                                    style={"opacity": 0.9},
                                ),
                                dbc.Button(
                                    "Open Help",
                                    href="/help",
                                    id=_id("help-link"),
                                    color="primary",
                                ),
                            ]
                        ),
                        style={"height": "100%"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3("Already have calibrations?", style={"marginTop": "0px"}),
                                html.P(
                                    "If a calibration has been saved, select it from the sidebar. "
                                    "You can reuse it without rebuilding.",
                                    style={"opacity": 0.9},
                                ),
                                dbc.Alert(
                                    "Tip: saved calibrations appear under the sidebar calibration section.",
                                    color="info",
                                    style={"marginBottom": "0px"},
                                ),
                            ]
                        ),
                        style={"height": "100%"},
                    ),
                    md=6,
                ),
            ],
            style={"marginBottom": "16px"},
        ),

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Create a new calibration"),
                            dbc.CardBody(
                                [
                                    html.P(
                                        "Choose the calibration type you want to create.",
                                        style={"opacity": 0.9},
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    "Fluorescent Calibration",
                                                    href="/fluorescent_calibration",
                                                    id=_id("fluorescent-link"),
                                                    color="success",
                                                    style={"width": "100%"},
                                                ),
                                                md=6,
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Scatter Calibration",
                                                    href="/scatter_calibration",
                                                    id=_id("scatter-link"),
                                                    color="secondary",
                                                    style={"width": "100%"},
                                                ),
                                                md=6,
                                            ),
                                        ],
                                        style={"marginTop": "8px"},
                                    ),
                                    html.Hr(),
                                    html.Ul(
                                        [
                                            html.Li("Upload bead FCS file"),
                                            html.Li("Set scattering threshold (noise removal)"),
                                            html.Li("Detect fluorescence peaks (after gating)"),
                                            html.Li("Fit MESF calibration and save payload"),
                                        ],
                                        style={"marginBottom": "0px"},
                                    ),
                                ]
                            ),
                        ],
                        style={"height": "100%"},
                    ),
                    md=12,
                ),
            ]
        ),

        html.Hr(),

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Quick navigation", style={"marginTop": "0px"}),
                                html.P(
                                    "Use these links if you know where you want to go.",
                                    style={"opacity": 0.85},
                                ),
                                html.Div(
                                    [
                                        dcc.Link("Help", href="/help", id=_id("quick-help")),
                                        html.Span("  |  "),
                                        dcc.Link(
                                            "Fluorescent Calibration",
                                            href="/fluorescent_calibration",
                                            id=_id("quick-fluorescent"),
                                        ),
                                        html.Span("  |  "),
                                        dcc.Link(
                                            "Scatter Calibration",
                                            href="/scatter_calibration",
                                            id=_id("quick-scatter"),
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ),
                    md=12,
                ),
            ]
        ),
    ],
    fluid=True,
    style={"paddingBottom": "48px"},
)
