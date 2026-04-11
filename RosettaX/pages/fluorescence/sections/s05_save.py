# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import service, directories
from RosettaX.pages.sidebar.ids import SidebarIds

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaveInputs:
    """
    Parsed and validated inputs for SaveSection actions.

    Attributes
    ----------
    file_name : str
        Name used when saving a calibration file.
    calib_payload : Optional[dict]
        Calibration payload produced by the calibration step.
    """

    file_name: str
    calib_payload: Optional[dict]

@dataclass(frozen=True)
class SaveResult:
    """
    Container for all Dash outputs of the SaveSection callback.
    """

    save_out: Any = dash.no_update
    sidebar_refresh_signal: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert this object into the tuple expected by Dash multi output callbacks.

        Returns
        -------
        tuple
            Outputs in the exact order declared in the Dash callback.
        """
        return (
            self.save_out,
            self.sidebar_refresh_signal,
        )


class SaveSection:
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

        Returns
        -------
        dbc.Card
            A Dash Bootstrap Card containing the save section layout.
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

        Returns
        -------
        dash.html.Div
            Row containing the save calibration button and calibration name input.
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
            calib_payload: Optional[dict],
            current_sidebar_refresh_signal: Any,
        ) -> tuple:
            """
            Save the current calibration payload.

            Parameters
            ----------
            n_clicks_save_calibration : int
                Click count for save calibration.
            file_name : str
                Calibration name.
            calib_payload : Optional[dict]
                Calibration payload.

            Returns
            -------
            tuple
                Dash outputs in the declared Output order.
            """
            logger.debug(
                "save_section_actions called with n_clicks_save_calibration=%r file_name=%r calib_payload_type=%s calib_payload_keys=%r",
                n_clicks_save_calibration,
                file_name,
                type(calib_payload).__name__,
                list(calib_payload.keys()) if isinstance(calib_payload, dict) else None,
            )

            parsed = self._parse_and_validate_common(
                file_name=file_name,
                calib_payload=calib_payload,
            )

            if isinstance(parsed, SaveResult):
                logger.debug(
                    "save_section_actions validation failed with message=%r",
                    parsed.save_out,
                )
                return parsed.to_tuple()

            try:
                result = self._action_save_calibration(inputs=parsed, current_sidebar_refresh_signal=current_sidebar_refresh_signal)
            except Exception:
                logger.exception(
                    "Failed to save calibration with file_name=%r calib_payload_keys=%r",
                    parsed.file_name,
                    list(parsed.calib_payload.keys()) if isinstance(parsed.calib_payload, dict) else None,
                )
                return SaveResult(
                    save_out="Failed to save calibration. See terminal logs for details.",
                    sidebar_refresh_signal=dash.no_update,
                ).to_tuple()

            logger.debug("save_section_actions succeeded with output=%r", result.save_out)
            return result.to_tuple()

    def _parse_and_validate_common(
        self,
        *,
        file_name: str,
        calib_payload: Optional[dict],
    ) -> SaveInputs | SaveResult:
        """
        Parse and validate inputs shared by save actions.

        Returns
        -------
        SaveInputs | SaveResult
            SaveInputs when validation passes, otherwise SaveResult containing an error message.
        """
        logger.debug(
            "_parse_and_validate_common called with file_name=%r calib_payload_type=%s",
            file_name,
            type(calib_payload).__name__,
        )

        if not isinstance(calib_payload, dict) or not calib_payload:
            logger.debug(
                "_parse_and_validate_common failed because calib_payload is missing or invalid: %r",
                calib_payload,
            )
            return SaveResult(save_out="No calibration payload available. Run Calibrate first.")

        file_name_clean = str(file_name or "").strip()
        logger.debug("Normalized file_name=%r to file_name_clean=%r", file_name, file_name_clean)

        if not file_name_clean:
            logger.debug("_parse_and_validate_common failed because file_name_clean is empty.")
            return SaveResult(save_out="Please provide a calibration name.")

        parsed_inputs = SaveInputs(
            file_name=file_name_clean,
            calib_payload=calib_payload,
        )
        logger.debug("Validation succeeded with parsed_inputs=%r", parsed_inputs)
        return parsed_inputs

    def _action_save_calibration(
        self,
        *,
        inputs: SaveInputs,
        current_sidebar_refresh_signal: Any,
    ) -> SaveResult:
        """
        Save the current calibration payload as a file on disk.

        Returns
        -------
        SaveResult
            User feedback message and sidebar refresh signal.
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
            output_directory=directories.fluorescence_calibration_directory,
        )

        logger.debug(
            "_action_save_calibration saved successfully to folder=%r filename=%r",
            saved.folder,
            saved.filename,
        )

        next_refresh_signal = 1 if current_sidebar_refresh_signal is None else int(current_sidebar_refresh_signal) + 1

        return SaveResult(
            save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
            sidebar_refresh_signal=next_refresh_signal,
        )