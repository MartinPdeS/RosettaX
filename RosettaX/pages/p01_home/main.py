# -*- coding: utf-8 -*-

import json
import logging
import time
from typing import Optional
from urllib import error, request

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms
from RosettaX.utils import usage_metrics


logger = logging.getLogger(__name__)
LATEST_GITHUB_TAG_API_URL = "https://api.github.com/repos/MartinPdeS/RosettaX/tags?per_page=1"
GITHUB_TAG_REQUEST_TIMEOUT_SECONDS = 2.0
GITHUB_TAG_CACHE_TTL_SECONDS = 300.0

_cached_github_tag_label: Optional[str] = None
_cached_github_tag_expires_at = 0.0


def _fetch_latest_github_tag_label() -> Optional[str]:
    request_headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RosettaX",
    }
    github_request = request.Request(
        LATEST_GITHUB_TAG_API_URL,
        headers=request_headers,
    )

    try:
        with request.urlopen(
            github_request,
            timeout=GITHUB_TAG_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            payload = json.load(response)
    except (error.URLError, error.HTTPError, OSError, TimeoutError, ValueError) as exc:
        logger.debug(
            "Failed to fetch latest GitHub tag from %s: %s",
            LATEST_GITHUB_TAG_API_URL,
            exc,
        )
        return None

    if not isinstance(payload, list) or not payload:
        logger.debug(
            "GitHub tag payload was empty or invalid: %r",
            payload,
        )
        return None

    latest_tag_name = str(payload[0].get("name", "")).strip()

    if not latest_tag_name:
        logger.debug("Latest GitHub tag payload did not include a tag name: %r", payload[0])
        return None

    if latest_tag_name.lower().startswith("v"):
        return latest_tag_name

    return f"v{latest_tag_name}"


def resolve_latest_github_tag_label() -> str:
    global _cached_github_tag_label
    global _cached_github_tag_expires_at

    current_time = time.monotonic()

    if (
        _cached_github_tag_label is not None
        and current_time < _cached_github_tag_expires_at
    ):
        return _cached_github_tag_label

    fetched_label = _fetch_latest_github_tag_label()

    if fetched_label is not None:
        _cached_github_tag_label = fetched_label
        _cached_github_tag_expires_at = current_time + GITHUB_TAG_CACHE_TTL_SECONDS
        return fetched_label

    _cached_github_tag_expires_at = current_time + GITHUB_TAG_CACHE_TTL_SECONDS

    if _cached_github_tag_label is not None:
        return _cached_github_tag_label

    return "Unavailable"


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
        self.documentation_url = "/documentation"
        self.support_url = "https://github.com/sponsors/MartinPdeS"
        self.lab_url = "https://www.vesiclecenter.com/"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"
        self.zenodo_doi_url = "https://doi.org/10.5281/zenodo.20709591"
        self.zenodo_badge_url = "https://zenodo.org/badge/1087203577.svg"

    def _id(
        self,
        name: str,
    ) -> str:
        return f"{self.page_name}-{name}"

    def layout(
        self,
        **_kwargs,
    ) -> dbc.Container:
        metrics = usage_metrics.load_usage_metrics()

        return dbc.Container(
            [
                self._github_tag_widget(),
                html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._hero_section(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._citation_card(),
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
                self._usage_metrics_card(metrics=metrics),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
            ],
            fluid=True,
            style={
                "paddingTop": "12px",
                "paddingBottom": "40px",
            },
        )

    def _github_tag_widget(self) -> html.Div:
        github_tag_label = resolve_latest_github_tag_label()

        return html.Div(
            [
                html.Span(
                    "Version:",
                    style={
                        "fontSize": "0.72rem",
                        "fontWeight": "700",
                        "letterSpacing": "0.08em",
                        "textTransform": "uppercase",
                        "opacity": 0.7,
                    },
                ),
                html.Span(
                    github_tag_label,
                    style={
                        "fontSize": "0.92rem",
                        "fontWeight": "700",
                    },
                ),
            ],
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "gap": "10px",
                "padding": "8px 12px",
                "borderRadius": "999px",
                "border": "1px solid rgba(128, 128, 128, 0.22)",
                "background": "rgba(255, 255, 255, 0.55)",
                "backdropFilter": "blur(8px)",
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
                                "Convert raw single-particle flow cytometry data into calibrated measurements. "
                                "Perform fluorescence and light-scattering calibrations, save calibration records, "
                                "and apply them to FCS files."
                            ),
                            style={
                                "fontSize": "1.08rem",
                                "opacity": 0.86,
                                "maxWidth": "980px",
                                "marginBottom": "0px",
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

    def _citation_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        "Support, citation, and lab",
                        style={
                            "fontWeight": "750",
                            "fontSize": "1.02rem",
                        },
                    )
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            (
                                "Support ongoing RosettaX development, cite the work in publications, "
                                "and find the lab affiliation below."
                            ),
                            style={
                                "fontSize": "0.95rem",
                                "opacity": 0.88,
                                "marginBottom": "14px",
                            },
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Support Developer",
                                    href=self.support_url,
                                    color="warning",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    style={
                                        "fontWeight": "700",
                                    },
                                ),
                                dbc.Button(
                                    "Citing this work",
                                    href=self.zenodo_doi_url,
                                    color="primary",
                                    outline=True,
                                    target="_blank",
                                    rel="noopener noreferrer",
                                ),
                                dbc.Button(
                                    "Amsterdam Vesicle Center",
                                    href=self.lab_url,
                                    color="info",
                                    outline=True,
                                    target="_blank",
                                    rel="noopener noreferrer",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "gap": "10px",
                                "flexWrap": "wrap",
                                "marginBottom": "0px",
                            },
                        ),
                    ],
                    style={
                        "padding": "20px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _usage_metrics_card(
        self,
        *,
        metrics: usage_metrics.UsageMetrics,
    ) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "RosettaX usage metrics.",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "",
                            style={
                                "fontSize": "0.86rem",
                                "opacity": 0.76,
                                "marginTop": "3px",
                            },
                        ),
                    ]
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                self._usage_metric_tile(
                                    value=str(metrics.apply_button_click_count),
                                    label="Apply button clicks",
                                ),
                                md=6,
                            ),
                            dbc.Col(
                                self._usage_metric_tile(
                                    value=str(metrics.total_calibrated_files),
                                    label="Total calibrated files",
                                ),
                                md=6,
                            ),
                        ],
                        className="g-3",
                    ),
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

    def _usage_metric_tile(
        self,
        *,
        value: str,
        label: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(
                    value,
                    style={
                        "fontSize": "2rem",
                        "fontWeight": "800",
                        "lineHeight": "1.0",
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.92rem",
                        "opacity": 0.76,
                        "marginTop": "6px",
                    },
                ),
            ],
            style={
                "padding": "18px",
                "borderRadius": "12px",
                "border": "1px solid rgba(13, 110, 253, 0.16)",
                "background": "rgba(13, 110, 253, 0.04)",
                "height": "100%",
            },
        )

    def _workflow_cards_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    self._workflow_card(
                        title="Fluorescence calibration",
                        subtitle="",
                        description=(
                            "Convert arbitrary units of fluorescence intensity into standard units (ABC, ERF, or MESF)."
                        ),
                        steps=[
                            "Upload bead FCS file",
                            "Detect fluorescence peaks",
                            "Add standard units to calibration table",
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
                        subtitle="",
                        description=(
                            "Convert arbitrary units of scattering intensity into standard units of scattering cross section (nm2) and particle diameter (nm)."
                        ),
                        steps=[
                            "Upload bead FCS file",
                            "Detect scattering peaks",
                            "Set optical configuration",
                            "Add standard units to calibration table",
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
                        subtitle="",
                        description=(
                            "Use saved fluorescence and/or scattering calibrations to add calibrated parameters to FCS files."
                        ),
                        steps=[
                            "Select calibration",
                            "Upload uncalibrated FCS file(s)",
                            "Select parameters to export",
                            "Apply and export calibrated FCS file(s)",
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
                                        target="_self",
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
                                    md=2,
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
                                        label="Support Developer",
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
    path="/",
    redirect_from=["/home"],
    name="RosettaX",
    order=0,
    layout=layout,
)