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
                        dbc.Col(self._quick_start_card(), lg=8),
                        dbc.Col(self._audience_card(), lg=4),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._subpages_card(), lg=7),
                        dbc.Col(self._hub_overview_card(), lg=5),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._coverage_card(),
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

    def _quick_start_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Quick Start Through The Documentation",
            subtitle="Follow this order when you need to understand a calibration from first principles to export checks.",
            body=[
                html.Div(
                    [
                        html.Div("1. System model and optics", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("Start with instrument assumptions, detector geometry, and where RosettaX sits in the workflow."),
                    ],
                    style={"marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div("2. Peak scripts and detector support", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("Confirm how peaks are extracted and whether your cytometer family uses an appropriate preset."),
                    ],
                    style={"marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div("3. Regression model and refractive index pages", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("Review the fitted equations and optical constants that turn detected peaks into calibration parameters."),
                    ],
                    style={"marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div("4. Payload, apply checks, and reports", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("Use these pages to validate what was saved, what is checked at apply time, and what provenance is retained."),
                    ]
                ),
            ],
            min_height="unset",
        )

    def _audience_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Who Should Use This Hub",
            subtitle="Documentation depth is tuned for practical calibration debugging and auditability.",
            body=[
                html.Div("Calibration operators who need repeatable procedures for day-to-day FCS processing."),
                html.Div("Method developers comparing detector geometry assumptions across instruments."),
                html.Div("Reviewers who need to trace exported files back to model choices and checks."),
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

    def _coverage_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Coverage Summary",
            subtitle="The documentation pages are organized by lifecycle stage so the same calibration can be understood end-to-end.",
            body=[
                html.Div("Configuration stage: system model, detector presets, and refractive index resolution."),
                html.Div("Calibration stage: peak scripts, regression fitting, and calibration payload structure."),
                html.Div("Application stage: apply checks, export-time warnings, and report provenance."),
                html.Div("Cross-stage navigation is intentionally redundant so a page can be read independently without losing context."),
            ],
            min_height="unset",
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
