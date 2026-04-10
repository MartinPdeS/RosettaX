from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import base64
import tempfile

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence import service
from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.utils.runtime_config import RuntimeConfig


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
        self.file_state = service.FileStateRefresher()

    @property
    def uploaded_fcs_filename_store_id(self) -> str:
        """
        Auxiliary session store used to preserve the original uploaded filename.

        This avoids having to modify the page ids class just to keep one extra
        piece of session state.
        """
        return f"{self.page.ids.Load.uploaded_fcs_path_store}-filename"

    def get_layout(self) -> dbc.Card:
        """
        Build the layout for the load section.
        """
        runtime_config = RuntimeConfig()

        initial_fcs_path = runtime_config.fcs_file_path
        initial_filename = Path(initial_fcs_path).name if initial_fcs_path else ""

        upload_widget = dcc.Upload(
            id=self.page.ids.Load.upload,
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
                            id=self.page.ids.Load.uploaded_fcs_path_store,
                            data=initial_fcs_path,
                            storage_type="session",
                        ),
                        dcc.Store(
                            id=self.uploaded_fcs_filename_store_id,
                            data=initial_filename,
                            storage_type="session",
                        ),
                        upload_widget,
                        html.Div(id=self.page.ids.Load.upload_filename),
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
        _header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        temporary_directory = Path(tempfile.gettempdir()) / "rosettax_uploads"
        temporary_directory.mkdir(parents=True, exist_ok=True)

        output_path = temporary_directory / f"{next(tempfile._get_candidate_names())}{suffix}"
        output_path.write_bytes(raw)
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

        if preferred_value is not None and str(preferred_value) in allowed_values:
            return str(preferred_value)

        if current_value is not None and str(current_value) in allowed_values:
            return str(current_value)

        if options:
            return str(options[0].get("value"))

        return None

    @staticmethod
    def _build_loaded_filename_label(display_filename: Optional[str]) -> str:
        if isinstance(display_filename, str) and display_filename.strip():
            return f"Loaded file: {display_filename.strip()}"
        return ""

    def _register_callbacks(self) -> None:
        """
        Register callbacks for:
        - loading from upload or restored session path
        - preserving the loaded filename for the whole session
        - initializing detector dropdowns
        """

        @callback(
            Output(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            Output(self.uploaded_fcs_filename_store_id, "data"),
            Output(self.page.ids.Load.upload_filename, "children"),
            Output(self.page.ids.Scattering.detector_dropdown, "options"),
            Output(self.page.ids.Scattering.detector_dropdown, "value"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "options"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "value"),
            Input(self.page.ids.Load.upload, "contents"),
            Input(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            State(self.page.ids.Load.upload, "filename"),
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
            selected_path: Optional[str] = None
            display_filename: str = ""

            if contents and uploaded_filename:
                try:
                    selected_path = self.write_upload_to_tempfile(
                        contents=str(contents),
                        filename=str(uploaded_filename),
                    )
                    display_filename = str(uploaded_filename)

                    print(f"Selected file: {uploaded_filename}")
                    print(f"Saved as: {selected_path}")

                except Exception as error:
                    print(f"Failed to save file: {error}")
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
                selected_path = stored_fcs_path.strip()

                if isinstance(stored_filename, str) and stored_filename.strip():
                    display_filename = stored_filename.strip()
                else:
                    display_filename = Path(selected_path).name

                print(f"Loaded from session or runtime config path: {selected_path}")

            else:
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

            except Exception as error:
                print(f"Failed to initialize backend: {error}")
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
                channels = self.file_state.options_from_file(selected_path)

            except Exception as error:
                print(f"Loaded file but could not read channels: {error}")
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

            scatter_options = list(channels.scatter_options or [])
            fluorescence_options = list(channels.fluorescence_options or [])

            scatter_value = self._pick_dropdown_value(
                preferred_value=runtime_config.fluorescence_page_scattering_detector,
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
                preferred_value=runtime_config.fluorescence_page_fluorescence_detector,
                current_value=str(current_fluorescence_value) if current_fluorescence_value else None,
                options=fluorescence_options,
            )
            if fluorescence_value is None:
                fluorescence_value = self._pick_dropdown_value(
                    preferred_value=None,
                    current_value=str(channels.fluorescence_value) if channels.fluorescence_value else None,
                    options=fluorescence_options,
                )

            return LoadResult(
                uploaded_fcs_path_store=selected_path,
                uploaded_fcs_filename_store=display_filename,
                upload_filename_children=self._build_loaded_filename_label(display_filename),
                scattering_detector_options=scatter_options,
                scattering_detector_value=scatter_value,
                fluorescence_detector_options=fluorescence_options,
                fluorescence_detector_value=fluorescence_value,
            ).to_tuple()