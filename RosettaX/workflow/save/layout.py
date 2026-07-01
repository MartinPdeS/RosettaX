# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.workflow.save.models import SaveConfig


logger = logging.getLogger(__name__)


class SaveLayout:
    """
    Reusable layout builder for calibration save sections.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: SaveConfig,
    ) -> None:
        self.ids = ids
        self.config = config

    def get_layout(self) -> dbc.Card:
        """
        Create the save section layout.
        """
        logger.debug(
            "Building save layout with header_title=%r",
            self.config.header_title,
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the save section header.
        """
        return dbc.CardHeader(
            self.config.header_title,
        )

    def _build_collapse(self) -> dbc.Collapse:
        """
        Build the save section collapse.
        """
        return dbc.Collapse(
            self._build_body(),
            id=self.ids.collapse,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the save section body.
        """
        return dbc.CardBody(
            [
                dash.html.Br(),
                dash.html.Div(
                    self._build_intro_text(),
                    style={
                        "marginBottom": "8px",
                    },
                ),
                self._build_save_row(),
                dash.html.Hr(),
                self._build_status_output(),
                dash.dcc.Download(
                    id=self.ids.download,
                ),
            ]
        )

    def _build_save_row(self) -> dash.html.Div:
        """
        Build the save row.
        """
        row_children: list[Any] = [
            self._build_file_name_input(),
        ]

        row_children.append(
            self._build_output_channel_name_input(),
        )

        row_children.append(
            self._build_save_button(),
        )

        return dash.html.Div(
            row_children,
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "flexWrap": "wrap",
            },
        )

    def _build_save_button(self) -> dbc.Button:
        """
        Build the save button.
        """
        return dbc.Button(
            self.config.button_text,
            id=self.ids.save_calibration_btn,
            n_clicks=0,
            color="secondary",
            disabled=True,
        )

    def _build_file_name_input(self) -> dash.dcc.Input:
        """
        Build the file name input.
        """
        return dash.dcc.Input(
            id=self.ids.file_name,
            type="text",
            value="",
            placeholder=self.config.file_name_placeholder,
            style={
                "width": "280px",
            },
        )

    def _build_output_channel_name_input(self) -> dash.dcc.Input:
        """
        Build the applied output channel name input.
        """
        return dash.dcc.Input(
            id=self.ids.output_channel_name,
            type="text",
            value="",
            placeholder=self.config.output_channel_name_placeholder,
            style={
                "width": "280px",
                "display": "block" if self.config.require_output_channel_name else "none",
            },
        )

    def _build_status_output(self) -> dash.html.Div:
        """
        Build the save status output.
        """
        return dash.html.Div(
            id=self.ids.save_out,
        )

    def _build_intro_text(self) -> str:
        """
        Build the explanatory save-section intro text.
        """
        if self.config.require_output_channel_name:
            return (
                "Enter a calibration name and the applied output channel name to enable download."
            )

        return "Enter a calibration name to enable download."
