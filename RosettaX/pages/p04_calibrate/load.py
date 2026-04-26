
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import base64
import tempfile

import dash
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.utils.reader import FCSFile
from RosettaX.pages.calibrate.ids import Ids

@dataclass(frozen=True)
class ApplyLoadResult:
    uploaded_fcs_path_store: Any = dash.no_update
    upload_saved_as: Any = dash.no_update
    channel_options: Any = dash.no_update
    channel_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.uploaded_fcs_path_store,
            self.upload_saved_as,
            self.channel_options,
            self.channel_value,
        )

class ApplyCalibrationLoadMixin:
    ids: Ids

    @staticmethod
    def write_upload_to_tempfile(*, contents: str, filename: str) -> str:
        _header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)

        suffix = Path(filename).suffix or ".bin"
        tmp_dir = Path(tempfile.gettempdir()) / "rosettax_uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        out_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        out_path.write_bytes(raw)
        return str(out_path)

    @staticmethod
    def _channel_options_from_file(*, file_path: str) -> list[dict[str, str]]:
        try:
            with FCSFile(Path(file_path), writable=False) as fcs:
                names: list[str] = []

                if hasattr(fcs, "channels") and isinstance(getattr(fcs, "channels"), (list, tuple)):
                    names = [str(x) for x in getattr(fcs, "channels")]
                elif hasattr(fcs, "channel_names") and isinstance(getattr(fcs, "channel_names"), (list, tuple)):
                    names = [str(x) for x in getattr(fcs, "channel_names")]
                elif hasattr(fcs, "get_channel_names"):
                    names = [str(x) for x in fcs.get_channel_names()]

            names = [n for n in names if n]
            return [{"label": n, "value": n} for n in names]
        except Exception:
            return []

    @staticmethod
    def _pick_dropdown_value(
        *,
        current_value: Optional[str],
        options: list[dict[str, str]],
    ) -> Optional[str]:
        allowed = {str(o.get("value")) for o in options if "value" in o}

        if current_value is not None and str(current_value) in allowed:
            return str(current_value)

        if options:
            return str(options[0].get("value"))

        return None

    def _load_get_layout(self) -> html.Div:
        return html.Div(
            [
                dcc.Store(
                    id=self.ids.Load.uploaded_fcs_path_store,
                    data=None,
                    storage_type="session",
                ),
                dcc.Upload(
                    id=self.ids.Load.upload,
                    children=html.Div(["Drag and drop or ", html.A("select a file")]),
                    multiple=False,
                    style=styling.UPLOAD if hasattr(styling, "UPLOAD") else {
                        "width": "100%",
                        "height": "46px",
                        "lineHeight": "46px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "6px",
                        "textAlign": "center",
                        "cursor": "pointer",
                    },
                    accept=".fcs",
                ),
                html.Div("", id=self.ids.Load.upload_filename, style={"marginTop": "8px", "opacity": 0.85}),
                html.Div("", id=self.ids.Load.upload_saved_as, style={"marginTop": "6px", "opacity": 0.85}),
            ]
        )

    def _load_register_callbacks(self) -> None:
        @callback(
            Output(self.ids.Load.upload_filename, "children"),
            Input(self.ids.Load.upload, "filename"),
            prevent_initial_call=True,
        )
        def _show_filename(name: Any) -> str:
            return f"Selected file: {name}" if name else ""

        @callback(
            Output(self.ids.Load.uploaded_fcs_path_store, "data"),
            Output(self.ids.Load.upload_saved_as, "children"),
            Output(self.ids.Apply.channel_dropdown, "options"),
            Output(self.ids.Apply.channel_dropdown, "value"),
            Input(self.ids.Load.upload, "contents"),
            State(self.ids.Load.upload, "filename"),
            State(self.ids.Apply.channel_dropdown, "value"),
            prevent_initial_call=True,
        )
        def _load_upload(contents: Any, filename: Any, current_channel_value: Any) -> tuple:
            if not contents or not filename:
                return ApplyLoadResult(
                    upload_saved_as="No file loaded.",
                    channel_options=[],
                    channel_value=None,
                ).to_tuple()

            try:
                selected_path = self.write_upload_to_tempfile(
                    contents=str(contents),
                    filename=str(filename),
                )
            except Exception as exc:
                return ApplyLoadResult(
                    upload_saved_as=f"Failed to save file: {exc}",
                    channel_options=[],
                    channel_value=None,
                ).to_tuple()

            options = self._channel_options_from_file(file_path=selected_path)
            value = self._pick_dropdown_value(
                current_value=str(current_channel_value) if current_channel_value else None,
                options=options,
            )

            return ApplyLoadResult(
                uploaded_fcs_path_store=selected_path,
                upload_saved_as=f"Saved as: {selected_path}",
                channel_options=options,
                channel_value=value,
            ).to_tuple()