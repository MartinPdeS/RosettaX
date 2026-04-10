# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.fluorescence import service


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
    sidebar_store: Any = dash.no_update

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
            self.sidebar_store,
        )


class SaveSection:
    """
    Save section.

    This section only handles saving the current calibration payload to disk
    and refreshing the sidebar listing.
    """

    def __init__(self, page) -> None:
        self.page = page

    def _get_layout(self) -> dbc.Card:
        """
        Create the layout for the save section.

        Returns
        -------
        dbc.Card
            A Dash Bootstrap Card containing the save section layout.
        """
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

    def _register_callbacks(self) -> None:
        """
        Register callbacks for the save section.
        """

        @dash.callback(
            dash.Output(self.page.ids.Save.save_out, "children"),
            dash.Output(self.page.ids.Sidebar.sidebar_store, "data"),
            dash.Input(self.page.ids.Save.save_calibration_btn, "n_clicks"),
            dash.State(self.page.ids.Save.file_name, "value"),
            dash.State(self.page.ids.Calibration.calibration_store, "data"),
            prevent_initial_call=True,
        )
        def save_section_actions(
            n_clicks_save_calibration: int,
            file_name: str,
            calib_payload: Optional[dict],
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
            parsed = self._parse_and_validate_common(
                file_name=file_name,
                calib_payload=calib_payload,
            )
            if isinstance(parsed, SaveResult):
                return parsed.to_tuple()

            return self._action_save_calibration(inputs=parsed).to_tuple()

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
        if not isinstance(calib_payload, dict) or not calib_payload:
            return SaveResult(save_out="No calibration payload available. Run Calibrate first.")

        file_name_clean = str(file_name or "").strip()
        if not file_name_clean:
            return SaveResult(save_out="Please provide a calibration name.")

        return SaveInputs(
            file_name=file_name_clean,
            calib_payload=calib_payload,
        )

    def _action_save_calibration(self, *, inputs: SaveInputs) -> SaveResult:
        """
        Save the current calibration payload as a file on disk.

        Returns
        -------
        SaveResult
            Updated sidebar store and a user feedback message.
        """
        saved = service.CalibrationFileStore.save_fluorescent_setup_to_file(
            name=inputs.file_name,
            payload=dict(inputs.calib_payload or {}),
        )

        next_sidebar = service.CalibrationFileStore.list_saved_calibrations()

        return SaveResult(
            save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
            sidebar_store=next_sidebar,
        )