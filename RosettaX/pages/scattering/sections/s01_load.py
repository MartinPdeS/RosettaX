# -*- coding: utf-8 -*-

import base64
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any = dash.no_update
    uploaded_filename: Any = dash.no_update


class Upload:
    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()
        logger.debug("Initialized Upload section with page=%r", page)

    def _refresh_runtime(self) -> RuntimeConfig:
        self.runtime_config = RuntimeConfig()
        return self.runtime_config

    def _get_initial_scattering_fcs_file_path(self) -> Optional[str]:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_path("files.scattering_fcs_file_path", default=None)

    def get_layout(self) -> dbc.Card:
        initial_fcs_path = self._get_initial_scattering_fcs_file_path()
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        logger.debug(
            "Building upload layout with initial_fcs_path=%r initial_filename=%r",
            initial_fcs_path,
            initial_filename,
        )

        return dbc.Card(
            [
                dbc.CardHeader("1. Upload FCS File"),
                dbc.CardBody(
                    [
                        dcc.Store(
                            id=self.page.ids.Upload.fcs_path_store,
                            data=initial_fcs_path,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.page.ids.Upload.filename_store,
                            data=initial_filename,
                            storage_type="session",
                        ),
                        dcc.Upload(
                            id=self.page.ids.Upload.upload,
                            children=html.Div(["Drag and Drop or ", html.A("Select Bead File")]),
                            style=styling.UPLOAD,
                            multiple=False,
                            accept=".fcs",
                        ),
                        html.Div(id=self.page.ids.Upload.filename),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        logger.debug(
            "write_upload_to_tempfile called with filename=%r contents_type=%s",
            filename,
            type(contents).__name__,
        )

        _, encoded_content = contents.split(",", 1)
        raw_bytes = base64.b64decode(encoded_content)

        file_suffix = Path(filename).suffix or ".bin"
        temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
        temporary_directory.mkdir(parents=True, exist_ok=True)

        temporary_file_path = temporary_directory / f"{next(tempfile._get_candidate_names())}{file_suffix}"
        temporary_file_path.write_bytes(raw_bytes)

        logger.debug(
            "write_upload_to_tempfile wrote temporary_file_path=%r byte_count=%r",
            str(temporary_file_path),
            len(raw_bytes),
        )

        return str(temporary_file_path)

    def _build_upload_state(
        self,
        *,
        contents: Optional[str],
        filename: Optional[str],
    ) -> UploadState:
        logger.debug(
            "_build_upload_state called with has_contents=%r filename=%r",
            bool(contents),
            filename,
        )

        if not contents or not filename:
            logger.debug("No upload payload provided. Returning empty UploadState.")
            return UploadState(
                uploaded_fcs_path=None,
                uploaded_filename=None,
            )

        try:
            uploaded_fcs_path = self.write_upload_to_tempfile(
                contents=contents,
                filename=filename,
            )

            runtime_config = self._refresh_runtime()
            runtime_config.update_paths(
                files__scattering_fcs_file_path=uploaded_fcs_path,
            )

            self.page.backend = BackEnd(
                fcs_file_path=uploaded_fcs_path,
            )

            logger.debug(
                "Created scattering backend for uploaded_fcs_path=%r",
                uploaded_fcs_path,
            )

            return UploadState(
                uploaded_fcs_path=uploaded_fcs_path,
                uploaded_filename=str(filename),
            )

        except Exception:
            logger.exception(
                "Failed to build upload state for filename=%r",
                filename,
            )
            self.page.backend = None

            return UploadState(
                uploaded_fcs_path=None,
                uploaded_filename=None,
            )

    def register_callbacks(self) -> None:
        @callback(
            Output(self.page.ids.Upload.filename, "children"),
            Input(self.page.ids.Upload.filename_store, "data"),
        )
        def show_filename(stored_filename: Any) -> str:
            logger.debug("show_filename called with stored_filename=%r", stored_filename)

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
        def handle_upload(contents: Any, filename: Any) -> tuple[Any, Any]:
            logger.debug(
                "handle_upload called with contents_type=%s filename=%r",
                type(contents).__name__,
                filename,
            )

            upload_state = self._build_upload_state(
                contents=str(contents) if contents is not None else None,
                filename=str(filename) if filename is not None else None,
            )

            logger.debug(
                "handle_upload returning uploaded_fcs_path=%r uploaded_filename=%r",
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )

            return (
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )