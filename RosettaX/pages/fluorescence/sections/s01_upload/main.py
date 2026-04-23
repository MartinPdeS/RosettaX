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
    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Upload section with page=%r", page)

    @property
    def uploaded_fcs_filename_store_id(self) -> str:
        return f"{self.page.ids.Upload.uploaded_fcs_path_store}-filename"

    def _get_initial_fluorescence_fcs_file_path(self) -> Optional[str]:
        runtime_config = RuntimeConfig.from_default_profile()
        return runtime_config.get_path("files.fluorescence_fcs_file_path", default=None)

    def get_layout(self):
        initial_fcs_path = self._get_initial_fluorescence_fcs_file_path()
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
                        title="Fluorescence calibration",
                        title_component="H2",
                        title_style_overrides={
                            "fontSize": "2rem",
                            "fontWeight": "600",
                            "lineHeight": "1.2",
                            "marginBottom": "8px",
                        },
                        description=(
                            "Start by uploading the bead FCS file used to build the fluorescence calibration. "
                            "After upload, RosettaX will inspect the detector names, populate the scattering and "
                            "fluorescence dropdowns, and keep the selected file available for the rest of the workflow."
                        ),
                        description_opacity=0.9,
                        description_margin_bottom_px=0,
                        description_style_overrides={
                            "fontSize": "1.02rem",
                            "maxWidth": "980px",
                            "marginBottom": "0px",
                        },
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
                            id=self.page.ids.Upload.uploaded_fcs_path_store,
                            data=initial_fcs_path,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.uploaded_fcs_filename_store_id,
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
                        html.Div(id=self.page.ids.Upload.upload_filename),
                    ],
                    style=styling.PAGE["body_scroll"],
                ),
            ]
        )

    def register_callbacks(self):
        @callback(
            Output(self.page.ids.Upload.upload_filename, "children"),
            Input(self.uploaded_fcs_filename_store_id, "data"),
        )
        def show_filename(stored_filename: Any) -> str:
            logger.debug("show_filename called with stored_filename=%r", stored_filename)
            return services.build_loaded_filename_text(stored_filename)

        @callback(
            Output(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            Output(self.uploaded_fcs_filename_store_id, "data"),
            Output(self.page.ids.Scattering.detector_dropdown, "options"),
            Output(self.page.ids.Scattering.detector_dropdown, "value"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "options"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "value"),
            Output("runtime-config-store", "data", allow_duplicate=True),
            Input(self.page.ids.Upload.upload, "contents"),
            Input(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            State(self.page.ids.Upload.upload, "filename"),
            State(self.uploaded_fcs_filename_store_id, "data"),
            State(self.page.ids.Scattering.detector_dropdown, "value"),
            State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            State("runtime-config-store", "data"),
            prevent_initial_call="initial_duplicate",
        )
        def handle_upload(
            contents: Any,
            stored_fcs_path: Any,
            filename: Any,
            stored_filename: Any,
            current_scattering_detector_value: Any,
            current_fluorescence_detector_value: Any,
            runtime_config_data: Any,
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

            upload_state = services.build_upload_state(
                page=self.page,
                contents=services.clean_optional_string(contents),
                stored_fcs_path=services.clean_optional_string(stored_fcs_path),
                filename=services.clean_optional_string(filename),
                stored_filename=services.clean_optional_string(stored_filename),
                current_scattering_detector_value=services.clean_optional_string(current_scattering_detector_value),
                current_fluorescence_detector_value=services.clean_optional_string(current_fluorescence_detector_value),
                runtime_config_data=runtime_config_data if isinstance(runtime_config_data, dict) else None,
                logger=logger,
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

            return upload_state.to_tuple()