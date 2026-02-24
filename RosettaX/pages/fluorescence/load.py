import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

import base64
import tempfile
from pathlib import Path

from RosettaX.pages import styling
from RosettaX.pages.fluorescence.backend import BackEnd


class LoadSection():
    """Section 1: Upload bead file (no debug mode)."""
    def _load_get_layout(self):
        widget = dcc.Upload(
            id=self.ids.upload,
            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
            style=styling.UPLOAD,
            multiple=False,
            accept=".fcs",
        )

        return dbc.Card(
            [
                dbc.CardHeader("1. Upload Bead File"),
                dbc.CardBody(
                    [
                        widget,
                        html.Div(id=self.ids.upload_filename),
                        html.Div(id=self.ids.upload_saved_as),
                    ],
                    style=self.context.card_body_scroll,
                ),
            ]
        )


    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        out_path.write_bytes(raw)
        return str(out_path)


    def _load_register_callbacks(self):
        @callback(
            Output(self.ids.upload_filename, "children"),
            Input(self.ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(name):
            return f"Selected file: {name}" if name else ""

        # Handle upload
        @callback(
            Output(self.ids.uploaded_fcs_path_store, "data"),
            Output(self.ids.upload_saved_as, "children"),
            Output(self.ids.scattering_detector_dropdown, "options"),
            Output(self.ids.scattering_detector_dropdown, "value"),
            Output(self.ids.fluorescence_detector_dropdown, "options"),
            Output(self.ids.fluorescence_detector_dropdown, "value"),
            Input(self.ids.upload, "contents"),
            State(self.ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def handle_upload(contents, filename):
            if not contents or not filename:
                msg = "No file uploaded."
                # return (dash.no_update, msg, [], [], None, None, dash.no_update)
                return (dash.no_update, msg, [], None)

            try:
                temp_path = self.write_upload_to_tempfile(contents=contents, filename=filename)
                self.context.backend = BackEnd(temp_path)
            except Exception as exc:
                msg = f"Failed to save file: {exc}"
                return (dash.no_update, msg, [], None)

            try:
                channels = self.context.service.channels_from_file(temp_path)
            except Exception as exc:
                msg = f"Saved as {temp_path}, but could not read: {exc}"
                return (temp_path, msg, [], None)

            return (
                temp_path,
                f"Saved as: {temp_path}",
                channels.scatter_options,
                channels.scatter_value,
                channels.fluorescence_options,
                channels.fluorescence_value
            )


        # # Handle upload
        # @callback(
        #     Output(ids.uploaded_fcs_path_store, "data"),
        #     Output(ids.upload_saved_as, "children"),
        #     Output(ids.scattering_detector_dropdown, "options"),
        #     Output(ids.fluorescence_detector_dropdown, "options"),
        #     Output(ids.scattering_detector_dropdown, "value"),
        #     # Output(ids.fluorescence_detector_dropdown, "value"),
        #     # Output(ids.fluorescence_hist_store, "data", allow_duplicate=True),
        #     Input(ids.upload, "contents"),
        #     State(ids.upload, "filename"),
        #     prevent_initial_call=True,
        # )
        # def handle_upload(contents, filename):
        #     print("DEBUG handle_upload: contents is None?", contents is None, "filename =", filename)

        #     if not contents or not filename:
        #         msg = "No file uploaded."
        #         print("DEBUG handle_upload: early return, no contents or filename")
        #         # return (dash.no_update, msg, [], [], None, None, dash.no_update)
        #         return (dash.no_update, msg, [], [], None)

        #     try:
        #         temp_path = helper.write_upload_to_tempfile(contents, filename)
        #         self.context.backend = BackEnd(temp_path)
        #         print("---: ", self.context.backend.fcs_file.get_column_names())
        #         print("DEBUG handle_upload: backend set, columns =", self.context.backend.fcs_file.get_column_names())
        #     except Exception as exc:
        #         msg = f"Failed to save file: {exc}"
        #         print("DEBUG handle_upload: exception while saving file:", exc)
        #         return (dash.no_update, msg, [], [], None,)

        #     try:
        #         channels = service.channels_from_file(temp_path)
        #         print("DEBUG handle_upload: channels.scatter_options =", channels.scatter_options)
        #     except Exception as exc:
        #         msg = f"Saved as {temp_path}, but could not read: {exc}"
        #         print("DEBUG handle_upload: exception while reading channels:", exc)
        #         return (temp_path, msg, [], [], None, None, dash.no_update)

        #     return (
        #         temp_path,
        #         f"Saved as: {temp_path}",
        #         channels.scatter_options,
        #         channels.fluorescence_options,
        #         channels.scatter_value,
        #         channels.fluorescence_value,
        #         None,
        #     )
