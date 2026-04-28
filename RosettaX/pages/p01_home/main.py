# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html


class HomePage:
    """
    Home page for RosettaX.

    Responsibilities
    ----------------
    - Present RosettaX in one clear message.
    - Help users choose one of the three main workflows.
    - Avoid repeated navigation links to the same destination.
    - Keep support and configuration links secondary.
    """

    def __init__(self) -> None:
        self.page_name = "home"

        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.pypi_url = "https://pypi.org/project/RosettaX/"
        self.anaconda_url = "https://anaconda.org/"
        self.documentation_url = "#"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(style={"height": "18px"}),
                self._workflow_cards_row(),
                html.Div(style={"height": "18px"}),
                self._secondary_actions_row(),
                html.Div(style={"height": "18px"}),
                self._footer_links(),
            ],
            fluid=True,
            style={
                "paddingTop": "12px",
                "paddingBottom": "40px",
            },
        )

    def _hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        "Flow cytometry calibration workspace",
                        style={
                            "fontSize": "0.78rem",
                            "fontWeight": "700",
                            "letterSpacing": "0.08em",
                            "textTransform": "uppercase",
                            "opacity": 0.68,
                            "marginBottom": "10px",
                        },
                    ),
                    html.H1(
                        "RosettaX",
                        style={
                            "marginBottom": "10px",
                            "fontWeight": "800",
                            "fontSize": "2.45rem",
                            "lineHeight": "1.08",
                        },
                    ),
                    html.P(
                        (
                            "Build fluorescence and scattering calibrations from bead based "
                            "FCS measurements, then apply saved calibrations to experimental files."
                        ),
                        style={
                            "fontSize": "1.1rem",
                            "opacity": 0.88,
                            "marginBottom": "0px",
                            "maxWidth": "980px",
                        },
                    ),
                ],
                style={
                    "padding": "26px",
                },
            ),
            style={
                "borderRadius": "16px",
            },
        )

    def _workflow_cards_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    self._workflow_card(
                        label="Build",
                        title="Fluorescence calibration",
                        description=(
                            "Create a fluorescence calibration from bead peaks and known MESF values."
                        ),
                        steps=[
                            "Upload bead FCS",
                            "Detect peaks",
                            "Enter MESF values",
                            "Create calibration",
                            "Save calibration",
                        ],
                        button_text="Open fluorescence workflow",
                        button_href="/fluorescence",
                        button_color="primary",
                        button_id=self._id("fluorescence-link"),
                    ),
                    lg=4,
                ),
                dbc.Col(
                    self._workflow_card(
                        label="Build",
                        title="Scattering calibration",
                        description=(
                            "Create a scattering calibration by linking measured peaks to Mie coupling values."
                        ),
                        steps=[
                            "Upload bead FCS",
                            "Detect peaks",
                            "Define Mie model",
                            "Compute coupling",
                            "Create calibration",
                            "Save calibration",
                        ],
                        button_text="Open scattering workflow",
                        button_href="/scattering",
                        button_color="secondary",
                        button_id=self._id("scattering-link"),
                    ),
                    lg=4,
                ),
                dbc.Col(
                    self._workflow_card(
                        label="Apply",
                        title="Apply calibration",
                        description=(
                            "Use a saved calibration to add calibrated channels to FCS files."
                        ),
                        steps=[
                            "Upload FCS files",
                            "Select calibration",
                            "Choose channels",
                            "Preview output",
                            "Export calibrated files",
                        ],
                        button_text="Open apply workflow",
                        button_href="/calibrate",
                        button_color="success",
                        button_id=self._id("apply-link"),
                    ),
                    lg=4,
                ),
            ],
            className="g-3",
        )

    def _workflow_card(
        self,
        *,
        label: str,
        title: str,
        description: str,
        steps: list[str],
        button_text: str,
        button_href: str,
        button_color: str,
        button_id: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        label,
                        style={
                            "display": "inline-block",
                            "fontSize": "0.74rem",
                            "fontWeight": "800",
                            "letterSpacing": "0.06em",
                            "textTransform": "uppercase",
                            "opacity": 0.65,
                            "marginBottom": "8px",
                        },
                    ),
                    html.H4(
                        title,
                        style={
                            "fontWeight": "760",
                            "marginBottom": "10px",
                        },
                    ),
                    html.P(
                        description,
                        style={
                            "opacity": 0.84,
                            "minHeight": "54px",
                            "marginBottom": "14px",
                        },
                    ),
                    html.Div(
                        [
                            self._workflow_step_pill(
                                index=index + 1,
                                label=step,
                            )
                            for index, step in enumerate(steps)
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "7px",
                            "marginBottom": "16px",
                        },
                    ),
                    dbc.Button(
                        button_text,
                        href=button_href,
                        id=button_id,
                        color=button_color,
                        style={
                            "width": "100%",
                        },
                    ),
                ]
            ),
            style={
                "height": "100%",
                "borderRadius": "14px",
            },
        )

    def _workflow_step_pill(
        self,
        *,
        index: int,
        label: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(
                    str(index),
                    style={
                        "width": "24px",
                        "height": "24px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontSize": "0.78rem",
                        "fontWeight": "800",
                        "backgroundColor": "rgba(13, 110, 253, 0.10)",
                        "border": "1px solid rgba(13, 110, 253, 0.28)",
                        "flex": "0 0 auto",
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.9rem",
                        "opacity": 0.86,
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "9px",
            },
        )

    def _secondary_actions_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    self._principles_card(),
                    lg=6,
                ),
                dbc.Col(
                    self._secondary_links_card(),
                    lg=6,
                ),
            ],
            className="g-3",
        )

    def _principles_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    "Before applying a calibration",
                    style={
                        "fontWeight": "700",
                    },
                ),
                dbc.CardBody(
                    [
                        self._principle_item(
                            "Use compatible acquisition settings",
                            "Reference and experimental files should use matching detector configuration.",
                        ),
                        self._principle_item(
                            "Inspect peak detection",
                            "The calibration fit is only meaningful if the selected bead peaks are correct.",
                        ),
                        self._principle_item(
                            "Keep the calibration JSON",
                            "Save it with exported FCS files so the conversion remains traceable.",
                        ),
                    ]
                ),
            ],
            style={
                "height": "100%",
                "borderRadius": "14px",
            },
        )

    def _principle_item(
        self,
        title: str,
        description: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(
                    title,
                    style={
                        "fontWeight": "650",
                        "marginBottom": "3px",
                    },
                ),
                html.Div(
                    description,
                    style={
                        "fontSize": "0.92rem",
                        "opacity": 0.76,
                    },
                ),
            ],
            style={
                "marginBottom": "14px",
            },
        )

    def _secondary_links_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    "Project and settings",
                    style={
                        "fontWeight": "700",
                    },
                ),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "Use settings to configure profiles and defaults. Use the repository "
                                "for source code, issues, and contributions."
                            ),
                            style={
                                "opacity": 0.82,
                                "marginBottom": "16px",
                            },
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "Open settings",
                                        href="/settings",
                                        id=self._id("settings-link"),
                                        color="dark",
                                        outline=True,
                                        style={
                                            "width": "100%",
                                        },
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Open GitHub",
                                        href=self.github_url,
                                        target="_blank",
                                        rel="noopener noreferrer",
                                        id=self._id("github-link"),
                                        color="dark",
                                        outline=True,
                                        style={
                                            "width": "100%",
                                        },
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Contact",
                                        href=f"mailto:{self.contact_email}",
                                        id=self._id("email-link"),
                                        color="primary",
                                        outline=True,
                                        style={
                                            "width": "100%",
                                        },
                                    ),
                                    md=4,
                                ),
                            ],
                            className="g-2",
                        ),
                    ]
                ),
            ],
            style={
                "height": "100%",
                "borderRadius": "14px",
            },
        )

    def _footer_links(self) -> html.Div:
        return html.Div(
            [
                html.Span(
                    "Resources:",
                    style={
                        "fontWeight": "600",
                        "marginRight": "10px",
                    },
                ),
                html.A(
                    "GitHub",
                    href=self.github_url,
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "marginRight": "12px",
                    },
                ),
                html.A(
                    "PyPI",
                    href=self.pypi_url,
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "marginRight": "12px",
                    },
                ),
                html.A(
                    "Anaconda",
                    href=self.anaconda_url,
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "marginRight": "12px",
                    },
                ),
                html.A(
                    "Online documentation",
                    href=self.documentation_url,
                    target="_blank",
                    rel="noopener noreferrer",
                ),
            ],
            style={
                "fontSize": "0.82rem",
                "opacity": 0.68,
                "textAlign": "center",
                "paddingTop": "4px",
            },
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