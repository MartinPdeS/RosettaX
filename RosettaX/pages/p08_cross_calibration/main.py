# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling, ui_forms


class CrossCalibrationPage:
    """
    Placeholder page for upcoming cross calibration workflows.
    """

    def __init__(self) -> None:
        self.style = styling.PAGE

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                self._build_header_card(),
            ],
            fluid=True,
            style=self.style,
        )

    def _build_header_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Cross calibration",
                        title_component="H2",
                        description=(
                            "Combine fluorescence and scattering calibration artifacts into a "
                            "shared cross-calibration relation for downstream reporting and "
                            "multi-channel interpretation."
                        ),
                    ),
                    dbc.Alert(
                        [
                            html.Strong("Under construction: "),
                            "this workflow is still being built and some controls or outputs may change.",
                        ],
                        color="warning",
                        className="mb-3",
                        style={
                            "marginBottom": "14px",
                        },
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                self._build_step_card(
                                    number=step["number"],
                                    title=step["title"],
                                    description=step["description"],
                                    color_name=step["color_name"],
                                ),
                                xs=12,
                                md=6,
                                lg=4,
                                style={
                                    "marginBottom": "10px",
                                },
                            )
                            for step in self._build_steps()
                        ],
                        className="g-2",
                    ),
                ],
                style=ui_forms.build_workflow_section_body_style(),
            ),
            style={
                **ui_forms.build_workflow_section_card_style(
                    color_name=styling.get_workflow_page_header_color(),
                ),
                "marginBottom": "16px",
            },
        )

    def _build_steps(self) -> list[dict[str, str]]:
        return [
            {
                "number": "1",
                "title": "Load calibrations",
                "description": (
                    "Select compatible fluorescence and scattering calibrations that were "
                    "derived for the same instrument context."
                ),
                "color_name": styling.get_workflow_section_color(1),
            },
            {
                "number": "2",
                "title": "Resolve mapping",
                "description": (
                    "Map shared bead populations and detector channels to build a stable "
                    "cross-domain calibration relation."
                ),
                "color_name": styling.get_workflow_section_color(2),
            },
            {
                "number": "3",
                "title": "Export relation",
                "description": (
                    "Review the generated relation and export a reusable cross-calibration "
                    "artifact for downstream analysis."
                ),
                "color_name": styling.get_workflow_section_color(3),
            },
        ]

    def _build_step_card(
        self,
        *,
        number: str,
        title: str,
        description: str,
        color_name: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        number,
                        style={
                            "width": "28px",
                            "height": "28px",
                            "borderRadius": "50%",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontWeight": "700",
                            "fontSize": "0.9rem",
                            "backgroundColor": styling.build_rgba(
                                color_name,
                                0.12,
                            ),
                            "border": f"1px solid {styling.build_rgba(color_name, 0.35)}",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H6(
                        title,
                        style={
                            "marginBottom": "6px",
                        },
                    ),
                    html.P(
                        description,
                        style={
                            "marginBottom": "0px",
                            "fontSize": "0.86rem",
                            "opacity": 0.78,
                        },
                    ),
                ],
                style={
                    "height": "100%",
                    "padding": "14px",
                },
            ),
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=color_name,
                style_overrides={
                    "height": "100%",
                },
            ),
        )


_page = CrossCalibrationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/cross-calibration",
    name="Cross Calibration",
    order=3,
    layout=layout,
)
