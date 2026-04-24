# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils import styling, ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig
from . import services


logger = logging.getLogger(__name__)


class Upload:
    """
    Scattering FCS upload section.

    Responsibilities
    ----------------
    - Render the upload area.
    - Store the uploaded FCS path in session state.
    - Store the uploaded filename in session state.
    - Synchronize the uploaded path into runtime-config-store.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Upload
        logger.debug("Initialized Upload section with page=%r", page)

    def _get_initial_scattering_fcs_file_path(self) -> Optional[str]:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return runtime_config.get_path(
            "files.scattering_fcs_file_path",
            default=None,
        )

    def get_layout(self) -> html.Div:
        initial_fcs_path = self._get_initial_scattering_fcs_file_path()
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        logger.debug(
            "Building upload layout with initial_fcs_path=%r initial_filename=%r",
            initial_fcs_path,
            initial_filename,
        )

        return html.Div(
            [
                self._build_hero_section(),
                html.Div(style={"height": "16px"}),
                self._build_upload_card(
                    initial_fcs_path=initial_fcs_path,
                    initial_filename=initial_filename,
                ),
            ]
        )

    def _build_hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Scattering calibration",
                        title_component="H2",
                        description=(
                            "Start by uploading the FCS file used for the scattering calibration workflow. "
                            "After upload, RosettaX will keep the selected file in session state and use it as "
                            "the data source for detector selection, histogram inspection, peak finding, and model fitting."
                        ),
                    ),
                ]
            )
        )

    def _build_upload_card(
        self,
        *,
        initial_fcs_path: Optional[str],
        initial_filename: str,
    ) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("1. Upload FCS File"),
                dbc.CardBody(
                    [
                        dcc.Store(
                            id=self.ids.fcs_path_store,
                            data=initial_fcs_path,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.ids.filename_store,
                            data=initial_filename,
                            storage_type="session",
                        ),
                        dcc.Upload(
                            id=self.ids.upload,
                            children=html.Div(
                                [
                                    "Drag and Drop or ",
                                    html.A("Select Bead File"),
                                ]
                            ),
                            style=styling.UPLOAD,
                            multiple=False,
                            accept=".fcs",
                        ),
                        html.Div(
                            id=self.ids.filename,
                        ),
                    ],
                    style=styling.PAGE["card_body_scroll"],
                ),
            ]
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the upload section.
        """
        logger.debug("Registering Upload section callbacks.")
        self._register_filename_display_callback()
        self._register_upload_callback()

    def _register_filename_display_callback(self) -> None:
        @callback(
            Output(self.ids.filename, "children"),
            Input(self.ids.filename_store, "data"),
        )
        def show_filename(stored_filename: Any) -> str:
            logger.debug(
                "show_filename called with stored_filename=%r",
                stored_filename,
            )

            if not stored_filename:
                return ""

            return f"Loaded file: {stored_filename}"

    def _register_upload_callback(self) -> None:
        @callback(
            Output(self.ids.fcs_path_store, "data"),
            Output(self.ids.filename_store, "data"),
            Output("runtime-config-store", "data", allow_duplicate=True),
            Input(self.ids.upload, "contents"),
            State(self.ids.upload, "filename"),
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

            upload_state = services.build_upload_state(
                page=self.page,
                contents=str(contents) if contents is not None else None,
                filename=str(filename) if filename is not None else None,
                runtime_config_data=runtime_config_data
                if isinstance(runtime_config_data, dict)
                else None,
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