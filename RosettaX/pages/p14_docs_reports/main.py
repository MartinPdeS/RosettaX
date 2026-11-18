
import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_guide_header,
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
                build_documentation_guide_header(
                    hero_id=self._id("hero"),
                    title="Reports and Provenance",
                    description="See what the PDF report records and how to review it alongside the calibration JSON.",
                    related=[
                        ("Regression models", "/documentation/regression-models"),
                        ("Supported cytometers", "/documentation/supported-cytometers"),
                    ],
                ),
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
            ],
            class_name="rosettax-docs-guide",
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
            subtitle="Use both files to trace the calibration and the run that applied it.",
            body=[
                html.Dl(
                    [
                        html.Dt("Calibration JSON"),
                        html.Dd("Defines the fitted relation, source channel, reference table, and model assumptions."),
                        html.Dt("PDF report"),
                        html.Dd("Records the input files, export choices, and warnings for a specific apply run."),
                    ],
                    className="rosettax-docs-definition-list",
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
                html.Ol(
                    [
                        html.Li("Open the report first and verify source files, selected calibration, and warning summary."),
                        html.Li("Cross-check report context against calibration JSON when coefficients or assumptions look unusual."),
                        html.Li("Archive calibrated outputs and report together; avoid separating files from provenance metadata."),
                        html.Li("If JSON and PDF disagree, treat it as a documentation inconsistency and re-run apply."),
                    ],
                    className="rosettax-docs-list",
                ),
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
