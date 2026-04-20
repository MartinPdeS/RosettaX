import dash
import dash_bootstrap_components as dbc
from dash import html


class HomePage:
    def __init__(self) -> None:
        self.page_name = "home"
        self.container_style = {
            "paddingTop": "24px",
            "paddingBottom": "48px",
        }

        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.pypi_url = "https://pypi.org/project/RosettaX/"
        self.anaconda_url = "https://anaconda.org/channels/martinpdes/packages/lightwave2d/overview"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(style={"height": "20px"}),
                self._primary_actions_row(),
                html.Div(style={"height": "20px"}),
                self._workflow_and_reuse_row(),
                html.Div(style={"height": "20px"}),
                self._project_links_row(),
                html.Div(style={"height": "20px"}),
                self._tips_row(),
            ],
            fluid=True,
            style=self.container_style,
        )

    def _hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H1(
                        "RosettaX",
                        style={
                            "marginBottom": "8px",
                            "fontWeight": "700",
                        },
                    ),
                    html.P(
                        "Flow cytometry calibration workspace for building, saving, reviewing, and applying fluorescence and scattering calibrations.",
                        style={
                            "fontSize": "1.05rem",
                            "opacity": 0.9,
                            "marginBottom": "0px",
                            "maxWidth": "900px",
                        },
                    ),
                ]
            ),
            style={"height": "100%"},
        )

    def _primary_actions_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._fluorescence_card(), md=4),
                dbc.Col(self._scattering_card(), md=4),
                dbc.Col(self._apply_card(), md=4),
            ],
            className="g-3",
        )

    def _fluorescence_card(self) -> dbc.Card:
        return self._card_with_body(
            title="Fluorescence calibration",
            description=(
                "Build a fluorescence calibration from an uploaded FCS file by selecting the relevant channels, detecting peaks, fitting the calibration, and saving the result."
            ),
            button_text="Open fluorescence workflow",
            button_href="/fluorescence",
            button_color="success",
            button_id=self._id("fluorescence-link"),
        )

    def _scattering_card(self) -> dbc.Card:
        return self._card_with_body(
            title="Scattering calibration",
            description=(
                "Build a scattering calibration from an uploaded FCS file, configure the relevant parameters, review the fit, and save the resulting calibration payload."
            ),
            button_text="Open scattering workflow",
            button_href="/scattering",
            button_color="secondary",
            button_id=self._id("scattering-link"),
        )

    def _apply_card(self) -> dbc.Card:
        return self._card_with_body(
            title="Apply calibration",
            description=(
                "Load one or more FCS files, select a saved calibration, choose the target and export channels, and export calibrated files."
            ),
            button_text="Open apply workflow",
            button_href="/calibrate",
            button_color="primary",
            button_id=self._id("apply-link"),
        )

    def _workflow_and_reuse_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._workflow_card(), md=7),
                dbc.Col(self._reuse_card(), md=5),
            ],
            className="g-3",
        )

    def _workflow_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Typical workflow"),
                dbc.CardBody(
                    [
                        html.Ol(
                            [
                                html.Li("Choose fluorescence or scattering calibration."),
                                html.Li("Upload the FCS file used for calibration."),
                                html.Li("Select the relevant channels and review the intermediate outputs."),
                                html.Li("Fit and save the calibration as JSON."),
                                html.Li("Reuse the saved calibration later from the sidebar or the apply page."),
                            ],
                            style={"marginBottom": "0px"},
                        )
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _reuse_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Reuse saved calibrations"),
                dbc.CardBody(
                    [
                        html.P(
                            "Saved calibrations appear in the sidebar and can be opened directly.",
                            style={"opacity": 0.9},
                        ),
                        html.Ul(
                            [
                                html.Li("Click the calibration name to inspect its JSON content."),
                                html.Li("Click Apply to open the apply page with that calibration preselected."),
                                html.Li("Use Refresh in the sidebar if you added files manually."),
                            ],
                            style={"marginBottom": "16px"},
                        ),
                        dbc.Button(
                            "Open apply page",
                            href="/apply-calibration",
                            id=self._id("reuse-apply"),
                            color="primary",
                            outline=True,
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _project_links_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._project_links_card(), md=12),
            ],
            className="g-3",
        )

    def _project_links_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Project links"),
                dbc.CardBody(
                    [
                        html.P(
                            "External resources for the project and distribution channels.",
                            style={"opacity": 0.9},
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5("GitHub", style={"marginTop": "0px"}),
                                                html.P(
                                                    "Browse the source code, issues, and repository history.",
                                                    style={"opacity": 0.9},
                                                ),
                                                dbc.Button(
                                                    "Open GitHub",
                                                    href=self.github_url,
                                                    target="_blank",
                                                    rel="noopener noreferrer",
                                                    color="dark",
                                                    id=self._id("github-link"),
                                                    style={"width": "100%"},
                                                ),
                                            ]
                                        ),
                                        style={"height": "100%"},
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5("PyPI", style={"marginTop": "0px"}),
                                                html.P(
                                                    "Open the Python package page and installation metadata.",
                                                    style={"opacity": 0.9},
                                                ),
                                                dbc.Button(
                                                    "Open PyPI",
                                                    href=self.pypi_url,
                                                    target="_blank",
                                                    rel="noopener noreferrer",
                                                    color="primary",
                                                    id=self._id("pypi-link"),
                                                    style={"width": "100%"},
                                                ),
                                            ]
                                        ),
                                        style={"height": "100%"},
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5("Anaconda", style={"marginTop": "0px"}),
                                                html.P(
                                                    "Open the Anaconda channel or package overview page.",
                                                    style={"opacity": 0.9},
                                                ),
                                                dbc.Button(
                                                    "Open Anaconda",
                                                    href=self.anaconda_url,
                                                    target="_blank",
                                                    rel="noopener noreferrer",
                                                    color="secondary",
                                                    id=self._id("anaconda-link"),
                                                    style={"width": "100%"},
                                                ),
                                            ]
                                        ),
                                        style={"height": "100%"},
                                    ),
                                    md=4,
                                ),
                            ],
                            className="g-3",
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _tips_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._tips_card(), md=8),
                dbc.Col(self._settings_card(), md=4),
            ],
            className="g-3",
        )

    def _tips_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Practical notes"),
                dbc.CardBody(
                    [
                        html.Ul(
                            [
                                html.Li("Use fluorescence calibration when you need a saved intensity mapping from measured signal to calibrated units."),
                                html.Li("Use scattering calibration when the calibration is based on scatter response and model parameters."),
                                html.Li("When applying a calibration to multiple files, keep detector names consistent across the uploaded batch."),
                                html.Li("Use the sidebar JSON preview when you want to quickly verify what is inside a saved calibration."),
                            ],
                            style={"marginBottom": "0px"},
                        )
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _settings_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Configuration"),
                dbc.CardBody(
                    [
                        html.P(
                            "Manage profiles and default settings for the application.",
                            style={"opacity": 0.9},
                        ),
                        dbc.Button(
                            "Open settings",
                            href="/settings",
                            id=self._id("settings-link"),
                            color="dark",
                            outline=True,
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _card_with_body(
        self,
        *,
        title: str,
        description: str,
        button_text: str,
        button_href: str,
        button_color: str,
        button_id: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(title, style={"marginTop": "0px", "marginBottom": "10px"}),
                    html.P(
                        description,
                        style={"opacity": 0.9, "minHeight": "120px"},
                    ),
                    dbc.Button(
                        button_text,
                        href=button_href,
                        id=button_id,
                        color=button_color,
                        style={"width": "100%"},
                    ),
                ]
            ),
            style={"height": "100%"},
        )


_page = HomePage()
layout = _page.layout

dash.register_page(
    __name__,
    path="/home",
    name="Home",
    order=0,
    layout=layout,
)