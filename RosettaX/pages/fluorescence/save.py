from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, callback_context, dcc, html

from RosettaX.reader import FCSFile
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


class SaveSection():
    """
    Save + export section.

    This section:
    - Add calibrated MESF to file: writes a new temp file server side and injects the new column into the dropdown.
    - Save calibration: stores the calibration payload in the sidebar store.
    - Export file: returns bytes via dcc.Download, browser decides download directory.
    """

    def _save_get_layout(self) -> dbc.Card:
        ids = self.ids

        return dbc.Card(
            [
                dbc.CardHeader("6. Save + export calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.Br(),
                            self._save_row_add_mesf(ids),
                            html.Br(),
                            self._save_row_save_calibration(ids),
                            html.Br(),
                            self._save_row_export_file(ids),
                            dcc.Download(id=ids.export_download),
                            html.Hr(),
                            html.Div(id=ids.save_out),
                        ]
                    ),
                    id=f"collapse-{ids.page_name}-save",
                    is_open=True,
                ),
            ]
        )

    @staticmethod
    def _save_row_add_mesf(ids) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Add calibrated MESF to file",
                    id=ids.add_mesf_btn,
                    n_clicks=0,
                    color="primary",
                ),
                dcc.Input(
                    id=ids.channel_name,
                    type="text",
                    value="MESF",
                    placeholder="column name",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    @staticmethod
    def _save_row_save_calibration(ids) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Save calibration",
                    id=ids.save_calibration_btn,
                    n_clicks=0,
                    color="secondary",
                ),
                dcc.Input(
                    id=ids.file_name,
                    type="text",
                    value="",
                    placeholder="calibration name",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    @staticmethod
    def _save_row_export_file(ids) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Export file",
                    id=ids.export_file_btn,
                    n_clicks=0,
                    color="success",
                ),
                dcc.Input(
                    id=ids.export_filename,
                    type="text",
                    value="beads_calibrated.fcs",
                    placeholder="output filename",
                    style={"width": "280px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _save_register_callbacks(self) -> None:
        @callback(
            Output(self.ids.scattering_detector_dropdown, "options", allow_duplicate=True),
            Output(self.ids.fluorescence_detector_dropdown, "options", allow_duplicate=True),
            Input(self.ids.uploaded_fcs_path_store, "data"),
            prevent_initial_call=True,
        )
        def refresh_detector_options(fcs_path: Optional[str]):
            if not fcs_path:
                return dash.no_update, dash.no_update

            backend = BackEnd(str(fcs_path))
            names = backend.get_column_names()
            opts = [{"label": n, "value": n} for n in names]
            return opts, opts

        @callback(
            Output(self.ids.save_out, "children"),
            Output(self.ids.sidebar_store, "data"),
            Output(self.ids.uploaded_fcs_path_store, "data", allow_duplicate=True),
            Output(self.ids.scattering_detector_dropdown, "options", allow_duplicate=True),
            Output(self.ids.fluorescence_detector_dropdown, "options", allow_duplicate=True),
            Output(self.ids.scattering_detector_dropdown, "value", allow_duplicate=True),
            Output(self.ids.fluorescence_detector_dropdown, "value", allow_duplicate=True),
            Output(self.ids.export_download, "data"),
            Input(self.ids.add_mesf_btn, "n_clicks"),
            Input(self.ids.save_calibration_btn, "n_clicks"),
            Input(self.ids.export_file_btn, "n_clicks"),
            State(self.ids.file_name, "value"),
            State(self.ids.channel_name, "value"),
            State(self.ids.export_filename, "value"),
            State(self.ids.sidebar_store, "data"),
            State(self.ids.calibration_store, "data"),
            State(self.ids.uploaded_fcs_path_store, "data"),
            State(self.ids.scattering_detector_dropdown, "options"),
            State(self.ids.fluorescence_detector_dropdown, "options"),
            State(self.ids.scattering_detector_dropdown, "value"),
            State(self.ids.fluorescence_detector_dropdown, "value"),
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
            if isinstance(parsed, tuple):
                return (*parsed, dash.no_update)

            backend = BackEnd(parsed.bead_file_path)

            if triggered == self.ids.save_calibration_btn:
                return (*self._save_action_save_calibration(inputs=parsed), dash.no_update)

            if triggered == self.ids.add_mesf_btn:
                return (*self._save_action_add_mesf_to_current_file(inputs=parsed, backend=backend), dash.no_update)

            if triggered == self.ids.export_file_btn:
                return self._save_action_export_download(inputs=parsed, backend=backend)

            return self._save_ret_no_update()

    @staticmethod
    def _save_triggered_id() -> str:
        if not callback_context.triggered:
            return ""
        return str(callback_context.triggered[0]["prop_id"]).split(".")[0]

    @staticmethod
    def _save_ret_no_update() -> tuple:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    @staticmethod
    def _save_ret_error(message: str) -> tuple:
        return (
            message,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

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
    ) -> SaveInputs | tuple:
        if not isinstance(calib_payload, dict) or not calib_payload:
            return self._save_ret_error("No calibration payload available. Run Calibrate first.")

        bead_file_path_clean = str(bead_file_path or "").strip()
        if not bead_file_path_clean:
            return self._save_ret_error("No bead file uploaded yet.")

        current_fluorescence_clean = str(current_fluorescence or "").strip()
        if not current_fluorescence_clean:
            return self._save_ret_error("Select a fluorescence detector first.")

        calibrated_channel_name_clean = str(calibrated_channel_name or "").strip()
        if not calibrated_channel_name_clean:
            return self._save_ret_error("Please provide a calibrated MESF column name.")

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

    def _save_action_save_calibration(self, *, inputs: SaveInputs) -> tuple:
        if not inputs.file_name:
            return self._save_ret_error("Please provide a calibration name.")

        next_sidebar = service.CalibrationSetupStore.save_fluorescent_setup(
            inputs.sidebar_data,
            name=inputs.file_name,
            payload=inputs.calib_payload,
        )

        msg = f'Calibration "{inputs.file_name}" saved.'
        return (
            msg,
            next_sidebar,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    def _save_action_add_mesf_to_current_file(self, *, inputs: SaveInputs, backend: BackEnd) -> tuple:
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

        msg = f'Added column "{inputs.calibrated_channel_name}" to current file.'
        return (
            msg,
            dash.no_update,
            exported_path,                      # store updated
            inputs.scatter_options or [],
            next_fluorescence_options,          # options updated
            inputs.current_scatter,
            dash.no_update,                     # <-- do NOT set value to MESF here
        )

    def _save_action_export_download(self, *, inputs: SaveInputs, backend: BackEnd) -> tuple:
        filename = str(inputs.export_filename or "").strip()
        if not filename:
            return (*self._save_ret_error("Please provide an export filename."), dash.no_update)

        p = Path(filename)
        if p.suffix.lower() != ".fcs":
            filename = p.with_suffix(".fcs").name
        else:
            filename = p.name

        export_response = backend.export_fluorescence_calibration(
            {
                "calibration": inputs.calib_payload,
                "source_path": inputs.bead_file_path,
                "source_column": inputs.current_fluorescence,
                "new_column": inputs.calibrated_channel_name,
                "mode": "save_new",
                "export_filename": filename,
            }
        )

        blob = export_response.get("exported_bytes")
        base = Path(export_response.get("export_name") or filename)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"{base.stem}_{stamp}{base.suffix}"

        if not isinstance(blob, (bytes, bytearray)) or not blob:
            return (*self._save_ret_error("Export failed: no exported_bytes returned."), dash.no_update)

        next_fluorescence_options = self._save_ensure_option(
            inputs.fluorescence_options,
            value=inputs.calibrated_channel_name,
        )

        msg = f"Export ready: {export_name}"

        return (
            msg,
            dash.no_update,
            dash.no_update,
            inputs.scatter_options or [],
            next_fluorescence_options,
            inputs.current_scatter,
            inputs.calibrated_channel_name,
            dcc.send_bytes(bytes(blob), filename=export_name),
        )