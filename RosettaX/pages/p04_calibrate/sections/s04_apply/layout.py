# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


logger = logging.getLogger(__name__)


class ApplyLayout:
    """
    Layout builder for the apply and export section.
    """

    def __init__(
        self,
        *,
        page: Any,
        section_number: int,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color

        self.header_tooltip_target_id = (
            f"{self.page.ids.Export.apply_and_export_button}-section-info-target"
        )

        self.header_tooltip_id = (
            f"{self.page.ids.Export.apply_and_export_button}-section-info-tooltip"
        )

        self.export_columns_tooltip_target_id = (
            f"{self.page.ids.Export.export_columns_dropdown}-info-target"
        )

        self.export_columns_tooltip_id = (
            f"{self.page.ids.Export.export_columns_dropdown}-info-tooltip"
        )

        self.apply_button_tooltip_target_id = (
            f"{self.page.ids.Export.apply_and_export_button}-info-target"
        )

        self.apply_button_tooltip_id = (
            f"{self.page.ids.Export.apply_and_export_button}-info-tooltip"
        )

    def build_layout(self) -> dbc.Card:
        """
        Build the apply and export layout.
        """
        logger.debug(
            "Building Apply layout for page=%s section_number=%r",
            self.page.__class__.__name__,
            self.section_number,
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Apply and export",
            tooltip_target_id=self.header_tooltip_target_id,
            tooltip_id=self.header_tooltip_id,
            tooltip_text=(
                "Apply the selected calibration to the uploaded FCS files, "
                "choose optional extra channels to preserve, and export the "
                "calibrated output files."
            ),
            subtitle=(
                "Generate calibrated FCS outputs from the selected calibration "
                "and input files."
            ),
            color_name=self.card_color,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_export_columns_panel(),
                dash.html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._build_action_panel(),
                dash.html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._build_status_alert(),
                dash.dcc.Download(
                    id=self.page.ids.Export.download,
                ),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_export_columns_panel(self) -> dbc.Card:
        """
        Build the extra export columns selector panel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Export columns",
                            tooltip_target_id=self.export_columns_tooltip_target_id,
                            tooltip_id=self.export_columns_tooltip_id,
                            tooltip_text=(
                                "Select optional channels to preserve in the exported "
                                "files. The calibration source channel is always included."
                            ),
                            title_style_overrides={
                                "fontSize": "0.98rem",
                            },
                        ),
                        dash.html.Div(
                            "Choose additional raw channels to copy unchanged into the output files.",
                            style=ui_forms.build_workflow_section_subtitle_style(
                                font_size="0.84rem",
                            ),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.card_color,
                    ),
                ),
                dbc.CardBody(
                    [
                        dash.dcc.Dropdown(
                            id=self.page.ids.Export.export_columns_dropdown,
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Select extra columns to export",
                            clearable=True,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "100%",
                            },
                        ),
                        dash.html.Div(
                            style={
                                "height": "8px",
                            },
                        ),
                        dash.html.Small(
                            (
                                "The calibration source channel will always be included. "
                                "These extra columns will be exported unchanged."
                            ),
                            style={
                                "opacity": 0.75,
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_panel_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_action_panel(self) -> dbc.Card:
        """
        Build the apply and export action panel.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.html.Div(
                        [
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        "Calibration export",
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    dash.html.Div(
                                        (
                                            "Apply the selected calibration to every uploaded "
                                            "FCS file and package the calibrated outputs for download."
                                        ),
                                        style=ui_forms.build_workflow_section_subtitle_style(
                                            font_size="0.9rem",
                                            opacity=0.72,
                                            margin_top_px=2,
                                        ),
                                    ),
                                ],
                                style={
                                    "flex": "1 1 auto",
                                },
                            ),
                            dash.html.Div(
                                [
                                    dbc.Button(
                                        "Apply & export",
                                        id=self.page.ids.Export.apply_and_export_button,
                                        n_clicks=0,
                                        color="primary",
                                    ),
                                    ui_forms.build_info_badge(
                                        tooltip_target_id=self.apply_button_tooltip_target_id,
                                    ),
                                    dbc.Tooltip(
                                        (
                                            "Run the calibration on the uploaded FCS files "
                                            "and prepare the exported calibrated files for download."
                                        ),
                                        id=self.apply_button_tooltip_id,
                                        target=self.apply_button_tooltip_target_id,
                                        placement="right",
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "0px",
                                    "flex": "0 0 auto",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "gap": "16px",
                            "flexWrap": "wrap",
                        },
                    ),
                ],
                style={
                    "padding": "14px 16px",
                },
            ),
            style=ui_forms.build_workflow_panel_style(
                color_name=self.card_color,
                background=styling.build_rgba(
                    self.card_color,
                    0.04,
                ),
            ),
        )

    def _build_status_alert(self) -> dbc.Alert:
        """
        Build the status alert.
        """
        return dbc.Alert(
            "Status will appear here.",
            id=self.page.ids.Export.status,
            color="secondary",
            style={
                "marginBottom": "0px",
                "borderRadius": "10px",
            },
        )