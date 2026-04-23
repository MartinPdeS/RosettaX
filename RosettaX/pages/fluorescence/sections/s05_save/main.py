# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import service, directories
from RosettaX.pages.sidebar.ids import SidebarIds
from . import services

logger = logging.getLogger(__name__)

class Save:
    """
    Save section.

    This section only handles saving the current calibration payload to disk
    and refreshing the sidebar listing.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized SaveSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        """
        Create the layout for the save section.
        """
        logger.debug("Building save section layout.")

        return dbc.Card(
            [
                dbc.CardHeader("5. Save calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            dash.html.Br(),
                            self._build_save_calibration_row(),
                            dash.html.Hr(),
                            dash.html.Div(id=self.page.ids.Save.save_out),
                        ]
                    ),
                    id=f"collapse-{self.page.ids.page_name}-save",
                    is_open=True,
                ),
            ]
        )

    def _build_save_calibration_row(self) -> dash.html.Div:
        """
        Create the save calibration row.
        """
        logger.debug("Building save calibration row.")

        return dash.html.Div(
            [
                dbc.Button(
                    "Save calibration",
                    id=self.page.ids.Save.save_calibration_btn,
                    n_clicks=0,
                    color="secondary",
                ),
                dash.dcc.Input(
                    id=self.page.ids.Save.file_name,
                    type="text",
                    value="",
                    placeholder="calibration name",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the save section.
        """
        logger.debug("Registering save section callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Save.save_out, "children"),
            dash.Output(SidebarIds.saved_calibrations_refresh_store, "data"),
            dash.Input(self.page.ids.Save.save_calibration_btn, "n_clicks"),
            dash.State(self.page.ids.Save.file_name, "value"),
            dash.State(self.page.ids.Calibration.calibration_store, "data"),
            dash.State(SidebarIds.saved_calibrations_refresh_store, "data"),
            prevent_initial_call=True,
        )
        def save_section_actions(
            n_clicks_save_calibration: int,
            file_name: str,
            calib_payload: dict | None,
            current_sidebar_refresh_signal: Any,
        ) -> tuple:
            logger.debug(
                "save_section_actions called with n_clicks_save_calibration=%r file_name=%r calib_payload_type=%s calib_payload_keys=%r current_sidebar_refresh_signal=%r",
                n_clicks_save_calibration,
                file_name,
                type(calib_payload).__name__,
                list(calib_payload.keys()) if isinstance(calib_payload, dict) else None,
                current_sidebar_refresh_signal,
            )

            del n_clicks_save_calibration

            parsed_inputs, validation_error = services.validate_save_inputs(
                file_name=file_name,
                calib_payload=calib_payload,
            )

            if validation_error is not None:
                logger.debug(
                    "save_section_actions validation failed with message=%r",
                    validation_error,
                )
                return services.SaveResult(
                    save_out=validation_error,
                    sidebar_refresh_signal=dash.no_update,
                ).to_tuple()

            try:
                result = self._action_save_calibration(
                    inputs=parsed_inputs,
                    current_sidebar_refresh_signal=current_sidebar_refresh_signal,
                )
            except Exception:
                logger.exception(
                    "Failed to save calibration with file_name=%r calib_payload_keys=%r",
                    parsed_inputs.file_name,
                    list(parsed_inputs.calib_payload.keys())
                    if isinstance(parsed_inputs.calib_payload, dict)
                    else None,
                )
                return services.SaveResult(
                    save_out="Failed to save calibration. See terminal logs for details.",
                    sidebar_refresh_signal=dash.no_update,
                ).to_tuple()

            logger.debug(
                "save_section_actions succeeded with save_out=%r sidebar_refresh_signal=%r",
                result.save_out,
                result.sidebar_refresh_signal,
            )
            return result.to_tuple()

    def _action_save_calibration(
        self,
        *,
        inputs: services.SaveInputs,
        current_sidebar_refresh_signal: Any,
    ) -> services.SaveResult:
        """
        Save the current calibration payload as a file on disk.
        """
        logger.debug(
            "_action_save_calibration called with file_name=%r payload_keys=%r",
            inputs.file_name,
            list(inputs.calib_payload.keys()) if isinstance(inputs.calib_payload, dict) else None,
        )

        saved = service.save_calibration_to_file(
            name=inputs.file_name,
            payload=dict(inputs.calib_payload or {}),
            calibration_kind="fluorescence",
            output_directory=directories.fluorescence_calibration,
        )

        logger.debug(
            "_action_save_calibration saved successfully to folder=%r filename=%r",
            saved.folder,
            saved.filename,
        )

        next_refresh_signal = services.compute_next_sidebar_refresh_signal(
            current_sidebar_refresh_signal=current_sidebar_refresh_signal,
        )

        return services.SaveResult(
            save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
            sidebar_refresh_signal=next_refresh_signal,
        )