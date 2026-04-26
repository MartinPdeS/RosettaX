# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html


class HomePage:
    """
    Home page for RosettaX.

    Responsibilities
    ----------------
    - Present the purpose of RosettaX.
    - Provide direct access to the main workflows.
    - Explain the recommended calibration workflow.
    - Provide project, support, and contribution links.
    """

    def __init__(self) -> None:
        self.page_name = "home"

        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.pypi_url = "https://pypi.org/project/RosettaX/"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(style={"height": "20px"}),
                self._primary_actions_row(),
                html.Div(style={"height": "20px"}),
                self._workflow_overview_row(),
                html.Div(style={"height": "20px"}),
                self._professional_notes_row(),
                html.Div(style={"height": "20px"}),
                self._support_and_project_row(),
            ],
            fluid=True,
        )

    def _hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        "Flow cytometry calibration workspace",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "700",
                                            "letterSpacing": "0.08em",
                                            "textTransform": "uppercase",
                                            "opacity": 0.72,
                                            "marginBottom": "10px",
                                        },
                                    ),
                                    html.H1(
                                        "RosettaX",
                                        style={
                                            "marginBottom": "10px",
                                            "fontWeight": "800",
                                            "fontSize": "2.4rem",
                                        },
                                    ),
                                    html.P(
                                        (
                                            "RosettaX provides an interactive workspace for building, "
                                            "reviewing, saving, and applying fluorescence and scattering "
                                            "calibrations from flow cytometry data."
                                        ),
                                        style={
                                            "fontSize": "1.08rem",
                                            "opacity": 0.92,
                                            "marginBottom": "16px",
                                            "maxWidth": "920px",
                                        },
                                    ),
                                    html.P(
                                        (
                                            "The application is designed for workflows where calibration "
                                            "traceability, detector consistency, and reproducible export "
                                            "of calibrated FCS files matter."
                                        ),
                                        style={
                                            "fontSize": "1.0rem",
                                            "opacity": 0.82,
                                            "marginBottom": "0px",
                                            "maxWidth": "920px",
                                        },
                                    ),
                                ],
                                md=8,
                            ),
                            dbc.Col(
                                self._status_card(),
                                md=4,
                            ),
                        ],
                        className="g-3 align-items-stretch",
                    )
                ]
            ),
            style={"height": "100%"},
        )

    def _status_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "Designed for",
                        style={
                            "marginTop": "0px",
                            "marginBottom": "12px",
                            "fontWeight": "700",
                        },
                    ),
                    html.Ul(
                        [
                            html.Li("Fluorescence calibration workflows"),
                            html.Li("Scattering calibration workflows"),
                            html.Li("Batch application to FCS files"),
                            html.Li("Saved calibration review and reuse"),
                        ],
                        style={
                            "marginBottom": "0px",
                            "paddingLeft": "20px",
                            "opacity": 0.9,
                        },
                    ),
                ]
            ),
            color="light",
            outline=True,
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
        return self._workflow_card(
            title="Fluorescence calibration",
            label="Build",
            description=(
                "Upload an FCS file, select the relevant fluorescence channel, detect "
                "reference bead populations, fit the calibration model, and save the "
                "resulting calibration record."
            ),
            button_text="Open fluorescence workflow",
            button_href="/fluorescence",
            button_color="success",
            button_id=self._id("fluorescence-link"),
        )

    def _scattering_card(self) -> dbc.Card:
        return self._workflow_card(
            title="Scattering calibration",
            label="Build",
            description=(
                "Configure optical and particle parameters, associate measured scatter "
                "signals with reference populations, review the fit, and save a scattering "
                "calibration payload."
            ),
            button_text="Open scattering workflow",
            button_href="/scattering",
            button_color="secondary",
            button_id=self._id("scattering-link"),
        )

    def _apply_card(self) -> dbc.Card:
        return self._workflow_card(
            title="Apply calibration",
            label="Export",
            description=(
                "Load one or more FCS files, select a saved calibration, choose source "
                "and target channels, and export calibrated files with consistent channel "
                "handling."
            ),
            button_text="Open apply workflow",
            button_href="/calibrate",
            button_color="primary",
            button_id=self._id("apply-link"),
        )

    def _workflow_overview_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._workflow_overview_card(), md=8),
                dbc.Col(self._configuration_card(), md=4),
            ],
            className="g-3",
        )

    def _workflow_overview_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Recommended workflow"),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    self._step_card(
                                        number="1",
                                        title="Prepare reference data",
                                        description=(
                                            "Start from FCS files acquired with well defined "
                                            "reference materials, detector settings, and channel names."
                                        ),
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    self._step_card(
                                        number="2",
                                        title="Build calibration",
                                        description=(
                                            "Use the fluorescence or scattering workflow to detect "
                                            "populations, inspect the fit, and save the calibration."
                                        ),
                                    ),
                                    md=4,
                                ),
                                dbc.Col(
                                    self._step_card(
                                        number="3",
                                        title="Apply and export",
                                        description=(
                                            "Apply saved calibrations to compatible FCS files and "
                                            "export calibrated channels for downstream analysis."
                                        ),
                                    ),
                                    md=4,
                                ),
                            ],
                            className="g-3",
                        )
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _configuration_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Profiles and defaults"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "Use profiles to manage default detector names, calibration "
                                "settings, plotting preferences, and application behavior."
                            ),
                            style={"opacity": 0.9},
                        ),
                        dbc.Button(
                            "Open settings",
                            href="/settings",
                            id=self._id("settings-link"),
                            color="dark",
                            outline=True,
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _professional_notes_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._quality_card(), md=6),
                dbc.Col(self._academic_use_card(), md=6),
            ],
            className="g-3",
        )

    def _quality_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Calibration quality checklist"),
                dbc.CardBody(
                    [
                        html.Ul(
                            [
                                html.Li("Use reference files acquired with documented instrument settings."),
                                html.Li("Keep detector and channel names consistent across files."),
                                html.Li("Inspect detected peaks before accepting a calibration fit."),
                                html.Li("Review the saved JSON payload before applying a calibration broadly."),
                                html.Li("Avoid mixing files acquired under incompatible voltage or gain settings."),
                            ],
                            style={"marginBottom": "0px"},
                        )
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _academic_use_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Academic and reproducible use"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "RosettaX is intended to make calibration workflows more transparent "
                                "by keeping calibration parameters, fit results, and export behavior "
                                "available for review."
                            ),
                            style={"opacity": 0.9},
                        ),
                        html.P(
                            (
                                "For manuscripts, reports, or shared datasets, keep the saved "
                                "calibration JSON files with the processed FCS files so the conversion "
                                "steps remain traceable."
                            ),
                            style={
                                "opacity": 0.9,
                                "marginBottom": "0px",
                            },
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _support_and_project_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._support_card(), md=4),
                dbc.Col(self._contribution_card(), md=4),
                dbc.Col(self._project_links_card(), md=4),
            ],
            className="g-3",
        )

    def _support_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Help and contact"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "For questions, bug reports, collaboration requests, or help with "
                                "calibration workflows, you can contact the maintainer directly."
                            ),
                            style={"opacity": 0.9},
                        ),
                        dbc.Button(
                            "Email maintainer",
                            href=f"mailto:{self.contact_email}",
                            id=self._id("email-link"),
                            color="primary",
                            style={
                                "width": "100%",
                                "marginBottom": "10px",
                            },
                        ),
                        html.Div(
                            self.contact_email,
                            style={
                                "fontSize": "0.9rem",
                                "opacity": 0.75,
                                "wordBreak": "break-word",
                            },
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _contribution_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Contribute"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "Contributions are useful for new reference materials, additional "
                                "instrument profiles, improved FCS compatibility, documentation, and "
                                "workflow validation."
                            ),
                            style={"opacity": 0.9},
                        ),
                        dbc.Button(
                            "Open repository",
                            href=self.github_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            color="dark",
                            outline=True,
                            id=self._id("contribute-github-link"),
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _project_links_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Project links"),
                dbc.CardBody(
                    [
                        dbc.Button(
                            "GitHub",
                            href=self.github_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            color="dark",
                            id=self._id("github-link"),
                            style={
                                "width": "100%",
                                "marginBottom": "10px",
                            },
                        ),
                        dbc.Button(
                            "PyPI",
                            href=self.pypi_url,
                            target="_blank",
                            rel="noopener noreferrer",
                            color="secondary",
                            id=self._id("pypi-link"),
                            style={
                                "width": "100%",
                                "marginBottom": "10px",
                            },
                        ),
                        dbc.Button(
                            "Help page",
                            href="/help",
                            color="primary",
                            outline=True,
                            id=self._id("help-link"),
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _workflow_card(
        self,
        *,
        title: str,
        label: str,
        description: str,
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
                            "fontSize": "0.75rem",
                            "fontWeight": "700",
                            "letterSpacing": "0.05em",
                            "textTransform": "uppercase",
                            "opacity": 0.72,
                            "marginBottom": "8px",
                        },
                    ),
                    html.H4(
                        title,
                        style={
                            "marginTop": "0px",
                            "marginBottom": "10px",
                            "fontWeight": "700",
                        },
                    ),
                    html.P(
                        description,
                        style={
                            "opacity": 0.9,
                            "minHeight": "128px",
                        },
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

    def _step_card(
        self,
        *,
        number: str,
        title: str,
        description: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        number,
                        style={
                            "width": "32px",
                            "height": "32px",
                            "borderRadius": "16px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontWeight": "700",
                            "border": "1px solid currentColor",
                            "marginBottom": "12px",
                        },
                    ),
                    html.H5(
                        title,
                        style={
                            "marginTop": "0px",
                            "marginBottom": "8px",
                            "fontWeight": "700",
                        },
                    ),
                    html.P(
                        description,
                        style={
                            "opacity": 0.9,
                            "marginBottom": "0px",
                        },
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