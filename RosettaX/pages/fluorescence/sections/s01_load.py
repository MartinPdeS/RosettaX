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

from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.utils import service, styling
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadState:
    uploaded_fcs_path: Any = dash.no_update
    uploaded_filename: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update


class Upload:
    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()
        logger.debug("Initialized Upload section with page=%r", page)

    @property
    def uploaded_fcs_filename_store_id(self) -> str:
        return f"{self.page.ids.Upload.uploaded_fcs_path_store}-filename"

    def _refresh_runtime(self) -> RuntimeConfig:
        self.runtime_config = RuntimeConfig()
        return self.runtime_config

    def _get_initial_fluorescence_fcs_file_path(self) -> Optional[str]:
        runtime_config = self._refresh_runtime()
        return runtime_config.get_path("files.fluorescence_fcs_file_path", default=None)

    def get_layout(self):
        initial_fcs_path = self._get_initial_fluorescence_fcs_file_path()
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        logger.debug(
            "Building upload layout with initial_fcs_path=%r initial_filename=%r",
            initial_fcs_path,
            initial_filename,
        )

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
                            id=self.page.ids.Upload.uploaded_fcs_path_store,
                            data=initial_fcs_path,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.uploaded_fcs_filename_store_id,
                            data=initial_filename,
                            storage_type="session",
                        ),
                        upload_widget,
                        html.Div(id=self.page.ids.Upload.upload_filename),
                    ],
                    style=self.page.style["body_scroll"],
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

    @staticmethod
    def _pick_dropdown_value(
        *,
        preferred_value: Optional[str],
        current_value: Optional[str],
        options: list[dict[str, Any]],
    ) -> Optional[str]:
        allowed_values = {
            str(option.get("value"))
            for option in options
            if "value" in option
        }

        if preferred_value is not None and str(preferred_value) in allowed_values:
            return str(preferred_value)

        if current_value is not None and str(current_value) in allowed_values:
            return str(current_value)

        if options:
            return str(options[0].get("value"))

        return None

    def _build_upload_state(
        self,
        *,
        contents: Optional[str],
        stored_fcs_path: Optional[str],
        filename: Optional[str],
        stored_filename: Optional[str],
        current_scattering_detector_value: Optional[str],
        current_fluorescence_detector_value: Optional[str],
    ) -> UploadState:
        if contents and filename:
            try:
                selected_fcs_path = self.write_upload_to_tempfile(
                    contents=contents,
                    filename=filename,
                )
                display_filename = filename
            except Exception:
                logger.exception(
                    "Failed to write uploaded file to temporary path for filename=%r",
                    filename,
                )
                return UploadState(
                    uploaded_fcs_path=None,
                    uploaded_filename="",
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                )
        elif stored_fcs_path:
            selected_fcs_path = str(stored_fcs_path).strip()
            display_filename = str(stored_filename).strip() if stored_filename else Path(selected_fcs_path).name
        else:
            return UploadState(
                uploaded_fcs_path=None,
                uploaded_filename="",
                scattering_detector_options=[],
                scattering_detector_value=None,
                fluorescence_detector_options=[],
                fluorescence_detector_value=None,
            )

        try:
            self.page.backend = BackEnd(selected_fcs_path)
            logger.debug(
                "Initialized fluorescence backend for selected_fcs_path=%r",
                selected_fcs_path,
            )
        except Exception:
            logger.exception(
                "Failed to initialize fluorescence backend for selected_fcs_path=%r",
                selected_fcs_path,
            )
            return UploadState(
                uploaded_fcs_path=selected_fcs_path,
                uploaded_filename=display_filename,
                scattering_detector_options=[],
                scattering_detector_value=None,
                fluorescence_detector_options=[],
                fluorescence_detector_value=None,
            )

        try:
            channels = service.build_channel_options_from_file(selected_fcs_path)
            logger.debug(
                "Extracted channel options successfully for selected_fcs_path=%r",
                selected_fcs_path,
            )
        except Exception:
            logger.exception(
                "Failed to extract channel options from selected_fcs_path=%r",
                selected_fcs_path,
            )
            return UploadState(
                uploaded_fcs_path=selected_fcs_path,
                uploaded_filename=display_filename,
                scattering_detector_options=[],
                scattering_detector_value=None,
                fluorescence_detector_options=[],
                fluorescence_detector_value=None,
            )

        runtime_config = self._refresh_runtime()
        runtime_config.update_paths(
            updates={
                "files.fluorescence_fcs_file_path": selected_fcs_path,
            }
        )

        scattering_detector_options = list(channels.scatter_options or [])
        fluorescence_detector_options = list(channels.secondary_options or [])

        preferred_scattering_detector = runtime_config.get_path(
            "page_defaults.fluorescence.scattering_detector",
            default=None,
        )
        preferred_fluorescence_detector = runtime_config.get_path(
            "page_defaults.fluorescence.fluorescence_detector",
            default=None,
        )

        scattering_detector_value = self._pick_dropdown_value(
            preferred_value=str(preferred_scattering_detector).strip() if preferred_scattering_detector else None,
            current_value=str(current_scattering_detector_value).strip() if current_scattering_detector_value else None,
            options=scattering_detector_options,
        )
        if scattering_detector_value is None:
            scattering_detector_value = self._pick_dropdown_value(
                preferred_value=None,
                current_value=str(channels.scatter_value).strip() if channels.scatter_value else None,
                options=scattering_detector_options,
            )

        fluorescence_detector_value = self._pick_dropdown_value(
            preferred_value=str(preferred_fluorescence_detector).strip() if preferred_fluorescence_detector else None,
            current_value=str(current_fluorescence_detector_value).strip() if current_fluorescence_detector_value else None,
            options=fluorescence_detector_options,
        )
        if fluorescence_detector_value is None:
            fluorescence_detector_value = self._pick_dropdown_value(
                preferred_value=None,
                current_value=str(channels.fluorescence_value).strip() if channels.fluorescence_value else None,
                options=fluorescence_detector_options,
            )

        logger.debug(
            "Built upload state with uploaded_fcs_path=%r uploaded_filename=%r "
            "scattering_detector_value=%r fluorescence_detector_value=%r",
            selected_fcs_path,
            display_filename,
            scattering_detector_value,
            fluorescence_detector_value,
        )

        return UploadState(
            uploaded_fcs_path=selected_fcs_path,
            uploaded_filename=display_filename,
            scattering_detector_options=scattering_detector_options,
            scattering_detector_value=scattering_detector_value,
            fluorescence_detector_options=fluorescence_detector_options,
            fluorescence_detector_value=fluorescence_detector_value,
        )

    def register_callbacks(self):
        @callback(
            Output(self.page.ids.Upload.upload_filename, "children"),
            Input(self.uploaded_fcs_filename_store_id, "data"),
        )
        def show_filename(stored_filename):
            logger.debug("show_filename called with stored_filename=%r", stored_filename)

            if not stored_filename:
                return ""

            return f"Loaded file: {stored_filename}"

        @callback(
            Output(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            Output(self.uploaded_fcs_filename_store_id, "data"),
            Output(self.page.ids.Scattering.detector_dropdown, "options"),
            Output(self.page.ids.Scattering.detector_dropdown, "value"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "options"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "value"),
            Input(self.page.ids.Upload.upload, "contents"),
            Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            State(self.page.ids.Upload.upload, "filename"),
            State(self.uploaded_fcs_filename_store_id, "data"),
            State(self.page.ids.Scattering.detector_dropdown, "value"),
            State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=False,
        )
        def handle_upload(
            contents,
            stored_fcs_path,
            filename,
            stored_filename,
            current_scattering_detector_value,
            current_fluorescence_detector_value,
        ):
            logger.debug(
                "handle_upload called with contents_type=%s stored_fcs_path=%r filename=%r "
                "stored_filename=%r current_scattering_detector_value=%r "
                "current_fluorescence_detector_value=%r",
                type(contents).__name__,
                stored_fcs_path,
                filename,
                stored_filename,
                current_scattering_detector_value,
                current_fluorescence_detector_value,
            )

            upload_state = self._build_upload_state(
                contents=str(contents) if contents else None,
                stored_fcs_path=str(stored_fcs_path).strip() if stored_fcs_path else None,
                filename=str(filename).strip() if filename else None,
                stored_filename=str(stored_filename).strip() if stored_filename else None,
                current_scattering_detector_value=(
                    str(current_scattering_detector_value).strip()
                    if current_scattering_detector_value
                    else None
                ),
                current_fluorescence_detector_value=(
                    str(current_fluorescence_detector_value).strip()
                    if current_fluorescence_detector_value
                    else None
                ),
            )

            logger.debug(
                "handle_upload returning uploaded_fcs_path=%r uploaded_filename=%r "
                "scattering_detector_options_count=%r fluorescence_detector_options_count=%r "
                "scattering_detector_value=%r fluorescence_detector_value=%r",
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
                len(upload_state.scattering_detector_options or []),
                len(upload_state.fluorescence_detector_options or []),
                upload_state.scattering_detector_value,
                upload_state.fluorescence_detector_value,
            )

            return (
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
                upload_state.scattering_detector_options,
                upload_state.scattering_detector_value,
                upload_state.fluorescence_detector_options,
                upload_state.fluorescence_detector_value,
            )