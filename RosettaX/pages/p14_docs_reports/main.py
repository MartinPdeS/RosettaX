# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
    build_documentation_link_chip,
)


class ReportsDocumentationPage:
    """
    Detailed documentation for RosettaX reports and provenance.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-reports"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Reports and Provenance",
                    description=(
                        "This page explains what RosettaX PDF reports are for, which details they preserve from an apply run, "
                        "and how they complement calibration JSON rather than replacing it."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use the documentation hub to move between report behavior and the underlying calibration model.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Regression models",
                                    href="/documentation/regression-models",
                                ),
                                build_documentation_link_chip(
                                    label="Supported cytometers",
                                    href="/documentation/supported-cytometers",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "10px",
                            },
                        ),
                    ],
                    min_height="unset",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._report_contents_card(), lg=6),
                        dbc.Col(self._json_vs_pdf_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._artifact_card(), lg=7),
                        dbc.Col(self._review_workflow_card(), lg=5),
                    ],
                    className="g-3",
                ),
            ]
        )

    def _report_contents_card(self) -> dbc.Card:
        return build_documentation_card(
            title="What the PDF report records",
            subtitle="The report is a run-level record of one apply/export action.",
            body=[
                html.Div(
                    "The apply report records the selected calibration, uploaded FCS paths, chosen export columns, output channels, warnings, and a sanitized snapshot of the saved calibration payload so the run can still be interpreted later.",
                ),
                html.Div(
                    "That makes the report useful for auditing how one exported dataset was produced, even if the original RosettaX session is no longer open.",
                ),
            ],
        )

    def _json_vs_pdf_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How the report differs from calibration JSON",
            subtitle="The JSON and the PDF answer different questions.",
            body=[
                html.Div(
                    "Use the calibration JSON to answer what the calibration is: the fitted relation, source channel, reference table, and model assumptions that define the calibration itself.",
                ),
                html.Div(
                    "Use the PDF to answer what happened during a specific apply run: which files were processed, which warnings appeared, and what export choices were made at that moment.",
                ),
            ],
        )

    def _artifact_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How provenance stays attached to exports",
            subtitle="RosettaX tries to keep the result artifact and its explanation together.",
            body=[
                html.Div(
                    "When the export artifact is a ZIP archive, the PDF report is embedded in that archive alongside the calibrated FCS files. This keeps the output files and their provenance in one place instead of splitting them across screenshots, notes, or email threads.",
                ),
                html.Div(
                    "The practical goal is reproducibility: someone opening the export later should be able to see both the calibrated files and the report that explains how they were generated.",
                ),
            ],
            min_height="unset",
        )

    def _review_workflow_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Recommended review workflow",
            subtitle="A lightweight audit path after each apply run.",
            body=[
                html.Div("Open the report first and verify source files, selected calibration, and warning summary."),
                html.Div("Cross-check report context against calibration JSON when coefficients or assumptions look unusual."),
                html.Div("Archive calibrated outputs and report together; avoid separating files from provenance metadata."),
                html.Div("If JSON and PDF disagree, treat it as a documentation inconsistency and re-run apply."),
            ],
            min_height="unset",
        )


_page = ReportsDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/reports",
    name="Reports Documentation",
    layout=layout,
)
