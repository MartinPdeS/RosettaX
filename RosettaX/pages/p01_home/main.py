
import importlib.metadata
import json
import logging
import time
from urllib import error, request

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX._version import __version__
from RosettaX.utils import ui_forms, usage_metrics

logger = logging.getLogger(__name__)
LATEST_GITHUB_TAG_API_URL = "https://api.github.com/repos/MartinPdeS/RosettaX/tags?per_page=1"
GITHUB_TAG_REQUEST_TIMEOUT_SECONDS = 2.0
GITHUB_TAG_CACHE_TTL_SECONDS = 300.0

_cached_github_tag_label: str | None = None
_cached_github_tag_expires_at = 0.0


def _fetch_latest_github_tag_label() -> str | None:
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

    try:
        local_version = importlib.metadata.version("RosettaX")
        return f"v{local_version}" if not local_version.startswith("v") else local_version
    except importlib.metadata.PackageNotFoundError:
        return "Unavailable"


class HomePage:
    """
    Home page for RosettaX.

    Responsibilities
    ----------------
    - Present RosettaX in one clear message.
    - Help users choose one of the main workflows.
    - Keep support and external resource links secondary.
    - Avoid help content that belongs on the help page.
    """

    def __init__(self) -> None:
        self.page_name = "home"

        self.github_url = "https://github.com/MartinPdeS/RosettaX"
        self.pypi_url = "https://pypi.org/project/RosettaX/"
        self.anaconda_url = "https://anaconda.org/channels/MartinPdeS/packages/Rosettax/overview"
        self.documentation_url = "/documentation"
        self.install_local_release_url = "/documentation/install-local"
        self.support_url = "https://github.com/sponsors/MartinPdeS"
        self.lab_url = "https://www.vesiclecenter.com/"
        self.contact_email = "martin.poinsinet.de.sivry@gmail.com"
        self.citation_url = "/citation"
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
        try:
            metrics = usage_metrics.record_home_page_visit()
        except Exception:
            logger.exception("Failed to record home page visit metric.")
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
                self._tools_overview_card(),
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
        local_version_label = (
            __version__ if __version__.startswith("v") else f"v{__version__}"
        )

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
                    local_version_label,
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
                                "Build and apply flow-cytometry calibrations, then inspect and prepare FCS data."
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
                                    href=self.citation_url,
                                    color="primary",
                                    outline=True,
                                ),
                                dbc.Button(
                                    "Amsterdam Vesicle Center",
                                    href=self.lab_url,
                                    color="info",
                                    outline=True,
                                    target="_blank",
                                    rel="noopener noreferrer",
                                ),
                                dbc.Button(
                                    "Install locally (Releases)",
                                    href=self.install_local_release_url,
                                    color="secondary",
                                    outline=True,
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

    def _tools_overview_card(self) -> dbc.Card:
        """Explain the task-oriented groups available in the sidebar."""
        tool_descriptions = [
            (
                "Calibrations",
                "Create fluorescence, scattering, or cross-calibrations, or apply a saved calibration.",
            ),
            (
                "FCS tools",
                "Visualize FCS data or create file slices for focused downstream work.",
            ),
            (
                "Manage",
                "Choose a profile and access sample files.",
            ),
            (
                "Learn",
                "Read the documentation or get help with RosettaX.",
            ),
        ]
        card = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        "What you can do",
                        style={"fontWeight": "750", "fontSize": "1.02rem"},
                    )
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        title,
                                        style={
                                            "fontWeight": "700",
                                            "marginBottom": "5px",
                                        },
                                    ),
                                    html.Div(
                                        description,
                                        style={"fontSize": "0.92rem", "opacity": 0.82},
                                    ),
                                ],
                                md=6,
                                lg=3,
                            )
                            for title, description in tool_descriptions
                        ],
                        className="g-3",
                    ),
                    style={"padding": "16px"},
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
                    ]
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                self._usage_metric_tile(
                                    value=str(metrics.home_page_visit_count),
                                    label="Home page visits",
                                ),
                                md=4,
                            ),
                            dbc.Col(
                                self._usage_metric_tile(
                                    value=str(metrics.apply_button_click_count),
                                    label="Apply button clicks",
                                ),
                                md=4,
                            ),
                            dbc.Col(
                                self._usage_metric_tile(
                                    value=str(metrics.total_calibrated_files),
                                    label="Total calibrated files",
                                ),
                                md=4,
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
    name="RosettaX - Amsterdam Vesicle Center",
    order=0,
    layout=layout,
)
