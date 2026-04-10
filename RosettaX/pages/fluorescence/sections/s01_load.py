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
    """
    Section 1: Load an FCS file and initialize the detector dropdowns.

    Supported modes
    ---------------
    1. Upload mode
       User uploads an FCS file through the UI.

    2. CLI path mode
       An FCS file path is provided via runtime configuration and loaded on startup.

    This section is the sole owner of detector dropdown Outputs.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.file_state = service.FileStateRefresher()

    def get_layout(self) -> dbc.Card:
        """
        Build the layout for the load section and inject an initial file path store.
        """
        runtime_config = RuntimeConfig()

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
                            id=self.page.ids.Load.fcs_path_store,
                            data=runtime_config.fcs_file_path,
                            storage_type="memory",
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
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        output_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
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

    def _register_callbacks(self) -> None:
        """
        Register callbacks for:
        - showing filename in the GUI
        - loading from upload or CLI path
        - printing terminal diagnostics
        """

        @callback(
            Output(self.page.ids.Load.upload_filename, "children"),
            Input(self.page.ids.Load.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(filename: Any) -> str:
            if filename:
                print(f"Selected file: {filename}")
                return str(filename)

            return ""

        @callback(
            Output(self.page.ids.Load.uploaded_fcs_path_store, "data"),
            Output(self.page.ids.Scattering.detector_dropdown, "options"),
            Output(self.page.ids.Scattering.detector_dropdown, "value"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "options"),
            Output(self.page.ids.Fluorescence.detector_dropdown, "value"),
            Input(self.page.ids.Load.upload, "contents"),
            Input(self.page.ids.Load.fcs_path_store, "data"),
            State(self.page.ids.Load.upload, "filename"),
            State(self.page.ids.Scattering.detector_dropdown, "value"),
            State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=False,
        )
        def load_file(
            contents: Any,
            initial_fcs_path: Any,
            filename: Any,
            current_scatter_value: Any,
            current_fluorescence_value: Any,
        ) -> tuple:
            selected_path: Optional[str] = None

            if contents and filename:
                try:
                    selected_path = self.write_upload_to_tempfile(
                        contents=str(contents),
                        filename=str(filename),
                    )
                    print(f"Selected file: {filename}")
                    print(f"Saved as: {selected_path}")

                except Exception as exc:
                    print(f"Failed to save file: {exc}")
                    return LoadResult(
                        scattering_detector_options=[],
                        scattering_detector_value=None,
                        fluorescence_detector_options=[],
                        fluorescence_detector_value=None,
                    ).to_tuple()

            elif isinstance(initial_fcs_path, str) and initial_fcs_path.strip():
                selected_path = initial_fcs_path.strip()
                print(f"Loaded from CLI path: {selected_path}")

            else:
                return LoadResult(
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                self.page.backend = BackEnd(selected_path)

            except Exception as exc:
                print(f"Failed to initialize backend: {exc}")
                return LoadResult(
                    uploaded_fcs_path_store=selected_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                channels = self.file_state.options_from_file(selected_path)

            except Exception as exc:
                print(f"Loaded file but could not read channels: {exc}")
                return LoadResult(
                    uploaded_fcs_path_store=selected_path,
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            scatter_options = list(channels.scatter_options or [])
            fluorescence_options = list(channels.fluorescence_options or [])

            scatter_value = self._pick_dropdown_value(
                preferred_value=None,
                current_value=str(current_scatter_value) if current_scatter_value else None,
                options=scatter_options,
            )
            if scatter_value is None:
                scatter_value = self._pick_dropdown_value(
                    preferred_value=None,
                    current_value=str(channels.scatter_value) if channels.scatter_value else None,
                    options=scatter_options,
                )

            runtime_config = RuntimeConfig()

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
                scattering_detector_options=scatter_options,
                scattering_detector_value=scatter_value,
                fluorescence_detector_options=fluorescence_options,
                fluorescence_detector_value=fluorescence_value,
            ).to_tuple()