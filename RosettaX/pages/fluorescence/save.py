from typing import Optional

import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc

from RosettaX.backend import BackEnd
from RosettaX.pages.fluorescence import BaseSection, SectionContext, helper


class SaveSection(BaseSection):
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
                            html.Label("Calibrated MESF Channel Name (new column):"),
                            dcc.Input(id=ids.channel_name, type="text", value="MESF"),
                            html.Br(),
                            html.Br(),
                            html.Label("Save Calibration Setup As:"),
                            dcc.Input(id=ids.file_name, type="text", value=""),
                            html.Br(),
                            html.Br(),
                            html.Label("Data export mode:"),
                            dcc.RadioItems(
                                id=ids.export_mode,
                                options=[
                                    {"label": "Update current file", "value": "update_temp"},
                                    {"label": "Save as new file", "value": "save_new"},
                                ],
                                value="update_temp",
                                inline=False,
                            ),
                            html.Br(),
                            html.Label("Output file name (only used for Save as new file):"),
                            dcc.Input(id=ids.export_filename, type="text", value="beads_calibrated.fcs"),
                            html.Br(),
                            html.Br(),
                            html.Button("Save calibration + export", id=ids.save_btn, n_clicks=0),
                            html.Div(id=ids.save_out),
                        ]
                    ),
                    id=f"collapse-{ids.page_name}-save",
                    is_open=True,
                ),
            ]
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
            Input(ids.save_btn, "n_clicks"),
            State(ids.file_name, "value"),
            State(ids.channel_name, "value"),
            State(ids.export_mode, "value"),
            State(ids.export_filename, "value"),
            State(ids.sidebar_store, "data"),
            State(ids.calibration_store, "data"),
            State(ids.uploaded_fcs_path_store, "data"),
            State(ids.scattering_detector_dropdown, "value"),
            State(ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def save_calibration(
            n_clicks: int,
            file_name: str,
            calibrated_channel_name: str,
            export_mode: str,
            export_filename: str,
            sidebar_data: Optional[dict],
            calib_payload: Optional[dict],
            bead_file_path: Optional[str],
            current_scatter: Optional[str],
            current_fluorescence: Optional[str],
        ):
            if not n_clicks:
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            name = str(file_name or "").strip()
            if not name:
                return (
                    "Please provide a calibration setup name.",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            if not isinstance(calib_payload, dict) or not calib_payload:
                return (
                    "No calibration payload to save. Run Calibrate first.",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            bead_file_path = str(bead_file_path or "").strip()
            if not bead_file_path:
                return (
                    "No bead file uploaded yet.",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            current_fluorescence = str(current_fluorescence or "").strip()
            if not current_fluorescence:
                return (
                    "Select a fluorescence detector first.",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            calibrated_channel_name = str(calibrated_channel_name or "").strip()
            if not calibrated_channel_name:
                return (
                    "Please provide a calibrated MESF channel name (new column).",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            export_mode = str(export_mode or "update_temp").strip()
            if export_mode not in {"update_temp", "save_new"}:
                export_mode = "update_temp"

            export_filename = str(export_filename or "").strip()
            if export_mode == "save_new" and not export_filename:
                return (
                    "Please provide an output file name for Save as new file.",
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            backend = BackEnd(bead_file_path)

            export_response = backend.export_fluorescence_calibration(
                {
                    "calibration": calib_payload,
                    "source_path": bead_file_path,
                    "source_column": current_fluorescence,
                    "new_column": calibrated_channel_name,
                    "mode": export_mode,
                    "export_filename": export_filename,
                }
            )

            exported_path = str(export_response.get("exported_path") or bead_file_path)

            next_sidebar = helper.CalibrationSetupStore.save_fluorescent_setup(
                sidebar_data,
                name=name,
                payload=calib_payload,
            )

            channels = service.channels_from_file(
                exported_path,
                preferred_scatter=current_scatter,
                preferred_fluorescence=calibrated_channel_name,
            )

            msg = f'Calibration "{name}" saved successfully. Exported to: {exported_path}'

            return (
                msg,
                next_sidebar,
                exported_path,
                channels.scatter_options,
                channels.fluorescence_options,
                channels.scatter_value,
                channels.fluorescence_value,
            )
