# -*- coding: utf-8 -*-

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages.calibrate.ids import Ids


@dataclass(frozen=True)
class FilePickerResult:
    """
    Container for the Dash outputs of the file upload callback.
    """

    uploaded_fcs_path_store: Any = dash.no_update
    upload_status: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (self.uploaded_fcs_path_store, self.upload_status)


class FilePickerSection:
    def __init__(self) -> None:
        self._upload_dir = Path.home() / ".rosettax" / "uploads"
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("1. Upload input FCS"),
                dbc.CardBody(
                    [
                        dcc.Upload(
                            id=Ids.FilePicker.upload,
                            children=html.Div(["Drag and drop or ", html.A("select an .fcs file")]),
                            multiple=False,
                            style={
                                "width": "100%",
                                "height": "46px",
                                "lineHeight": "46px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "6px",
                                "textAlign": "center",
                                "cursor": "pointer",
                            },
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "No file loaded.",
                            id=Ids.FilePicker.upload_status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                        dcc.Store(id=Ids.Stores.uploaded_fcs_path_store),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(Ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Output(Ids.FilePicker.upload_status, "children"),
            dash.Input(Ids.FilePicker.upload, "contents"),
            dash.State(Ids.FilePicker.upload, "filename"),
            prevent_initial_call=True,
        )
        def save_uploaded_file(contents: Optional[str], filename: Optional[str]) -> tuple:
            if not contents or not filename:
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    upload_status="No file loaded.",
                ).to_tuple()

            name = str(filename)
            suffix = Path(name).suffix.lower()
            if suffix != ".fcs":
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    upload_status="Please upload a .fcs file.",
                ).to_tuple()

            try:
                header, b64data = contents.split(",", 1)
                blob = base64.b64decode(b64data.encode("utf-8"), validate=True)
            except Exception as exc:
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    upload_status=f"Upload decode failed: {type(exc).__name__}: {exc}",
                ).to_tuple()

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{Path(name).stem}_{stamp}.fcs"
            out_path = self._upload_dir / safe_name

            try:
                out_path.write_bytes(blob)
            except Exception as exc:
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    upload_status=f"Could not write file: {type(exc).__name__}: {exc}",
                ).to_tuple()

            return FilePickerResult(
                uploaded_fcs_path_store=str(out_path),
                upload_status=f"Loaded file: {out_path.name}",
            ).to_tuple()