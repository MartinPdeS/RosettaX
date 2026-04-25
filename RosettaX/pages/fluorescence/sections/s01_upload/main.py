# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.fluorescence.state import FluorescencePageState
from RosettaX.pages.fluorescence.state import build_empty_peak_lines_payload
from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.runtime_config import RuntimeConfig

from . import services


logger = logging.getLogger(__name__)


class Upload:
    """
    Fluorescence FCS upload section.

    Responsibilities
    ----------------
    - Render the fluorescence calibration upload area.
    - Store the uploaded FCS path in the page state store.
    - Store the uploaded filename in the page state store.
    - Clear fluorescence peak annotations after a new upload.
    - Clear fluorescence graph state after a new upload.
    - Synchronize the uploaded path into runtime-config-store.

    Notes
    -----
    Detector selection is owned by the active peak script.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Upload

        logger.debug(
            "Initialized Upload section with page=%r",
            page,
        )

    def _get_initial_fluorescence_fcs_file_path(self) -> Optional[str]:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from the page state store inside callbacks.

        Returns
        -------
        Optional[str]
            Initial fluorescence FCS file path.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return runtime_config.get_path(
            "files.fluorescence_fcs_file_path",
            default=None,
        )

    def get_layout(self) -> html.Div:
        """
        Build the upload section layout.

        Returns
        -------
        html.Div
            Upload layout.
        """
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
                html.Div(
                    style={
                        "height": "16px",
                    },
                ),
                self._build_upload_card(
                    initial_filename=initial_filename,
                ),
            ]
        )

    def _build_hero_section(self) -> dbc.Card:
        """
        Build the hero section.

        Returns
        -------
        dbc.Card
            Hero card.
        """
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
                            "After upload, RosettaX will keep the selected file available for the rest of the "
                            "workflow. Detector selection is handled by the selected peak script."
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
        initial_filename: str,
    ) -> dbc.Card:
        """
        Build the upload card.

        Parameters
        ----------
        initial_filename:
            Filename displayed before callbacks run.

        Returns
        -------
        dbc.Card
            Upload card.
        """
        return dbc.Card(
            [
                dbc.CardHeader("1. Upload FCS File"),
                dbc.CardBody(
                    [
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
                            id=self.ids.upload_filename,
                            children=services.build_loaded_filename_text(
                                initial_filename,
                            ),
                        ),
                    ],
                    style=styling.PAGE["body_scroll"],
                ),
            ]
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence upload section.
        """
        logger.debug("Registering Upload section callbacks.")

        self._register_filename_display_callback()
        self._register_upload_callback()

    def _register_filename_display_callback(self) -> None:
        @callback(
            Output(self.ids.upload_filename, "children"),
            Input(self.page.ids.State.page_state_store, "data"),
        )
        def show_filename(
            page_state_payload: Any,
        ) -> str:
            page_state = FluorescencePageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            logger.debug(
                "show_filename called with uploaded_filename=%r",
                page_state.uploaded_filename,
            )

            return services.build_loaded_filename_text(
                page_state.uploaded_filename,
            )

    def _register_upload_callback(self) -> None:
        @callback(
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Output(
                "runtime-config-store",
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.upload, "contents"),
            State(self.ids.upload, "filename"),
            State(self.page.ids.State.page_state_store, "data"),
            State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents: Any,
            filename: Any,
            page_state_payload: Any,
            runtime_config_data: Any,
        ) -> tuple[Any, Any]:
            logger.debug(
                "handle_upload called with contents_type=%s filename=%r "
                "page_state_payload_type=%s runtime_config_data_type=%s",
                type(contents).__name__,
                filename,
                type(page_state_payload).__name__,
                type(runtime_config_data).__name__,
            )

            current_page_state = FluorescencePageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            upload_state = services.build_upload_state(
                page=self.page,
                contents=services.clean_optional_string(
                    contents,
                ),
                stored_fcs_path=services.clean_optional_string(
                    current_page_state.uploaded_fcs_path,
                ),
                filename=services.clean_optional_string(
                    filename,
                ),
                stored_filename=services.clean_optional_string(
                    current_page_state.uploaded_filename,
                ),
                current_scattering_detector_value=None,
                current_fluorescence_detector_value=None,
                runtime_config_data=runtime_config_data
                if isinstance(runtime_config_data, dict)
                else None,
                logger=logger,
            )

            next_page_state = current_page_state.update(
                uploaded_fcs_path=upload_state.uploaded_fcs_path,
                uploaded_filename=upload_state.uploaded_filename,
                peak_lines_payload=build_empty_peak_lines_payload(),
                fluorescence_peak_lines=[],
                fluorescence_histogram_payload=None,
                fluorescence_source_channel=None,
                status_message="",
            )

            logger.debug(
                "handle_upload returning uploaded_fcs_path=%r uploaded_filename=%r",
                upload_state.uploaded_fcs_path,
                upload_state.uploaded_filename,
            )

            return (
                next_page_state.to_dict(),
                upload_state.runtime_config_data,
            )