from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence import BaseSection, SectionContext, helper
from RosettaX.pages.runtime_config import get_ui_flags


class LoadSection(BaseSection):
    def __init__(self, *, context: SectionContext) -> None:
        super().__init__(context=context)
        self.debug_text_id = f"{self.context.ids.page_name}-load-debug-out"

    def layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("1. Upload Bead File"),
                dbc.CardBody(
                    [
                        self._upload_component(),
                        self._filename_outputs(),
                        html.Br(),
                        *self._max_events_input_if_debug(),
                        self._debug_output_container(),
                    ],
                    style=self.context.card_body_scroll,
                ),
            ]
        )

    def _upload_component(self) -> html.Div:
        ids = self.context.ids
        return dcc.Upload(
            id=ids.upload,
            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
            style=styling.UPLOAD,
            multiple=False,
        )

    def _filename_outputs(self) -> html.Div:
        ids = self.context.ids
        return html.Div(
            [
                html.Div(id=ids.upload_filename),
                html.Div(id=ids.upload_saved_as),
            ]
        )

    def _max_events_input_if_debug(self) -> list:
        if not get_ui_flags().debug:
            return []

        ids = self.context.ids
        return [
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

    def _debug_output_container(self) -> html.Div:
        debug_style = {"display": "block"} if get_ui_flags().debug else {"display": "none"}
        return html.Div(
            [
                html.Hr(),
                dbc.Alert("Debug outputs (LoadSection)", color="secondary", is_open=True),
                html.Pre(id=self.debug_text_id, style={"whiteSpace": "pre-wrap"}),
            ],
            style=debug_style,
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
            Input(ids.upload, "contents"),
            State(ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def load_uploaded_file(contents: Optional[str], filename: Optional[str]):
            return self._handle_file_upload(contents, filename, service)

    def _handle_file_upload(self, contents, filename, service):
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
                debug_text if get_ui_flags().debug else "",
            )

        try:
            temp_path = helper.write_upload_to_tempfile(contents=contents, filename=str(filename))
        except Exception as exc:
            debug_text = f"Failed to write temp file: {exc}"
            return (
                dash.no_update,
                debug_text,
                [],
                [],
                None,
                None,
                dash.no_update,
                debug_text if get_ui_flags().debug else "",
            )

        try:
            channels = service.channels_from_file(temp_path)
        except Exception as exc:
            debug_text = f"Saved as: {temp_path} but could not read it: {exc}"
            return (
                temp_path,
                debug_text,
                [],
                [],
                None,
                None,
                dash.no_update,
                debug_text if get_ui_flags().debug else "",
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
            debug_text if get_ui_flags().debug else "",
        )
