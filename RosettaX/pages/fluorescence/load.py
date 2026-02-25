from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import base64
import tempfile

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages.runtime_config import get_runtime_config


@dataclass(frozen=True)
class LoadResult:
    """
    Container for all Dash outputs of the load callback.

    This keeps the callback return logic stable and makes the Output ordering explicit.
    """

    uploaded_fcs_path_store: Any = dash.no_update
    upload_saved_as: Any = dash.no_update
    scattering_detector_options: Any = dash.no_update
    scattering_detector_value: Any = dash.no_update
    fluorescence_detector_options: Any = dash.no_update
    fluorescence_detector_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert to the tuple expected by Dash multi output callbacks.

        Returns
        -------
        tuple
            (uploaded_fcs_path_store,
             upload_saved_as,
             scattering_detector_options,
             scattering_detector_value,
             fluorescence_detector_options,
             fluorescence_detector_value)
        """
        return (
            self.uploaded_fcs_path_store,
            self.upload_saved_as,
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

    def _load_get_layout(self) -> dbc.Card:
        """
        Build the layout for the load section and inject an initial file path store.
        """
        runtime_config = get_runtime_config()

        widget = dcc.Upload(
            id=self.ids.Load.upload,
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
                            id=self.ids.Load.fcs_path_store,
                            data=runtime_config.fcs_file_path,
                            storage_type="memory",
                        ),
                        widget,
                        html.Div(id=self.ids.Load.upload_filename),
                        html.Div(id=self.ids.Load.upload_saved_as),
                    ],
                    style=self.card_body_scroll,
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

        out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        out_path.write_bytes(raw)
        return str(out_path)

    def _load_register_callbacks(self) -> None:
        """
        Register callbacks for:
        - showing filename
        - loading from upload or CLI path
        """

        @callback(
            Output(self.ids.Load.upload_filename, "children"),
            Input(self.ids.Load.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_filename(name: Any) -> str:
            return f"Selected file: {name}" if name else ""

        @callback(
            Output(self.ids.Load.uploaded_fcs_path_store, "data"),
            Output(self.ids.Load.upload_saved_as, "children"),
            Output(self.ids.Scattering.detector_dropdown, "options"),
            Output(self.ids.Scattering.detector_dropdown, "value"),
            Output(self.ids.Fluorescence.detector_dropdown, "options"),
            Output(self.ids.Fluorescence.detector_dropdown, "value"),
            Input(self.ids.Load.upload, "contents"),
            Input(self.ids.Load.fcs_path_store, "data"),
            State(self.ids.Load.upload, "filename"),
            State(self.ids.Scattering.detector_dropdown, "value"),
            State(self.ids.Fluorescence.detector_dropdown, "value"),
            prevent_initial_call=False,
        )
        def load_file(
            contents: Any,
            initial_fcs_path: Any,
            filename: Any,
            current_scatter_value: Any,
            current_fluorescence_value: Any,
        ) -> tuple:

            runtime_config = get_runtime_config()

            selected_path: Optional[str] = None
            status_message: str = ""

            # Upload mode
            if contents and filename:
                try:
                    selected_path = self.write_upload_to_tempfile(
                        contents=str(contents),
                        filename=str(filename),
                    )
                    status_message = f"Saved as: {selected_path}"
                except Exception as exc:
                    return LoadResult(
                        upload_saved_as=f"Failed to save file: {exc}",
                        scattering_detector_options=[],
                        scattering_detector_value=None,
                        fluorescence_detector_options=[],
                        fluorescence_detector_value=None,
                    ).to_tuple()

            # CLI path mode
            elif isinstance(initial_fcs_path, str) and initial_fcs_path.strip():
                selected_path = initial_fcs_path.strip()
                status_message = f"Loaded from CLI path: {selected_path}"

            else:
                return LoadResult(
                    upload_saved_as="No file loaded.",
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                self.backend = BackEnd(selected_path)
            except Exception as exc:
                return LoadResult(
                    upload_saved_as=f"Failed to initialize backend: {exc}",
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            try:
                channels = self.file_state.options_from_file(selected_path)
            except Exception as exc:
                return LoadResult(
                    uploaded_fcs_path_store=selected_path,
                    upload_saved_as=f"{status_message}, but could not read: {exc}",
                    scattering_detector_options=[],
                    scattering_detector_value=None,
                    fluorescence_detector_options=[],
                    fluorescence_detector_value=None,
                ).to_tuple()

            scatter_options = list(channels.scatter_options or [])
            fluorescence_options = list(channels.fluorescence_options or [])

            # Scattering selection (automatic only)
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

            # Fluorescence selection (CLI preferred)
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
                upload_saved_as=status_message,
                scattering_detector_options=scatter_options,
                scattering_detector_value=scatter_value,
                fluorescence_detector_options=fluorescence_options,
                fluorescence_detector_value=fluorescence_value,
            ).to_tuple()

    @staticmethod
    def _pick_dropdown_value(
        *,
        preferred_value: Optional[str],
        current_value: Optional[str],
        options: list[dict[str, str]],
    ) -> Optional[str]:

        allowed = {str(o.get("value")) for o in options if "value" in o}

        if preferred_value is not None and str(preferred_value) in allowed:
            return str(preferred_value)

        if current_value is not None and str(current_value) in allowed:
            return str(current_value)

        if options:
            return str(options[0].get("value"))

        return None