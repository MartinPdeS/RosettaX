import dash
import dash_bootstrap_components as dbc
from .components import build_documentation_container
from dash import dcc, html

DOCUMENTATION_TOPICS = (
    (
        "Setup and instruments",
        (
            ("Install RosettaX", "/documentation/install-local", "Install a local copy from a release."),
            ("Supported flow cytometers", "/documentation/supported-cytometers", "Find your instrument and its detector presets."),
        ),
    ),
    (
        "Scattering and optics",
        (
            ("System model and optics", "/documentation/system-model", "Understand detector geometry and angular collection."),
            ("Material refractive index", "/documentation/refractive-index", "See how material names resolve to refractive indices."),
        ),
    ),
    (
        "Peak detection and fitting",
        (
            ("Peak process scripts", "/documentation/peak-scripts", "See how each peak detection method selects bead populations."),
            ("Regression models", "/documentation/regression-models", "Review the equations that fit calibration curves."),
        ),
    ),
    (
        "Calibration files and validation",
        (
            ("Calibration file format", "/documentation/calibration-payload", "Inspect the fields saved in a calibration JSON file."),
            ("Apply calibration checks", "/documentation/apply-checks", "Check input compatibility and scattering limits."),
            ("Reports and provenance", "/documentation/reports", "See which settings and results are recorded in exports."),
        ),
    ),
)


class DocumentationPage:
    """Index of the RosettaX technical guides."""

    def __init__(self) -> None:
        self.page_name = "documentation"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        """Build the documentation index with guides grouped by topic."""
        return build_documentation_container(
            [
                html.Header(
                    [
                        html.H1("Documentation", id=self._id("hero")),
                        html.P("Guides for setting up, building, and applying a calibration."),
                    ],
                    className="rosettax-docs-intro",
                ),
                html.Nav(
                    [
                        html.Section(
                            [
                                html.H2(topic),
                                html.Ul(
                                    [
                                        html.Li(
                                            dcc.Link(
                                                [
                                                    html.Span(title, className="rosettax-docs-link-title"),
                                                    html.Span(description, className="rosettax-docs-link-description"),
                                                    html.Span("→", className="rosettax-docs-link-arrow", **{"aria-hidden": "true"}),
                                                ],
                                                href=href,
                                            )
                                        )
                                        for title, href, description in guides
                                    ]
                                ),
                            ]
                        )
                        for topic, guides in DOCUMENTATION_TOPICS
                    ],
                    className="rosettax-docs-topics",
                    **{"aria-label": "Documentation topics"},
                ),
            ]
        )


_page = DocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation",
    name="Documentation",
    order=5,
    layout=layout,
)
