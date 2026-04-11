import base64
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.scattering.backend import BackEnd


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any = dash.no_update
    uploaded_filename: Any = dash.no_update


class LoadSection:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized LoadSection with page=%r", page)

    def get_layout(self):
        upload_widget = dcc.Upload(
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
                        dcc.Store(
                            id=self.page.ids.Upload.fcs_path_store,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.page.ids.Upload.filename_store,
                            storage_type="session",
                        ),
                        upload_widget,
                        html.Div(id=self.page.ids.Upload.filename),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        _, encoded_content = contents.split(",", 1)
        raw_bytes = base64.b64decode(encoded_content)

        file_suffix = Path(filename).suffix or ".bin"
        temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
        temporary_directory.mkdir(parents=True, exist_ok=True)

        temporary_file_path = temporary_directory / f"{next(tempfile._get_candidate_names())}{file_suffix}"
        temporary_file_path.write_bytes(raw_bytes)

        return str(temporary_file_path)

    def _build_upload_state(
        self,
        *,
        contents: Optional[str],
        filename: Optional[str],
    ) -> UploadState:
        if not contents or not filename:
            return UploadState(
                uploaded_fcs_path=None,
                uploaded_filename=None,
            )

        try:
            temporary_fcs_path = self.write_upload_to_tempfile(
                contents=contents,
                filename=filename,
            )
        except Exception:
            logger.exception(
                "Failed to write uploaded file to temporary path for filename=%r",
                filename,
            )
            return UploadState(
                uploaded_fcs_path=None,
                uploaded_filename=None,
            )

        try:
            self.page.backend = BackEnd(temporary_fcs_path)
        except Exception:
            logger.exception(
                "Failed to initialize BackEnd for temporary_fcs_path=%r",
                temporary_fcs_path,
            )

        return UploadState(
            uploaded_fcs_path=temporary_fcs_path,
            uploaded_filename=filename,
        )

    def register_callbacks(self):
        @callback(
            Output(self.page.ids.Upload.filename, "children"),
            Input(self.page.ids.Upload.filename_store, "data"),
        )
        def show_filename(stored_filename):
            if not stored_filename:
                return ""

            return f"Loaded file: {stored_filename}"

        @callback(
            Output(self.page.ids.Upload.fcs_path_store, "data"),
            Output(self.page.ids.Upload.filename_store, "data"),
            Input(self.page.ids.Upload.upload, "contents"),
            State(self.page.ids.Upload.upload, "filename"),
            prevent_initial_call=True,
        )
        def handle_upload(contents, filename):
            upload_state = self._build_upload_state(
                contents=contents,
                filename=filename,
            )

            return (
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )