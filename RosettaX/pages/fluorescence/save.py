from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages.fluorescence import service


@dataclass(frozen=True)
class SaveInputs:
    file_name: str
    calibrated_channel_name: str
    export_filename: str
    sidebar_data: Optional[dict]
    calib_payload: Optional[dict]
    bead_file_path: str
    current_scatter: Optional[str]
    current_fluorescence: str
    scatter_options: Optional[list[dict]]
    fluorescence_options: Optional[list[dict]]


@dataclass(frozen=True)
class SaveResult:
    save_out: Any = dash.no_update
    sidebar_store: Any = dash.no_update
    uploaded_fcs_path_store: Any = dash.no_update
    scatter_options: Any = dash.no_update
    fluorescence_options: Any = dash.no_update
    scatter_value: Any = dash.no_update
    fluorescence_value: Any = dash.no_update
    export_download: Any = dash.no_update


    def to_tuple(self) -> tuple:
        return (
            self.save_out,
            self.sidebar_store,
            self.uploaded_fcs_path_store,
            self.scatter_options,
            self.fluorescence_options,
            self.scatter_value,
            self.fluorescence_value,
            self.export_download,
        )


class SaveSection():
    """
    Save + export section.

    This section:
    - Add calibrated MESF to file: writes a new temp file server side and injects the new column into the dropdown.
    - Save calibration: stores the calibration payload in the sidebar store.
    - Export file: returns bytes via dash.dcc.Download, browser decides download directory.
    """

    def _save_get_layout(self) -> dbc.Card:
        """
        Creates the layout for the save + export section.

        Returns
        -------
        dbc.Card
            A Dash Bootstrap Card containing the save + export section layout.
        """
        return dbc.Card(
            [
                dbc.CardHeader("6. Save + export calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            dash.html.Br(),
                            self._save_row_add_mesf(),
                            dash.html.Br(),
                            self._save_row_save_calibration(),
                            dash.html.Br(),
                            self._save_row_export_file(),
                            dash.dcc.Download(id=self.ids.Save.export_download),
                            dash.html.Hr(),
                            dash.html.Div(id=self.ids.Save.save_out),
                        ]
                    ),
                    id=f"collapse-{self.ids.page_name}-save",
                    is_open=True,
                ),
            ]
        )

    def _save_row_add_mesf(self) -> dash.html.Div:
        """
        Creates the layout for the add MESF row.

        Returns
        -------
        dash.html.Div
            A Dash HTML Div containing the add MESF button and channel name input, styled to be on the same row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Add calibrated MESF to file",
                    id=self.ids.Save.add_mesf_btn,
                    n_clicks=0,
                    color="primary",
                ),
                dash.dcc.Input(
                    id=self.ids.Save.channel_name,
                    type="text",
                    value="MESF",
                    placeholder="column name",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _save_row_save_calibration(self) -> dash.html.Div:
        """
        Creates the layout for the save calibration row.

        Returns
        -------
        dash.html.Div
            A Dash HTML Div containing the save calibration button and filename input, styled to be on the same row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Save calibration",
                    id=self.ids.Save.save_calibration_btn,
                    n_clicks=0,
                    color="secondary",
                ),
                dash.dcc.Input(
                    id=self.ids.Save.file_name,
                    type="text",
                    value="",
                    placeholder="calibration name",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _save_row_export_file(self) -> dash.html.Div:
        """
        Creates the layout for the export file row.

        Returns
        -------
        dash.html.Div
            A Dash HTML Div containing the export file button and filename input, styled to be on the
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Export file",
                    id=self.ids.Save.export_file_btn,
                    n_clicks=0,
                    color="success",
                ),
                dash.dcc.Input(
                    id=self.ids.Save.export_filename,
                    type="text",
                    value="beads_calibrated.fcs",
                    placeholder="output filename",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _save_register_callbacks(self) -> None:
        """
        Registers the callbacks for the save + export section. This includes handling the actions for adding MESF to the current file, saving the calibration, and exporting the file.

        Returns
        -------
        None
        """
        @dash.callback(
            dash.Output(self.ids.Scattering.detector_dropdown, "options", allow_duplicate=True),
            dash.Output(self.ids.Fluorescence.detector_dropdown, "options", allow_duplicate=True),
            dash.Input(self.ids.Load.uploaded_fcs_path_store, "data"),
            prevent_initial_call=True,
        )
        def refresh_detector_options(fcs_path: Optional[str]):
            if not fcs_path:
                return dash.no_update, dash.no_update

            backend = BackEnd(str(fcs_path))
            names = backend.get_column_names()
            opts = [{"label": n, "value": n} for n in names]
            return opts, opts

        @dash.callback(
            dash.Output(self.ids.Save.save_out, "children"),
            dash.Output(self.ids.Sidebar.sidebar_store, "data"),
            dash.Output(self.ids.Load.uploaded_fcs_path_store, "data", allow_duplicate=True),
            dash.Output(self.ids.Scattering.detector_dropdown, "options", allow_duplicate=True),
            dash.Output(self.ids.Fluorescence.detector_dropdown, "options", allow_duplicate=True),
            dash.Output(self.ids.Scattering.detector_dropdown, "value", allow_duplicate=True),
            dash.Output(self.ids.Fluorescence.detector_dropdown, "value", allow_duplicate=True),
            dash.Output(self.ids.Save.export_download, "data"),
            dash.Input(self.ids.Save.add_mesf_btn, "n_clicks"),
            dash.Input(self.ids.Save.save_calibration_btn, "n_clicks"),
            dash.Input(self.ids.Save.export_file_btn, "n_clicks"),
            dash.State(self.ids.Save.file_name, "value"),
            dash.State(self.ids.Save.channel_name, "value"),
            dash.State(self.ids.Save.export_filename, "value"),
            dash.State(self.ids.Sidebar.sidebar_store, "data"),
            dash.State(self.ids.Calibration.calibration_store, "data"),
            dash.State(self.ids.Load.uploaded_fcs_path_store, "data"),
            dash.State(self.ids.Scattering.detector_dropdown, "options"),
            dash.State(self.ids.Fluorescence.detector_dropdown, "options"),
            dash.State(self.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def save_section_actions(
            n_clicks_add_mesf: int,
            n_clicks_save_calibration: int,
            n_clicks_export_file: int,
            file_name: str,
            calibrated_channel_name: str,
            export_filename: str,
            sidebar_data: Optional[dict],
            calib_payload: Optional[dict],
            bead_file_path: Optional[str],
            scatter_options: Optional[list[dict]],
            fluorescence_options: Optional[list[dict]],
            current_scatter: Optional[str],
            current_fluorescence: Optional[str],
        ):
            triggered = self._save_triggered_id()

            parsed = self._save_parse_and_validate_common(
                file_name=file_name,
                calibrated_channel_name=calibrated_channel_name,
                export_filename=export_filename,
                sidebar_data=sidebar_data,
                calib_payload=calib_payload,
                bead_file_path=bead_file_path,
                current_scatter=current_scatter,
                current_fluorescence=current_fluorescence,
                scatter_options=scatter_options,
                fluorescence_options=fluorescence_options,
            )
            if isinstance(parsed, SaveResult):
                return parsed.to_tuple()

            backend = BackEnd(parsed.bead_file_path)

            if triggered == self.ids.Save.save_calibration_btn:
                return self._save_action_save_calibration(inputs=parsed).to_tuple()

            if triggered == self.ids.Save.add_mesf_btn:
                return self._save_action_add_mesf_to_current_file(inputs=parsed, backend=backend).to_tuple()

            if triggered == self.ids.Save.export_file_btn:
                return self._save_action_export_download(inputs=parsed, backend=backend).to_tuple()

            return SaveResult().to_tuple()

    @staticmethod
    def _save_triggered_id() -> str:
        """
        Utility function to get the ID of the triggered input in a Dash callback.

        Returns
        -------
        str
            The ID of the triggered input, or an empty string if no input was triggered.
        """
        if not dash.callback_context.triggered:
            return ""
        return str(dash.callback_context.triggered[0]["prop_id"]).split(".")[0]

    def _save_parse_and_validate_common(
        self,
        *,
        file_name: str,
        calibrated_channel_name: str,
        export_filename: str,
        sidebar_data: Optional[dict],
        calib_payload: Optional[dict],
        bead_file_path: Optional[str],
        current_scatter: Optional[str],
        current_fluorescence: Optional[str],
        scatter_options: Optional[list[dict]],
        fluorescence_options: Optional[list[dict]],
    ) -> SaveInputs | SaveResult:
        """
        Parses and validates the common inputs for the save section actions. This includes checking that required fields are provided and returning a SaveInputs dataclass if validation passes, or an error message tuple if validation fails.

        Parameters
        ----------
        file_name : str
            The name of the calibration to save.
        calibrated_channel_name : str
            The name of the calibrated channel/column.
        export_filename : str
            The desired filename for export.
        sidebar_data : Optional[dict]
            The current data in the sidebar store, used for saving calibration setups.
        calib_payload : Optional[dict]
            The current calibration payload, required for saving and exporting.
        bead_file_path : Optional[str]
            The file path of the uploaded bead file, required for adding MESF to current file and exporting.
        current_scatter : Optional[str]
            The currently selected scatter channel, used for re-populating dropdown after adding MESF.
        current_fluorescence : Optional[str]
            The currently selected fluorescence channel, required for adding MESF to current file and exporting.
        scatter_options : Optional[list[dict]]
            The current options for the scatter dropdown, used for re-populating dropdown after adding MESF.
        fluorescence_options : Optional[list[dict]]
            The current options for the fluorescence dropdown, used for re-populating dropdown after adding MESF and ensuring the new calibrated channel is included.

        Returns
        -------
        SaveInputs | tuple
            A SaveInputs dataclass containing the parsed and validated inputs if validation passes, or a tuple with an error message and dash.no_update for other outputs if validation fails.
        """
        if not isinstance(calib_payload, dict) or not calib_payload:
            return SaveResult(save_out="No calibration payload available. Run Calibrate first.")

        bead_file_path_clean = str(bead_file_path or "").strip()
        if not bead_file_path_clean:
            return SaveResult(save_out="No bead file uploaded yet.")

        current_fluorescence_clean = str(current_fluorescence or "").strip()
        if not current_fluorescence_clean:
            return SaveResult(save_out="Select a fluorescence detector first.")

        calibrated_channel_name_clean = str(calibrated_channel_name or "").strip()
        if not calibrated_channel_name_clean:
            return SaveResult(save_out="Please provide a calibrated MESF column name.")

        return SaveInputs(
            file_name=str(file_name or "").strip(),
            calibrated_channel_name=calibrated_channel_name_clean,
            export_filename=str(export_filename or "").strip(),
            sidebar_data=sidebar_data,
            calib_payload=calib_payload,
            bead_file_path=bead_file_path_clean,
            current_scatter=str(current_scatter).strip() if current_scatter is not None else None,
            current_fluorescence=current_fluorescence_clean,
            scatter_options=scatter_options,
            fluorescence_options=fluorescence_options,
        )

    @staticmethod
    def _save_ensure_option(options: Optional[list[dict]], *, value: str) -> list[dict]:
        safe = [dict(o) for o in (options or []) if isinstance(o, dict)]
        if any(str(o.get("value")) == value for o in safe):
            return safe
        safe.append({"label": value, "value": value})
        return safe

    def _save_action_save_calibration(self, *, inputs: SaveInputs) -> SaveResult:
        """"
        Saves the current calibration setup.

        Returns
        -------
        SaveResult
            A SaveResult object containing the user feedback message, updated sidebar store, and placeholders for other Dash components.
        """
        if not inputs.file_name:
            return SaveResult(save_out="Please provide a calibration name.")

        next_sidebar = service.CalibrationSetupStore.save_fluorescent_setup(
            inputs.sidebar_data,
            name=inputs.file_name,
            payload=inputs.calib_payload,
        )

        return SaveResult(
            save_out=f'Calibration "{inputs.file_name}" saved.',
            sidebar_store=next_sidebar,
        )

    def _save_action_add_mesf_to_current_file(self, *, inputs: SaveInputs, backend: BackEnd) -> SaveResult:
        """
        Adds a new column to the current file with the calibrated MESF values. This is done by writing a new temp file server side and updating the fluorescence dropdown options to include the new column.

        Returns
        -------
        SaveResult
            A SaveResult object containing the user feedback message, updated sidebar store, updated file path, updated scatter options, updated fluorescence options, current scatter value, and current fluorescence value.

        """
        export_response = backend.export_fluorescence_calibration(
            {
                "calibration": inputs.calib_payload,
                "source_path": inputs.bead_file_path,
                "source_column": inputs.current_fluorescence,
                "new_column": inputs.calibrated_channel_name,
                "mode": "update_temp",
                "export_filename": "",
            }
        )

        exported_path = str(export_response.get("exported_path") or inputs.bead_file_path)

        next_fluorescence_options = self._save_ensure_option(
            inputs.fluorescence_options,
            value=inputs.calibrated_channel_name,
        )

        return SaveResult(
            save_out=f'Added column "{inputs.calibrated_channel_name}" to current file.',
            uploaded_fcs_path_store=exported_path,
            scatter_options=inputs.scatter_options or [],
            fluorescence_options=next_fluorescence_options,
            scatter_value=inputs.current_scatter,
            fluorescence_value=dash.no_update,
        )

    def _save_action_export_download(self, *, inputs: SaveInputs, backend: BackEnd) -> SaveResult:
        """
        Saves a new file with the calibrated MESF values and returns a download link. This is done by writing a new file server side and sending the bytes to the client for download.

        Parameters
        ----------
        inputs : SaveInputs
            The parsed and validated inputs required for exporting the file, including calibration payload, file paths, and current dropdown options.
        backend : BackEnd
            The backend instance used to perform the export operation.

        Returns
        -------
        SaveResult
            A SaveResult object containing the user feedback message, placeholders for updated sidebar store and file path, updated scatter options, updated fluorescence options, current scatter value, current fluorescence value, and the data for dash
        """
        filename = str(inputs.export_filename or "").strip()
        if not filename:
            return SaveResult(save_out="Please provide an export filename.")

        p = Path(filename)
        if p.suffix.lower() != ".fcs":
            filename = p.with_suffix(".fcs").name
        else:
            filename = p.name

        kwargs = {
            "calibration": inputs.calib_payload,
            "source_path": inputs.bead_file_path,
            "source_column": inputs.current_fluorescence,
            "new_column": inputs.calibrated_channel_name,
            "mode": "export",
            "export_filename": filename,
        }

        export_response = backend.export_fluorescence_calibration(kwargs)

        blob = export_response.get("exported_bytes")
        base = Path(export_response.get("export_name") or filename)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"{base.stem}_{stamp}{base.suffix}"

        if not isinstance(blob, (bytes, bytearray)) or not blob:
            return SaveResult(save_out="Export failed: no exported_bytes returned.")

        next_fluorescence_options = self._save_ensure_option(
            inputs.fluorescence_options,
            value=inputs.calibrated_channel_name,
        )

        return SaveResult(
            save_out=f"Export ready: {export_name}",
            scatter_options=inputs.scatter_options or [],
            fluorescence_options=next_fluorescence_options,
            scatter_value=inputs.current_scatter,
            fluorescence_value=inputs.calibrated_channel_name,
            export_download=dash.dcc.send_bytes(bytes(blob), filename=export_name),
        )
