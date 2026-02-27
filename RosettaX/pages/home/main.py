import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


class HomePage:
    def __init__(self) -> None:
        self.page_name = "home"
        self.path = "/"
        self.name = "Home"

        self.container_style = {"paddingBottom": "48px"}

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def register(self) -> "HomePage":
        dash.register_page(__name__, path=self.path, name=self.name, order=0)
        return self

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                self._header_section(),
                html.Hr(),
                self._intro_cards_row(),
                self._create_calibration_row(),
                html.Hr(),
                # self._quick_navigation_row(),
            ],
            fluid=True,
            style=self.container_style,
        )

    def _header_section(self) -> html.Div:
        return html.Div(
            [
                html.H1("RosettaX", style={"marginBottom": "6px"}),
                html.P(
                    "Flow cytometry calibration tool.",
                    style={"opacity": 0.85, "marginBottom": "0px"},
                ),
            ],
            style={"paddingTop": "24px"},
        )

    def _intro_cards_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._new_here_card(), md=6),
                dbc.Col(self._existing_calibrations_card(), md=6),
            ],
            style={"marginBottom": "16px"},
        )

    def _new_here_card(self) -> dbc.Card:
        return self._card_with_body(
            [
                html.H3("New here?", style={"marginTop": "0px"}),
                html.P(
                    "Start with the Help page. It walks through the workflow: "
                    "scattering threshold, fluorescence peaks, MESF fitting, saving, and applying.",
                    style={"opacity": 0.9},
                ),
                dbc.Button(
                    "Open Help",
                    href="/help",
                    id=self._id("help-link"),
                    color="primary",
                ),
            ]
        )

    def _existing_calibrations_card(self) -> dbc.Card:
        return self._card_with_body(
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
        )

    def _create_calibration_row(self) -> dbc.Row:
        return dbc.Row([dbc.Col(self._create_calibration_card(), md=12)])

    def _create_calibration_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Create a new calibration"),
                dbc.CardBody(
                    [
                        html.P(
                            "Choose the calibration type you want to create.",
                            style={"opacity": 0.9},
                        ),
                        self._create_calibration_buttons_row(),
                        html.Hr(),
                        self._workflow_bullets(),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _create_calibration_buttons_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Fluorescent Calibration",
                        href="/fluorescent_calibration",
                        id=self._id("fluorescent-link"),
                        color="success",
                        style={"width": "100%"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Button(
                        "Scatter Calibration",
                        href="/scatter_calibration",
                        id=self._id("scatter-link"),
                        color="secondary",
                        style={"width": "100%"},
                    ),
                    md=6,
                ),
            ],
            style={"marginTop": "8px"},
        )

    def _workflow_bullets(self) -> html.Ul:
        return html.Ul(
            [
                html.Li("Upload bead FCS file"),
                html.Li("Set scattering threshold (noise removal)"),
                html.Li("Detect fluorescence peaks (after gating)"),
                html.Li("Fit MESF calibration and save payload"),
            ],
            style={"marginBottom": "0px"},
        )

    def _quick_navigation_row(self) -> dbc.Row:
        return dbc.Row([dbc.Col(self._quick_navigation_card(), md=12)])

    def _quick_navigation_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Quick navigation", style={"marginTop": "0px"}),
                    html.P(
                        "Use these links if you know where you want to go.",
                        style={"opacity": 0.85},
                    ),
                    self._quick_links(),
                ]
            )
        )

    def _quick_links(self) -> html.Div:
        return html.Div(
            [
                dcc.Link("Help", href="/help", id=self._id("quick-help")),
                html.Span("  |  "),
                dcc.Link(
                    "Fluorescent Calibration",
                    href="/fluorescent_calibration",
                    id=self._id("quick-fluorescent"),
                ),
                html.Span("  |  "),
                dcc.Link(
                    "Scatter Calibration",
                    href="/scatter_calibration",
                    id=self._id("quick-scatter"),
                ),
            ]
        )

    def _card_with_body(self, body_children: list[object]) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(body_children),
            style={"height": "100%"},
        )


layout = HomePage().register().layout()