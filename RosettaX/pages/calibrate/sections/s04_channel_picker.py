# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.reader import FCSFile
from RosettaX.utils import service


logger = logging.getLogger(__name__)


class ChannelPickerSection:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ChannelPickerSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("2. Select target channel"),
                dbc.CardBody(
                    [
                        dash.html.Div("Target channel", style={"marginBottom": "6px"}),
                        dash.dcc.Dropdown(
                            id=self.page.ids.ChannelPicker.dropdown,
                            options=[],
                            value=None,
                            placeholder="Select channel",
                            clearable=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering channel picker callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.ChannelPicker.dropdown, "options"),
            dash.Output(self.page.ids.ChannelPicker.dropdown, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.ChannelPicker.dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_channels(
            uploaded_fcs_path_data: Any,
            current_dropdown_value: Any,
        ) -> tuple:
            return self._populate_channels(
                uploaded_fcs_path_data=uploaded_fcs_path_data,
                current_dropdown_value=current_dropdown_value,
            )

    def _populate_channels(
        self,
        *,
        uploaded_fcs_path_data: Any,
        current_dropdown_value: Any,
    ) -> tuple:
        logger.debug(
            "_populate_channels called with uploaded_fcs_path_data=%r current_dropdown_value=%r",
            uploaded_fcs_path_data,
            current_dropdown_value,
        )

        first_uploaded_fcs_path = service.resolve_first_fcs_path(
            uploaded_fcs_path_data
        )

        if not first_uploaded_fcs_path:
            logger.debug("No uploaded FCS path available. Returning empty dropdown.")
            return [], None

        try:
            with FCSFile(first_uploaded_fcs_path, writable=False) as fcs_file:
                column_names = fcs_file.get_column_names()
        except Exception:
            logger.exception(
                "Could not read channels from uploaded FCS file: %r",
                first_uploaded_fcs_path,
            )
            return [], None

        dropdown_options = [
            {
                "label": column_name,
                "value": column_name,
            }
            for column_name in column_names
        ]

        if not dropdown_options:
            logger.debug(
                "No channels found in uploaded FCS file: %r",
                first_uploaded_fcs_path,
            )
            return [], None

        allowed_values = {str(option["value"]) for option in dropdown_options}

        if current_dropdown_value in allowed_values:
            resolved_dropdown_value = current_dropdown_value
        else:
            resolved_dropdown_value = None

        logger.debug(
            "Resolved target channel dropdown with %r options and value=%r from file=%r",
            len(dropdown_options),
            resolved_dropdown_value,
            first_uploaded_fcs_path,
        )

        return dropdown_options, resolved_dropdown_value