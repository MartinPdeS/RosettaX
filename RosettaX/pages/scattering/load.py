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
                dbc.CardHeader("1. Upload FCS File"),
                dbc.CardBody(
                    [
                        widget,
                        html.Div(id=self.ids.upload_filename),
                        html.Div(id=self.ids.upload_saved_as),
                    ],
                    style=self.card_body_scroll,
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
                self.backend = BackEnd(temp_path)
            except Exception as exc:
                msg = f"Failed to save file: {exc}"
                return (dash.no_update, msg, [], None)

            try:
                channels = self.service.channels_from_file(temp_path)
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