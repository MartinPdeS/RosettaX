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


@dataclass(frozen=True)
class SaveResult:
    """
    Container for all Dash outputs of the Save callback.
    """

    save_out: Any = dash.no_update
    sidebar_refresh_store: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.save_out,
            self.sidebar_refresh_store,
        )


class Save:
    """
    Save section.

    Responsibilities
    ----------------
    - Save the current scattering calibration payload to disk.
    - Trigger a refresh of the sidebar saved calibrations listing.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Save section with page=%r", page)

    def get_layout(self) -> dbc.Card:
        """
        Create the layout for the save section.
        """
        logger.debug("Building Save section layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        logger.debug("Building Save section header.")
        return dbc.CardHeader("5. Save calibration")

    def _build_collapse(self) -> dbc.Collapse:
        logger.debug("Building Save section collapse.")
        return dbc.Collapse(
            self._build_body(),
            id=f"collapse-{self.page.ids.page_name}-save",
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        logger.debug("Building Save section body.")
        return dbc.CardBody(
            [
                dash.html.Br(),
                self._build_save_calibration_row(),
                dash.html.Hr(),
                self._build_status_output(),
            ]
        )

    def _build_status_output(self) -> dash.html.Div:
        logger.debug("Building Save section status output.")
        return dash.html.Div(id=self.page.ids.Save.save_out)

    def _build_save_calibration_row(self) -> dash.html.Div:
        """
        Build the save calibration row.
        """
        logger.debug("Building Save section calibration row.")

        return dash.html.Div(
            [
                self._build_save_calibration_button(),
                self._build_file_name_input(),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _build_save_calibration_button(self) -> dbc.Button:
        logger.debug("Building Save section save button.")
        return dbc.Button(
            "Save calibration",
            id=self.page.ids.Save.save_calibration_btn,
            n_clicks=0,
            color="secondary",
        )

    def _build_file_name_input(self) -> dash.dcc.Input:
        logger.debug("Building Save section file name input.")
        return dash.dcc.Input(
            id=self.page.ids.Save.file_name,
            type="text",
            value="",
            placeholder="calibration name",
            style={"width": "280px"},
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the save section.
        """
        logger.debug("Registering Save section callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Save.save_out, "children"),
            dash.Output(SidebarIds.saved_calibrations_refresh_store, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Save.save_calibration_btn, "n_clicks"),
            dash.State(self.page.ids.Save.file_name, "value"),
            dash.State(self.page.ids.Calibration.calibration_store, "data"),
            prevent_initial_call=True,
        )
        def save_section_actions(
            n_clicks_save_calibration: int,
            file_name: str,
            calib_payload: dict | None,
        ) -> tuple:
            logger.debug(
                "save_section_actions called with n_clicks_save_calibration=%r file_name=%r calib_payload_type=%s calib_payload_keys=%r",
                n_clicks_save_calibration,
                file_name,
                type(calib_payload).__name__,
                list(calib_payload.keys()) if isinstance(calib_payload, dict) else None,
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
                return SaveResult(
                    save_out=validation_error,
                    sidebar_refresh_store=dash.no_update,
                ).to_tuple()

            try:
                result = self._action_save_calibration(inputs=parsed_inputs)
            except Exception:
                logger.exception(
                    "save_section_actions failed while saving calibration with file_name=%r calib_payload_keys=%r",
                    parsed_inputs.file_name,
                    list(parsed_inputs.calib_payload.keys())
                    if isinstance(parsed_inputs.calib_payload, dict)
                    else None,
                )
                return SaveResult(
                    save_out="Failed to save calibration. See terminal logs for details.",
                    sidebar_refresh_store=dash.no_update,
                ).to_tuple()

            logger.debug(
                "save_section_actions succeeded with save_out=%r sidebar_refresh_store=%r",
                result.save_out,
                result.sidebar_refresh_store,
            )
            return result.to_tuple()

    def _action_save_calibration(self, *, inputs: services.SaveInputs) -> SaveResult:
        """
        Save the current calibration payload to disk.
        """
        logger.debug(
            "_action_save_calibration called with file_name=%r payload_keys=%r",
            inputs.file_name,
            list(inputs.calib_payload.keys()) if isinstance(inputs.calib_payload, dict) else None,
        )

        try:
            saved = service.save_calibration_to_file(
                name=inputs.file_name,
                payload=dict(inputs.calib_payload or {}),
                calibration_kind="scattering",
                output_directory=directories.scattering_calibration,
            )
        except Exception:
            logger.exception(
                "_action_save_calibration failed for file_name=%r payload_keys=%r",
                inputs.file_name,
                list(inputs.calib_payload.keys()) if isinstance(inputs.calib_payload, dict) else None,
            )
            raise

        logger.debug(
            "Calibration saved successfully to folder=%r filename=%r",
            saved.folder,
            saved.filename,
        )

        sidebar_refresh_payload = services.build_sidebar_refresh_payload(
            saved_folder=saved.folder,
            saved_filename=saved.filename,
        )

        return SaveResult(
            save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
            sidebar_refresh_store=sidebar_refresh_payload,
        )