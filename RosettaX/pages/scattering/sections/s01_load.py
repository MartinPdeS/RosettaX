import base64
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence.backend import BackEnd


@dataclass(frozen=True)
class LoadResult:
    uploaded_fcs_path_store: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.uploaded_fcs_path_store,
            self.scattering_detector_options,
            self.scattering_detector_value,
            self.fluorescence_detector_options,
            self.fluorescence_detector_value,
        )


class LoadSection:

    def __init__(self, page) -> None:
        self.page = page

    def _get_layout(self):
        widget = dcc.Upload(
            id=self.page.ids.Upload.upload,
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
                        html.Div(id=self.page.ids.Upload.filename),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        _header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        output_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        output_path.write_bytes(raw)
        return str(output_path)

    def _register_callbacks(self):
        @callback(
            Output(self.page.ids.Upload.filename, "children"),
            Input(self.page.ids.Upload.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(name):
            if name:
                print(f"Selected file: {name}")
                return str(name)

            return ""

        @callback(
            Output(self.page.ids.Upload.fcs_path_store, "data"),
            Output(self.page.ids.scattering_detector_dropdown, "options"),
            Output(self.page.ids.scattering_detector_dropdown, "value"),
            Output(self.page.ids.fluorescence_detector_dropdown, "options"),
            Output(self.page.ids.fluorescence_detector_dropdown, "value"),
            Input(self.page.ids.Upload.upload, "contents"),
            State(self.page.ids.Upload.upload, "filename"),
            State(self.page.ids.scattering_detector_dropdown, "value"),
            State(self.page.ids.fluorescence_detector_dropdown, "value"),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents,
            filename,
            current_scattering_detector_value,
            current_fluorescence_detector_value,
        ):
            if not contents or not filename:
                return LoadResult(
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                temporary_fcs_path = self.write_upload_to_tempfile(
                    contents=contents,
                    filename=filename,
                )
                print(f"Selected file: {filename}")
                print(f"Saved as: {temporary_fcs_path}")

            except Exception as exc:
                print(f"Failed to save file: {exc}")
                return LoadResult(
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                self.page.backend = BackEnd(temporary_fcs_path)

            except Exception as exc:
                print(f"Failed to initialize backend: {exc}")
                return LoadResult(
                    uploaded_fcs_path_store=temporary_fcs_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                channels = self.page.service.channels_from_file(temporary_fcs_path)

            except Exception as exc:
                print(f"Saved file but could not read channels: {exc}")
                return LoadResult(
                    uploaded_fcs_path_store=temporary_fcs_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            scattering_detector_options = list(channels.scatter_options or [])
            fluorescence_detector_options = list(channels.fluorescence_options or [])

            allowed_scattering_values = {
                str(option["value"])
                for option in scattering_detector_options
                if "value" in option
            }
            allowed_fluorescence_values = {
                str(option["value"])
                for option in fluorescence_detector_options
                if "value" in option
            }

            scattering_detector_value = (
                str(current_scattering_detector_value)
                if current_scattering_detector_value is not None
                and str(current_scattering_detector_value) in allowed_scattering_values
                else channels.scatter_value
            )
            if scattering_detector_value not in allowed_scattering_values:
                scattering_detector_value = (
                    scattering_detector_options[0]["value"]
                    if scattering_detector_options
                    else None
                )

            fluorescence_detector_value = (
                str(current_fluorescence_detector_value)
                if current_fluorescence_detector_value is not None
                and str(current_fluorescence_detector_value) in allowed_fluorescence_values
                else channels.fluorescence_value
            )
            if fluorescence_detector_value not in allowed_fluorescence_values:
                fluorescence_detector_value = (
                    fluorescence_detector_options[0]["value"]
                    if fluorescence_detector_options
                    else None
                )

            return LoadResult(
                uploaded_fcs_path_store=temporary_fcs_path,
                scattering_detector_options=scattering_detector_options,
                scattering_detector_value=scattering_detector_value,
                fluorescence_detector_options=fluorescence_detector_options,
                fluorescence_detector_value=fluorescence_detector_value,
            ).to_tuple()