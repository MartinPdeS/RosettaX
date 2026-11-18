
import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_guide_header,
)


class ApplyChecksDocumentationPage:
    """
    Detailed documentation for checks performed during apply calibration.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-apply-checks"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_guide_header(
                    hero_id=self._id("hero"),
                    title="Checks Performed While Applying a Calibration",
                    description="Review the checks RosettaX runs before export and learn how to interpret their warnings.",
                    related=[
                        ("Calibration payload", "/documentation/calibration-payload"),
                        ("Reports and provenance", "/documentation/reports"),
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(self._checks_card(), lg=7),
                        dbc.Col(self._warning_interpretation_card(), lg=5),
                    ],
                    className="g-3",
                ),
            ],
            class_name="rosettax-docs-guide",
        )

    def _checks_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Apply-time checks",
            subtitle="Validation is performed on both the request and the requested target model.",
            body=[
                html.Div(
                    "At the request level, RosettaX requires at least one uploaded FCS file, a selected calibration, and a non-empty calibration payload. It also resolves the source channel from the payload and fails if that channel is missing.",
                ),
                html.Div(
                    "If the calibration is scattering, target model parameters are mandatory. Diameter grids must be positive and ordered correctly, refractive indices must be finite and physically valid, and the requested source channel must exist in each input dataframe.",
                ),
                html.Div(
                    "For scattering diameter inversion, RosettaX checks whether the target Mie relation is strictly monotonic over the full requested range. If it is not, the apply workflow automatically selects the left-most monotonic branch and records a warning so the export remains auditable.",
                ),
                html.Div(
                    "Export columns are normalized before writing output, and warnings collected during the apply run are surfaced again in the PDF report and result payload.",
                ),
            ],
            min_height="unset",
        )

    def _warning_interpretation_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to interpret apply warnings",
            subtitle="Check the issue type before sharing an export.",
            body=[
                html.Dl(
                    [
                        html.Dt("Blocking error"),
                        html.Dd("Fix the missing channel or incomplete calibration payload before exporting."),
                        html.Dt("Restricted inversion"),
                        html.Dd("A non-monotonic target relation can limit inversion to the left-most monotonic branch. Check the warning in the report."),
                        html.Dt("Recurring warning"),
                        html.Dd("Review the inputs and target model when the same warning appears across multiple runs."),
                    ],
                    className="rosettax-docs-definition-list",
                ),
            ],
            min_height="unset",
        )


_page = ApplyChecksDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/apply-checks",
    name="Apply Checks Documentation",
    layout=layout,
)
