# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging

import base64
import tempfile

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.utils import service
from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadResult:
    uploaded_fcs_path_store: Any = dash.no_update
    uploaded_fcs_filename_store: Any = dash.no_update
    upload_filename_children: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.uploaded_fcs_path_store,
            self.uploaded_fcs_filename_store,
            self.upload_filename_children,
            self.scattering_detector_options,
            self.scattering_detector_value,
            self.fluorescence_detector_options,
            self.fluorescence_detector_value,
        )


class LoadSection:
    """
    Section 1: Load an FCS file and initialize the detector dropdowns.

    Supported modes
    ---------------
    1. Upload mode
       User uploads an FCS file through the UI.

    2. Session restore mode
       The previously loaded FCS file path is restored from a session store.

    3. Runtime config mode
       An FCS file path is provided via runtime configuration and loaded on startup.

    This section is the sole owner of detector dropdown Outputs.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized LoadSection with page=%r", page)

    @property
    def uploaded_fcs_filename_store_id(self) -> str:
        """
        Auxiliary session store used to preserve the original uploaded filename.

        This avoids having to modify the page ids class just to keep one extra
        piece of session state.
        """
        store_id = f"{self.page.ids.Upload.uploaded_fcs_path_store}-filename"
        logger.debug("Resolved uploaded_fcs_filename_store_id=%r", store_id)
        return store_id

    def get_layout(self) -> dbc.Card:
        """
        Build the layout for the load section.
        """
        runtime_config = RuntimeConfig()

        initial_fcs_path = runtime_config.Default.fcs_file_path
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        logger.debug(
            "Building load section layout with initial_fcs_path=%r initial_filename=%r",
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
        """
        Decode a Dash upload payload and persist it to a temporary file.
        """
        logger.debug(
            "write_upload_to_tempfile called with filename=%r contents_prefix=%r",
            filename,
            contents[:64] if isinstance(contents, str) else contents,
        )

        header, b64data = contents.split(",", 1)
        logger.debug("Parsed upload header=%r", header)

        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
        temporary_directory.mkdir(parents=True, exist_ok=True)

        output_path = temporary_directory / f"{next(tempfile._get_candidate_names())}{suffix}"
        output_path.write_bytes(raw)

        logger.debug(
            "Upload written successfully to output_path=%r byte_count=%r",
            str(output_path),
            len(raw),
        )
        return str(output_path)

    @staticmethod
    def _pick_dropdown_value(
        *,
        preferred_value: Optional[str],
        current_value: Optional[str],
        options: list[dict[str, str]],
    ) -> Optional[str]:
        allowed_values = {
            str(option.get("value"))
            for option in options
            if "value" in option
        }

        logger.debug(
            "_pick_dropdown_value called with preferred_value=%r current_value=%r allowed_values=%r",
            preferred_value,
            current_value,
            allowed_values,
        )

        if preferred_value is not None and str(preferred_value) in allowed_values:
            resolved = str(preferred_value)
            logger.debug("_pick_dropdown_value selected preferred_value=%r", resolved)
            return resolved

        if current_value is not None and str(current_value) in allowed_values:
            resolved = str(current_value)
            logger.debug("_pick_dropdown_value selected current_value=%r", resolved)
            return resolved

        if options:
            resolved = str(options[0].get("value"))
            logger.debug("_pick_dropdown_value fell back to first option value=%r", resolved)
            return resolved

        logger.debug("_pick_dropdown_value found no valid options and returned None")
        return None

    @staticmethod
    def _build_loaded_filename_label(display_filename: Optional[str]) -> str:
        if isinstance(display_filename, str) and display_filename.strip():
            label = f"Loaded file: {display_filename.strip()}"
            logger.debug(
                "_build_loaded_filename_label built label=%r from display_filename=%r",
                label,
                display_filename,
            )
            return label

        logger.debug(
            "_build_loaded_filename_label received empty display_filename=%r and returned empty label",
            display_filename,
        )
        return ""

    def register_callbacks(self) -> None:
        """
        Register callbacks for:
        - loading from upload or restored session path
        - preserving the loaded filename for the whole session
        - initializing detector dropdowns
        """
        logger.debug("Registering load section callbacks.")

        @callback(
            Output(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            Output(self.uploaded_fcs_filename_store_id, "data"),
            Output(self.page.ids.Upload.upload_filename, "children"),
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
        def load_file(
            contents: Any,
            stored_fcs_path: Any,
            uploaded_filename: Any,
            stored_filename: Any,
            current_scatter_value: Any,
            current_fluorescence_value: Any,
        ) -> tuple:
            logger.debug(
                "load_file called with contents_type=%s stored_fcs_path=%r uploaded_filename=%r "
                "stored_filename=%r current_scatter_value=%r current_fluorescence_value=%r",
                type(contents).__name__,
                stored_fcs_path,
                uploaded_filename,
                stored_filename,
                current_scatter_value,
                current_fluorescence_value,
            )

            selected_path: Optional[str] = None
            display_filename: str = ""

            if contents and uploaded_filename:
                logger.debug("load_file entered upload mode.")
                try:
                    selected_path = self.write_upload_to_tempfile(
                        contents=str(contents),
                        filename=str(uploaded_filename),
                    )
                    display_filename = str(uploaded_filename)

                    logger.debug(
                        "Upload mode succeeded with uploaded_filename=%r selected_path=%r",
                        uploaded_filename,
                        selected_path,
                    )

                except Exception:
                    logger.exception(
                        "Failed to save uploaded file with uploaded_filename=%r",
                        uploaded_filename,
                    )
                    return LoadResult(
                        uploaded_fcs_path_store=None,
                        uploaded_fcs_filename_store="",
                        upload_filename_children="",
                        scattering_detector_options=[],
                        scattering_detector_value=None,
                        fluorescence_detector_options=[],
                        fluorescence_detector_value=None,
                    ).to_tuple()

            elif isinstance(stored_fcs_path, str) and stored_fcs_path.strip():
                logger.debug("load_file entered session restore or runtime config mode.")
                selected_path = stored_fcs_path.strip()

                if isinstance(stored_filename, str) and stored_filename.strip():
                    display_filename = stored_filename.strip()
                else:
                    display_filename = Path(selected_path).name

                logger.debug(
                    "Restored selected_path=%r display_filename=%r from store/runtime config",
                    selected_path,
                    display_filename,
                )

            else:
                logger.debug("load_file found no upload contents and no stored path. Returning empty LoadResult.")
                return LoadResult(
                    uploaded_fcs_path_store=None,
                    uploaded_fcs_filename_store="",
                    upload_filename_children="",
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                self.page.backend = BackEnd(selected_path)
                logger.debug("BackEnd initialized successfully for selected_path=%r", selected_path)

            except Exception:
                logger.exception(
                    "Failed to initialize BackEnd for selected_path=%r",
                    selected_path,
                )
                return LoadResult(
                    uploaded_fcs_path_store=selected_path,
                    uploaded_fcs_filename_store=display_filename,
                    upload_filename_children=self._build_loaded_filename_label(display_filename),
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                channels = service.build_channel_options_from_file(selected_path)
                logger.debug("Channel extraction succeeded for selected_path=%r channels=%r", selected_path, channels)

            except Exception:
                logger.exception(
                    "Loaded file but failed to extract channels from selected_path=%r",
                    selected_path,
                )
                return LoadResult(
                    uploaded_fcs_path_store=selected_path,
                    uploaded_fcs_filename_store=display_filename,
                    upload_filename_children=self._build_loaded_filename_label(display_filename),
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            runtime_config = RuntimeConfig()
            runtime_config.update(fcs_file_path=selected_path)
            logger.debug("Updated runtime config with fcs_file_path=%r", selected_path)

            scatter_options = list(channels.scatter_options or [])
            fluorescence_options = list(channels.secondary_options or [])

            logger.debug(
                "Resolved scatter_options_count=%r fluorescence_options_count=%r",
                len(scatter_options),
                len(fluorescence_options),
            )

            scatter_value = self._pick_dropdown_value(
                preferred_value=runtime_config.Default.fluorescence_page_scattering_detector,
                current_value=str(current_scatter_value) if current_scatter_value else None,
                options=scatter_options,
            )
            if scatter_value is None:
                scatter_value = self._pick_dropdown_value(
                    preferred_value=None,
                    current_value=str(channels.scatter_value) if channels.scatter_value else None,
                    options=scatter_options,
                )

            fluorescence_value = self._pick_dropdown_value(
                preferred_value=runtime_config.Default.fluorescence_page_fluorescence_detector,
                current_value=str(current_fluorescence_value) if current_fluorescence_value else None,
                options=fluorescence_options,
            )
            if fluorescence_value is None:
                fluorescence_value = self._pick_dropdown_value(
                    preferred_value=None,
                    current_value=str(channels.fluorescence_value) if channels.fluorescence_value else None,
                    options=fluorescence_options,
                )

            logger.debug(
                "Final dropdown resolution selected scatter_value=%r fluorescence_value=%r",
                scatter_value,
                fluorescence_value,
            )

            result = LoadResult(
                uploaded_fcs_path_store=selected_path,
                uploaded_fcs_filename_store=display_filename,
                upload_filename_children=self._build_loaded_filename_label(display_filename),
                scattering_detector_options=scatter_options,
                scattering_detector_value=scatter_value,
                fluorescence_detector_options=fluorescence_options,
                fluorescence_detector_value=fluorescence_value,
            )

            logger.debug("load_file returning LoadResult=%r", result)
            return result.to_tuple()