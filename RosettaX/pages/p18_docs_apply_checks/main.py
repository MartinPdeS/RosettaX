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
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Checks Performed While Applying a Calibration",
                    description=(
                        "Apply is not a blind export step. This page documents the request and model checks RosettaX "
                        "runs before writing calibrated output files."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use these pages to connect apply checks to calibration payloads and reports.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Calibration payload",
                                    href="/documentation/calibration-payload",
                                ),
                                build_documentation_link_chip(
                                    label="Reports and provenance",
                                    href="/documentation/reports",
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
                self._checks_card(),
            ]
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
                    "For scattering diameter inversion, RosettaX checks whether the target Mie relation is strictly monotonic over the full requested range. If it is not, the apply workflow automatically selects the largest monotonic branch and records a warning so the export remains auditable.",
                ),
                html.Div(
                    "Export columns are normalized before writing output, and warnings collected during the apply run are surfaced again in the PDF report and result payload.",
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
