# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.pages.scattering.services.upload import build_upload_state


logger = logging.getLogger(__name__)


class Upload:
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Upload section with page=%r", page)

    def _get_initial_scattering_fcs_file_path(self) -> Optional[str]:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        runtime_config = RuntimeConfig.from_default_profile()
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
            Output("runtime-config-store", "data", allow_duplicate=True),
            Input(self.page.ids.Upload.upload, "contents"),
            State(self.page.ids.Upload.upload, "filename"),
            State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents: Any,
            filename: Any,
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any]:
            logger.debug(
                "handle_upload called with contents_type=%s filename=%r runtime_config_data_type=%s",
                type(contents).__name__,
                filename,
                type(runtime_config_data).__name__,
            )

            upload_state = build_upload_state(
                page=self.page,
                contents=str(contents) if contents is not None else None,
                filename=str(filename) if filename is not None else None,
                runtime_config_data=runtime_config_data if isinstance(runtime_config_data, dict) else None,
            )

            logger.debug(
                "handle_upload returning uploaded_fcs_path=%r uploaded_filename=%r",
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )

            return (
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
                upload_state.runtime_config_data,
            )