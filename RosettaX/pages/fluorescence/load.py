from typing import Optional

import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc

from RosettaX.pages import styling
from RosettaX.pages.fluorescence import BaseSection, SectionContext, helper
from RosettaX.pages.runtime_config import get_runtime_config

class LoadSection(BaseSection):
    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)
        self.debug_text_id = f"{self.context.ids.page_name}-load-debug-out"

    def layout(self) -> dbc.Card:
        ids = self.context.ids

        debug_container_style = {"display": "block"} if get_runtime_config().debug else {"display": "none"}

        return dbc.Card(
            [
                dbc.CardHeader("1. Upload Bead File"),
                dbc.CardBody(
                    [
                        dcc.Upload(
                            id=ids.upload,
                            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
                            style=styling.UPLOAD,
                            multiple=False,
                        ),
                        html.Div(id=ids.upload_filename),
                        html.Div(id=ids.upload_saved_as),
                        html.Br(),
                        *(
                            [
                                html.Div(
                                    [
                                        html.Div("Max events used for plots and peak finding:"),
                                        dcc.Input(
                                            id=ids.max_events_for_plots_input,
                                            type="number",
                                            min=10_000,
                                            step=10_000,
                                            value=200_000,
                                            style={"width": "220px"},
                                        ),
                                    ],
                                    style=styling.CARD,
                                )
                            ]
                            if get_runtime_config().debug
                            else []
                        ),
                        html.Br(),
                        html.Button("Load", id=ids.load_file_btn, n_clicks=0),
                        html.Div(
                            [
                                html.Hr(),
                                dbc.Alert("Debug outputs (LoadSection)", color="secondary", is_open=True),
                                html.Pre(id=self.debug_text_id, style={"whiteSpace": "pre-wrap"}),
                            ],
                            style=debug_container_style,
                        ),
                    ],
                    style=self.context.card_body_scroll,
                ),
            ]
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids
        service = self.context.service

        @callback(
            Output(ids.upload_filename, "children"),
            Input(ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_selected_filename(filename: Optional[str]):
            if not filename:
                return ""
            return f"Selected file: {filename}"

        @callback(
            Output(ids.uploaded_fcs_path_store, "data"),
            Output(ids.upload_saved_as, "children"),
            Output(ids.scattering_detector_dropdown, "options"),
            Output(ids.fluorescence_detector_dropdown, "options"),
            Output(ids.scattering_detector_dropdown, "value"),
            Output(ids.fluorescence_detector_dropdown, "value"),
            Output(ids.fluorescence_hist_store, "data", allow_duplicate=True),
            Output(self.debug_text_id, "children"),
            Input(ids.load_file_btn, "n_clicks"),
            State(ids.upload, "contents"),
            State(ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def load_uploaded_file(
            n_clicks: int,
            contents: Optional[str],
            filename: Optional[str],
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
                    "",
                )

            if not contents or not filename:
                debug_text = "No file uploaded yet."
                return (
                    dash.no_update,
                    "No file uploaded yet.",
                    [],
                    [],
                    None,
                    None,
                    dash.no_update,
                    debug_text if get_runtime_config().debug else "",
                )

            try:
                temp_path = helper.write_upload_to_tempfile(contents=contents, filename=str(filename))
            except Exception as exc:
                debug_text = f"Failed to write temp file: {exc}"
                return (
                    dash.no_update,
                    f"Failed to write temp file: {exc}",
                    [],
                    [],
                    None,
                    None,
                    dash.no_update,
                    debug_text if get_runtime_config().debug else "",
                )

            try:
                channels = service.channels_from_file(temp_path)
            except Exception as exc:
                debug_text = f"Saved as: {temp_path} but could not read it: {exc}"
                return (
                    temp_path,
                    f"Saved as: {temp_path} but could not read it: {exc}",
                    [],
                    [],
                    None,
                    None,
                    dash.no_update,
                    debug_text if get_runtime_config().debug else "",
                )

            debug_text = (
                f"temp_path: {temp_path}\n"
                f"scatter_options: {len(channels.scatter_options)}\n"
                f"fluorescence_options: {len(channels.fluorescence_options)}\n"
            )

            return (
                temp_path,
                f"Saved as: {temp_path}",
                channels.scatter_options,
                channels.fluorescence_options,
                channels.scatter_value,
                channels.fluorescence_value,
                None,
                debug_text if get_runtime_config().debug else "",
            )
