# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms


class HomePage:
    """
    Home page for RosettaX.

    Responsibilities
    ----------------
    - Present RosettaX in one clear message.
    - Help users choose one of the three main workflows.
    - Keep support and external resource links secondary.
    - Avoid help content that belongs on the help page.
    """

    def __init__(self) -> None:
        self.page_name = "home"

        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.pypi_url = "https://pypi.org/project/RosettaX/"
        self.anaconda_url = "https://anaconda.org/channels/MartinPdeS/packages/Rosettax/overview"
        self.documentation_url = "https://martinpdes.github.io/RosettaX/docs/latest/index.html"
        self.support_url = "https://github.com/sponsors/MartinPdeS"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"

    def _id(
        self,
        name: str,
    ) -> str:
        return f"{self.page_name}-{name}"

    def layout(
        self,
        **_kwargs,
    ) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._workflow_cards_row(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._secondary_actions_card(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._footer_links(),
            ],
            fluid=True,
            style={
                "paddingTop": "12px",
                "paddingBottom": "40px",
            },
        )

    def _hero_section(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            "RosettaX",
                            style={
                                "fontWeight": "800",
                                "fontSize": "2.55rem",
                                "lineHeight": "1.05",
                                "marginBottom": "8px",
                            },
                        ),
                        html.Div(
                            (
                                "A calibration workflow for bead based flow cytometry. "
                                "Build fluorescence and scattering calibrations, save them "
                                "as reusable records, then apply them to experimental FCS files."
                            ),
                            style={
                                "fontSize": "1.08rem",
                                "opacity": 0.86,
                                "maxWidth": "980px",
                                "marginBottom": "18px",
                            },
                        ),
                    ],
                    style={
                        "padding": "26px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _workflow_cards_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    self._workflow_card(
                        title="Fluorescence calibration",
                        subtitle="MESF based fluorescence response",
                        description=(
                            "Create a calibration from fluorescence bead peak positions "
                            "and known MESF reference values."
                        ),
                        steps=[
                            "Upload bead FCS",
                            "Detect fluorescence peaks",
                            "Review MESF table",
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
                        title="Scattering calibration",
                        subtitle="Mie based scattering response",
                        description=(
                            "Create a scattering calibration by linking measured bead "
                            "peaks to modeled optical coupling values."
                        ),
                        steps=[
                            "Upload bead FCS",
                            "Detect scattering peaks",
                            "Configure Mie model",
                            "Compute coupling",
                            "Fit response",
                            "Save calibration",
                        ],
                        button_text="Open scattering workflow",
                        button_href="/scattering",
                        button_color="primary",
                        button_id=self._id("scattering-link"),
                    ),
                    lg=4,
                ),
                dbc.Col(
                    self._workflow_card(
                        title="Apply calibration",
                        subtitle="Batch calibrated FCS export",
                        description=(
                            "Use a saved fluorescence or scattering calibration to add "
                            "calibrated channels to FCS files."
                        ),
                        steps=[
                            "Upload input FCS files",
                            "Select calibration",
                            "Configure target model",
                            "Choose export columns",
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
        title: str,
        subtitle: str,
        description: str,
        steps: list[str],
        button_text: str,
        button_href: str,
        button_color: str,
        button_id: str,
    ) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            title,
                            style={
                                "fontWeight": "760",
                                "fontSize": "1.08rem",
                                "lineHeight": "1.2",
                            },
                        ),
                        html.Div(
                            subtitle,
                            style={
                                "fontSize": "0.84rem",
                                "opacity": 0.72,
                                "marginTop": "3px",
                            },
                        ),
                    ],
                    style={
                        "background": "rgba(13, 110, 253, 0.06)",
                        "borderBottom": "1px solid rgba(13, 110, 253, 0.16)",
                        "padding": "12px 16px",
                        "borderTopLeftRadius": "12px",
                        "borderTopRightRadius": "12px",
                    },
                ),
                dbc.CardBody(
                    [
                        html.P(
                            description,
                            style={
                                "opacity": 0.82,
                                "minHeight": "66px",
                                "marginBottom": "14px",
                            },
                        ),
                        html.Div(
                            [
                                self._workflow_step_pill(
                                    index=index + 1,
                                    label=step,
                                )
                                for index, step in enumerate(
                                    steps,
                                )
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "7px",
                                "marginBottom": "16px",
                            },
                        ),
                        html.Div(
                            dbc.Button(
                                button_text,
                                href=button_href,
                                id=button_id,
                                color=button_color,
                                style={
                                    "width": "100%",
                                },
                            ),
                            style={
                                "marginTop": "auto",
                            },
                        ),
                    ],
                    style={
                        "height": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                        "padding": "16px",
                    },
                ),
            ],
            style={
                "height": "100%",
                "borderRadius": "12px",
                "border": "1px solid rgba(13, 110, 253, 0.16)",
                "boxShadow": "0 0.25rem 0.65rem rgba(0, 0, 0, 0.06)",
                "overflow": "visible",
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

    def _secondary_actions_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Project resources",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Documentation, source code, package links, and project support.",
                            style={
                                "fontSize": "0.86rem",
                                "opacity": 0.76,
                                "marginTop": "3px",
                            },
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    self._resource_button(
                                        label="Documentation",
                                        href=self.documentation_url,
                                        color="primary",
                                        outline=False,
                                        target="_blank",
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    self._resource_button(
                                        label="GitHub",
                                        href=self.github_url,
                                        color="dark",
                                        outline=True,
                                        target="_blank",
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    self._resource_button(
                                        label="PyPI",
                                        href=self.pypi_url,
                                        color="secondary",
                                        outline=True,
                                        target="_blank",
                                    ),
                                    md=2,
                                ),
                                dbc.Col(
                                    self._resource_button(
                                        label="Anaconda",
                                        href=self.anaconda_url,
                                        color="secondary",
                                        outline=True,
                                        target="_blank",
                                    ),
                                    md=2,
                                ),
                                dbc.Col(
                                    self._resource_button(
                                        label="Support",
                                        href=self.support_url,
                                        color="warning",
                                        outline=False,
                                        target="_blank",
                                    ),
                                    md=2,
                                ),
                            ],
                            className="g-2",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Contact: ",
                                    style={
                                        "fontWeight": "600",
                                    },
                                ),
                                html.A(
                                    self.contact_email,
                                    href=f"mailto:{self.contact_email}",
                                    id=self._id("email-link"),
                                ),
                            ],
                            style={
                                "fontSize": "0.86rem",
                                "opacity": 0.75,
                                "marginTop": "12px",
                            },
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _resource_button(
        self,
        *,
        label: str,
        href: str,
        color: str,
        outline: bool,
        target: str,
    ) -> dbc.Button:
        return dbc.Button(
            label,
            href=href,
            color=color,
            outline=outline,
            target=target,
            rel="noopener noreferrer",
            style={
                "width": "100%",
            },
        )

    def _footer_links(self) -> html.Div:
        return html.Div(
            "RosettaX is an open source scientific calibration tool for flow cytometry.",
            style={
                "fontSize": "0.82rem",
                "opacity": 0.62,
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