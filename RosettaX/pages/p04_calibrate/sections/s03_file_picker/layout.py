# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms


logger = logging.getLogger(__name__)


class FilePickerLayout:
    """
    Layout builder for the input FCS file picker section.
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
            f"{self.page.ids.FilePicker.upload}-section-info-target"
        )

        self.header_tooltip_id = (
            f"{self.page.ids.FilePicker.upload}-section-info-tooltip"
        )

    def build_layout(self) -> dbc.Card:
        """
        Build the file picker layout.
        """
        logger.debug(
            "Building FilePicker layout for page=%s section_number=%r",
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
            title=f"{self.section_number}. Upload input FCS",
            tooltip_target_id=self.header_tooltip_target_id,
            tooltip_id=self.header_tooltip_id,
            tooltip_text=(
                "Upload one or more FCS files to apply a saved calibration. "
                "When multiple files are uploaded, RosettaX checks whether "
                "their channel structure is consistent before continuing."
            ),
            subtitle="Select the input cytometry files that will be calibrated.",
            color_name=self.card_color,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_upload_panel(),
                dash.html.Div(
                    style={
                        "height": "14px",
                    },
                ),
                self._build_alert(),
                self._build_upload_store(),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_upload_panel(self) -> dbc.Card:
        """
        Build the upload panel.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.html.Div(
                        [
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        "Input FCS files",
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    dash.html.Div(
                                        (
                                            "Upload a single file or a batch of files. "
                                            "Uploaded files are copied to the local "
                                            "RosettaX upload directory for this session."
                                        ),
                                        style=ui_forms.build_workflow_section_subtitle_style(
                                            font_size="0.9rem",
                                            opacity=0.72,
                                            margin_top_px=2,
                                        ),
                                    ),
                                ],
                                style={
                                    "marginBottom": "12px",
                                },
                            ),
                            self._build_upload_widget(),
                        ]
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

    def _build_upload_widget(self) -> dash.dcc.Upload:
        """
        Build the Dash upload widget.
        """
        return dash.dcc.Upload(
            id=self.page.ids.FilePicker.upload,
            children=dash.html.Div(
                [
                    dash.html.Span(
                        "Drag and drop or ",
                    ),
                    dash.html.A(
                        "select one or more .fcs files",
                        style={
                            "fontWeight": "650",
                            "textDecoration": "none",
                        },
                    ),
                ]
            ),
            multiple=True,
            style={
                "width": "100%",
                "minHeight": "64px",
                "lineHeight": "64px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "12px",
                "textAlign": "center",
                "cursor": "pointer",
                "background": "rgba(128, 128, 128, 0.045)",
                "borderColor": "rgba(128, 128, 128, 0.35)",
                "transition": "border-color 120ms ease, background 120ms ease",
            },
        )

    def _build_alert(self) -> dbc.Alert:
        """
        Build the upload status alert.
        """
        return dbc.Alert(
            "Upload one or more FCS files.",
            id=self.page.ids.FilePicker.column_consistency_alert,
            color="secondary",
            is_open=True,
            style={
                "marginBottom": "0px",
                "borderRadius": "10px",
            },
        )

    def _build_upload_store(self) -> dash.dcc.Store:
        """
        Build the uploaded file path store.
        """
        return dash.dcc.Store(
            id=self.page.ids.Stores.uploaded_fcs_path_store,
            storage_type="session",
        )