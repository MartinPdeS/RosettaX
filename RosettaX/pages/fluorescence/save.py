from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, callback_context, dcc, html

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages.fluorescence import BaseSection, SectionContext, helper


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
    locked_fluorescence_source_channel: str


class SaveSection(BaseSection):
    """
    Save + export section.

    This section:
    - Add calibrated MESF to file: writes a new temp file server side and injects the new column into the dropdown.
    - Save calibration: stores the calibration payload in the sidebar store.
    - Export file: returns bytes via dcc.Download, browser decides download directory.
    """

    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)

    def layout(self) -> dbc.Card:
        ids = self.context.ids

        return dbc.Card(
            [
                dbc.CardHeader("6. Save + export calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.Br(),
                            self._row_add_mesf(ids),
                            html.Br(),
                            self._row_save_calibration(ids),
                            html.Br(),
                            self._row_export_file(ids),
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
    def _row_add_mesf(ids) -> html.Div:
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
    def _row_save_calibration(ids) -> html.Div:
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
    def _row_export_file(ids) -> html.Div:
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

    def register_callbacks(self) -> None:
        ids = self.context.ids
        service = self.context.service

        @callback(
            Output(ids.save_out, "children"),
            Output(ids.sidebar_store, "data"),
            Output(ids.uploaded_fcs_path_store, "data", allow_duplicate=True),
            Output(ids.scattering_detector_dropdown, "options", allow_duplicate=True),
            Output(ids.fluorescence_detector_dropdown, "options", allow_duplicate=True),
            Output(ids.scattering_detector_dropdown, "value", allow_duplicate=True),
            Output(ids.fluorescence_detector_dropdown, "value", allow_duplicate=True),
            Output(ids.export_download, "data"),
            Input(ids.add_mesf_btn, "n_clicks"),
            Input(ids.save_calibration_btn, "n_clicks"),
            Input(ids.export_file_btn, "n_clicks"),
            State(ids.file_name, "value"),
            State(ids.channel_name, "value"),
            State(ids.export_filename, "value"),
            State(ids.sidebar_store, "data"),
            State(ids.calibration_store, "data"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.scattering_detector_dropdown, "options"),
            State(ids.fluorescence_detector_dropdown, "options"),
            State(ids.scattering_detector_dropdown, "value"),
            State(ids.fluorescence_detector_dropdown, "value"),
            State(ids.fluorescence_source_channel_store, "data"),
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
            locked_fluorescence_source_channel: Optional[str],
        ):
            triggered = self._triggered_id()

            parsed = self._parse_and_validate_common(
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
                locked_fluorescence_source_channel=locked_fluorescence_source_channel,
            )
            if isinstance(parsed, tuple):
                return (*parsed, dash.no_update)

            backend = BackEnd(parsed.bead_file_path)

            if triggered == ids.save_calibration_btn:
                return (*self._action_save_calibration(inputs=parsed), dash.no_update)

            if triggered == ids.add_mesf_btn:
                return (*self._action_add_mesf_to_current_file(inputs=parsed, backend=backend), dash.no_update)

            if triggered == ids.export_file_btn:
                return self._action_export_download(
                    inputs=parsed,
                    backend=backend,
                    service=service,
                )

            return self._ret_no_update()

    @staticmethod
    def _triggered_id() -> str:
        if not callback_context.triggered:
            return ""
        return str(callback_context.triggered[0]["prop_id"]).split(".")[0]

    @staticmethod
    def _ret_no_update() -> tuple:
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
    def _ret_error(message: str) -> tuple:
        return (
            message,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    def _parse_and_validate_common(
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
        locked_fluorescence_source_channel: Optional[str],
    ) -> SaveInputs | tuple:
        if not isinstance(calib_payload, dict) or not calib_payload:
            return self._ret_error("No calibration payload available. Run Calibrate first.")

        bead_file_path_clean = str(bead_file_path or "").strip()
        if not bead_file_path_clean:
            return self._ret_error("No bead file uploaded yet.")

        current_fluorescence_clean = str(current_fluorescence or "").strip()
        if not current_fluorescence_clean:
            return self._ret_error("Select a fluorescence detector first.")

        calibrated_channel_name_clean = str(calibrated_channel_name or "").strip()
        if not calibrated_channel_name_clean:
            return self._ret_error("Please provide a calibrated MESF column name.")

        locked_clean = str(locked_fluorescence_source_channel or "").strip()
        if not locked_clean:
            locked_clean = current_fluorescence_clean

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
            locked_fluorescence_source_channel=locked_clean,
        )

    @staticmethod
    def _ensure_option(options: Optional[list[dict]], *, value: str) -> list[dict]:
        safe = [dict(o) for o in (options or []) if isinstance(o, dict)]
        if any(str(o.get("value")) == value for o in safe):
            return safe
        safe.append({"label": value, "value": value})
        return safe

    def _action_save_calibration(self, *, inputs: SaveInputs) -> tuple:
        if not inputs.file_name:
            return self._ret_error("Please provide a calibration name.")

        next_sidebar = helper.CalibrationSetupStore.save_fluorescent_setup(
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

    def _action_add_mesf_to_current_file(self, *, inputs: SaveInputs, backend: BackEnd) -> tuple:
        export_response = backend.export_fluorescence_calibration(
            {
                "calibration": inputs.calib_payload,
                "source_path": inputs.bead_file_path,
                "source_column": inputs.locked_fluorescence_source_channel,
                "new_column": inputs.calibrated_channel_name,
                "mode": "update_temp",
                "export_filename": "",
            }
        )

        exported_path = str(export_response.get("exported_path") or inputs.bead_file_path)

        next_fluorescence_options = self._ensure_option(
            inputs.fluorescence_options,
            value=inputs.calibrated_channel_name,
        )

        msg = f'Added column "{inputs.calibrated_channel_name}" to current file.'
        return (
            msg,
            dash.no_update,
            exported_path,
            inputs.scatter_options or [],
            next_fluorescence_options,
            inputs.current_scatter,
            inputs.calibrated_channel_name,
        )

    def _action_export_download(self, *, inputs: SaveInputs, backend: BackEnd, service) -> tuple:
        filename = str(inputs.export_filename or "").strip()
        if not filename:
            return (*self._ret_error("Please provide an export filename."), dash.no_update)

        p = Path(filename)
        if p.suffix.lower() != ".fcs":
            filename = p.with_suffix(".fcs").name
        else:
            filename = p.name

        export_response = backend.export_fluorescence_calibration(
            {
                "calibration": inputs.calib_payload,
                "source_path": inputs.bead_file_path,
                "source_column": inputs.locked_fluorescence_source_channel,
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
            return (*self._ret_error("Export failed: no exported_bytes returned."), dash.no_update)

        next_fluorescence_options = self._ensure_option(
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