# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


class Header:
    def __init__(
        self,
        page,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.card_color = card_color

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Apply calibration",
                        title_component="H2",
                        description=(
                            "Use this page when you already have a saved calibration and want to apply it "
                            "to one or more FCS files. Select the calibration payload, upload the target "
                            "files, choose the relevant detector mapping, and export calibrated outputs."
                        ),
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
            id=self.page.ids.Header.container,
            style={
                **ui_forms.build_workflow_section_card_style(
                    color_name=self.card_color,
                ),
                "marginBottom": "16px",
            },
        )

    def register_callbacks(self) -> None:
        """
        This section is static and does not register Dash callbacks.
        """
        return

    def _build_steps(self) -> list[dict[str, str]]:
        """
        Build the apply calibration workflow step metadata.
        """
        return [
            {
                "number": "1",
                "title": "Select calibration",
                "description": (
                    "Choose the saved fluorescence or scattering calibration JSON "
                    "that will be applied to the uploaded data. For scattering "
                    "payloads, confirm the target particle model before continuing."
                ),
                "color_name": styling.get_workflow_section_color(1),
            },
            {
                "number": "2",
                "title": "Upload input FCS",
                "description": (
                    "Load one or more experimental FCS files that should receive "
                    "the calibrated output channels."
                ),
                "color_name": styling.get_workflow_section_color(2),
            },
            {
                "number": "3",
                "title": "Apply and export",
                "description": (
                    "Choose optional extra raw channels to preserve, run the "
                    "calibration, and download the calibrated export package."
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
        """
        Build one workflow step card.
        """
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
