# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from .components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
)


class DocumentationPage:
    """
    Under-the-hood documentation for RosettaX.

    This page explains how RosettaX models fluorescence and scattering
    calibrations, what is written into calibration files, and which checks are
    enforced before calibrated exports are produced.
    """

    def __init__(self) -> None:
        self.page_name = "documentation"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                self._hero_section(),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._subpages_card(), lg=7),
                        dbc.Col(self._hub_overview_card(), lg=5),
                    ],
                    className="g-3",
                ),
            ]
        )

    def _hero_section(self) -> dbc.Card:
        return build_documentation_hero(
            hero_id=self._id("hero"),
            title="Documentation",
            description=(
                "This page is the RosettaX technical reference hub: how refractive indices are resolved, "
                "which regression models are fitted, what is saved into calibration JSON files, and which "
                "checks guard the apply workflow. Use the deep-dive pages below when you want fuller "
                "documentation for scripts, cytometer support, or regression behavior."
            ),
        )

    def _subpages_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Documentation sub-pages",
            subtitle="Use these pages for focused technical documentation by topic.",
            body=[
                html.Ul(
                    [
                        html.Li(html.A("System model and optics", href="/documentation/system-model", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Peak process scripts", href="/documentation/peak-scripts", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Supported flow cytometers", href="/documentation/supported-cytometers", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Material refractive index resolution", href="/documentation/refractive-index", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Calibration file wrapper and payload", href="/documentation/calibration-payload", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Apply calibration checks", href="/documentation/apply-checks", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Regression models", href="/documentation/regression-models", style={"textDecoration": "none", "fontWeight": "600"})),
                        html.Li(html.A("Reports and provenance", href="/documentation/reports", style={"textDecoration": "none", "fontWeight": "600"})),
                    ],
                    style={
                        "marginBottom": "0px",
                        "paddingLeft": "20px",
                        "display": "grid",
                        "rowGap": "8px",
                    },
                ),
            ],
            min_height="unset",
        )

    def _hub_overview_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to use this hub",
            subtitle="The page is arranged from overview to implementation details.",
            body=[
                html.Div(
                    [
                        html.Div("1. Pick a sub-page from the list", style={"fontWeight": "700", "marginBottom": "4px"}),
                        html.Div("Each sub-page focuses on one technical topic so you can find details quickly."),
                    ],
                    style={"marginBottom": "12px"},
                ),
                html.Div(
                    [
                        html.Div("2. Use related-page links inside each sub-page", style={"fontWeight": "700", "marginBottom": "4px"}),
                        html.Div("Those links move you between modeling assumptions, calibration structure, and apply behavior."),
                    ],
                    style={"marginBottom": "12px"},
                ),
                html.Div(
                    [
                        html.Div("3. Treat this page as an index", style={"fontWeight": "700", "marginBottom": "4px"}),
                        html.Div("The implementation details now live in dedicated pages rather than long inline sections."),
                    ]
                ),
            ],
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
