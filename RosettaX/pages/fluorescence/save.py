# -*- coding: utf-8 -*-

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages.fluorescence import service


@dataclass(frozen=True)
class SaveInputs:
    """
    Parsed and validated inputs for SaveSection actions.

    Attributes
    ----------
    file_name : str
        Name used when saving a calibration file.
    calibrated_channel_name : str
        Name of the calibrated output column to add into the current file.
    export_filename : str
        Desired export filename for download.
    sidebar_data : Optional[dict]
        Current sidebar store content. May be ignored if sidebar is rebuilt from disk.
    calib_payload : Optional[dict]
        Calibration payload produced by the calibration step.
    bead_file_path : str
        Path to the currently loaded bead file on disk.
    current_scatter : Optional[str]
        Currently selected scatter detector.
    current_fluorescence : str
        Currently selected fluorescence detector.
    scatter_options : Optional[list[dict]]
        Current scatter dropdown options.
    fluorescence_options : Optional[list[dict]]
        Current fluorescence dropdown options.
    """

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
    """
    Container for all Dash outputs of the SaveSection callback.

    This keeps the callback code readable by returning a single object that
    maps to the Dash Outputs order via to_tuple().
    """

    save_out: Any = dash.no_update
    sidebar_store: Any = dash.no_update
    uploaded_fcs_path_store: Any = dash.no_update
    scatter_options: Any = dash.no_update
    fluorescence_options: Any = dash.no_update
    scatter_value: Any = dash.no_update
    fluorescence_value: Any = dash.no_update
    export_download: Any = dash.no_update

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
            self.uploaded_fcs_path_store,
            self.scatter_options,
            self.fluorescence_options,
            self.scatter_value,
            self.fluorescence_value,
            self.export_download,
        )


class SaveSection:
    """
    Save and export section.

    This section handles:
    - Add calibrated channel to the current file: writes a temp file server side and updates dropdowns.
    - Save calibration: writes a small JSON file to disk and refreshes the sidebar store listing.
    - Export file: returns bytes via dash.dcc.Download (browser decides download directory).
    """

    def _save_get_layout(self) -> dbc.Card:
        """
        Create the layout for the save and export section.

        Returns
        -------
        dbc.Card
            A Dash Bootstrap Card containing the save and export section layout.
        """
        return dbc.Card(
            [
                dbc.CardHeader("6. Save and export calibration"),
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
        Create the add calibrated column row.

        Returns
        -------
        dash.html.Div
            Row containing the add calibrated column button and column name input.
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
        Create the export file row.

        Returns
        -------
        dash.html.Div
            Row containing the export button and output filename input.
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
        Register callbacks for the save and export section.

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
            """
            Refresh detector dropdown options when a new file is set.

            Parameters
            ----------
            fcs_path : Optional[str]
                Current path from uploaded file store.

            Returns
            -------
            tuple
                (scatter_options, fluorescence_options)
            """
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
            """
            Main SaveSection callback dispatcher.

            Parameters
            ----------
            n_clicks_add_mesf : int
                Click count for add calibrated column.
            n_clicks_save_calibration : int
                Click count for save calibration.
            n_clicks_export_file : int
                Click count for export file.
            file_name : str
                Calibration name.
            calibrated_channel_name : str
                New column name for calibrated values.
            export_filename : str
                Output filename for download.
            sidebar_data : Optional[dict]
                Sidebar store data.
            calib_payload : Optional[dict]
                Calibration payload.
            bead_file_path : Optional[str]
                Current FCS path from store.
            scatter_options : Optional[list[dict]]
                Scatter dropdown options.
            fluorescence_options : Optional[list[dict]]
                Fluorescence dropdown options.
            current_scatter : Optional[str]
                Current selected scatter channel.
            current_fluorescence : Optional[str]
                Current selected fluorescence channel.

            Returns
            -------
            tuple
                Dash outputs in the declared Output order.
            """
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
        Get the ID of the triggered input in a Dash callback.

        Returns
        -------
        str
            Triggered component ID or empty string if none.
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
        Parse and validate inputs shared by all actions.

        Returns
        -------
        SaveInputs | SaveResult
            SaveInputs when validation passes, otherwise SaveResult containing an error message.
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
        """
        Ensure an option exists in a dropdown option list.

        Parameters
        ----------
        options : Optional[list[dict]]
            Existing options.
        value : str
            Value to ensure.

        Returns
        -------
        list[dict]
            Updated options list containing value.
        """
        safe = [dict(o) for o in (options or []) if isinstance(o, dict)]
        if any(str(o.get("value")) == value for o in safe):
            return safe
        safe.append({"label": value, "value": value})
        return safe

    def _save_action_save_calibration(self, *, inputs: SaveInputs) -> SaveResult:
        """
        Save the current calibration payload as a file on disk.

        This uses service.CalibrationFileStore, which should write a simple JSON file and provide
        a listing suitable for the sidebar.

        Returns
        -------
        SaveResult
            Updated sidebar store and a user feedback message.
        """
        if not inputs.file_name:
            return SaveResult(save_out="Please provide a calibration name.")

        saved = service.CalibrationFileStore.save_fluorescent_setup_to_file(
            name=inputs.file_name,
            payload=dict(inputs.calib_payload or {}),
        )

        next_sidebar = service.CalibrationFileStore.list_saved_calibrations()

        return SaveResult(
            save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
            sidebar_store=next_sidebar,
        )

    def _save_action_add_mesf_to_current_file(self, *, inputs: SaveInputs, backend: BackEnd) -> SaveResult:
        """
        Add a new column with calibrated values to the current file.

        This writes a new temp file server side and updates the file path store
        so downstream steps operate on the updated file.

        Returns
        -------
        SaveResult
            Updated file path store and updated dropdown options.
        """
        kwargs = {
            "calibration": inputs.calib_payload,
            "source_path": inputs.bead_file_path,
            "source_column": inputs.current_fluorescence,
            "new_column": inputs.calibrated_channel_name,
            "mode": "update_temp",
            "export_filename": "",
        }

        export_response = backend.export_fluorescence_calibration(kwargs)
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
        Export a new file with the calibrated values and return a download response.

        Returns
        -------
        SaveResult
            Contains dash.dcc.send_bytes data for the download component.
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
            "mode": "save_new",
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