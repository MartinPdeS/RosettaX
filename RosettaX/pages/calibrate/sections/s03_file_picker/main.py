# -*- coding: utf-8 -*-

import base64
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import checks


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FilePickerResult:
    """
    Container for the Dash outputs of the file upload callback.
    """

    uploaded_fcs_path_store: Any = dash.no_update
    alert_children: Any = dash.no_update
    alert_color: Any = dash.no_update
    alert_is_open: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.uploaded_fcs_path_store,
            self.alert_children,
            self.alert_color,
            self.alert_is_open,
        )


class FilePicker:
    def __init__(self, page) -> None:
        self.page = page
        self._upload_dir = Path.home() / ".rosettax" / "uploads"
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("1. Upload input FCS")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_upload_widget(),
                self._build_spacing(),
                self._build_alert(),
                self._build_upload_store(),
            ]
        )

    @staticmethod
    def _build_spacing(height: str = "10px") -> dash.html.Div:
        return dash.html.Div(style={"height": height})

    def _build_upload_widget(self) -> dash.dcc.Upload:
        return dash.dcc.Upload(
            id=self.page.ids.FilePicker.upload,
            children=dash.html.Div(
                [
                    "Drag and drop or ",
                    dash.html.A("select one or more .fcs files"),
                ]
            ),
            multiple=True,
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
        )

    def _build_alert(self) -> dbc.Alert:
        return dbc.Alert(
            "Upload one or more FCS files.",
            id=self.page.ids.FilePicker.column_consistency_alert,
            color="secondary",
            is_open=True,
            style={"marginBottom": "0px"},
        )

    def _build_upload_store(self) -> dash.dcc.Store:
        return dash.dcc.Store(
            id=self.page.ids.Stores.uploaded_fcs_path_store,
            storage_type="session",
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Output(self.page.ids.FilePicker.column_consistency_alert, "children"),
            dash.Output(self.page.ids.FilePicker.column_consistency_alert, "color"),
            dash.Output(self.page.ids.FilePicker.column_consistency_alert, "is_open"),
            dash.Input(self.page.ids.FilePicker.upload, "contents"),
            dash.State(self.page.ids.FilePicker.upload, "filename"),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents_list: Optional[list[str]],
            filenames: Optional[list[str]],
        ) -> tuple:
            logger.debug(
                "handle_upload called with contents_count=%r filenames=%r",
                None if contents_list is None else len(contents_list),
                filenames,
            )

            if not contents_list or not filenames:
                logger.debug("Upload was cancelled or no files were provided.")
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    alert_children="Upload canceled.",
                    alert_color="danger",
                    alert_is_open=True,
                ).to_tuple()

            try:
                saved_paths = self._save_uploaded_files(
                    contents_list=contents_list,
                    filenames=filenames,
                )
            except Exception:
                logger.exception("Failed while saving uploaded FCS files.")
                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    alert_children="Failed to save uploaded FCS files.",
                    alert_color="danger",
                    alert_is_open=True,
                ).to_tuple()


            try:
                consistency_report = checks.check_multifiles_consistency(
                    [str(path) for path in saved_paths]
                )
            except Exception:
                logger.exception("Failed while checking uploaded FCS files consistency.")
                consistency_report = {
                    "are_all_files_consistent": False,
                    "mismatch_details": [
                        "Could not verify whether all uploaded FCS files are consistent."
                    ],
                }

            except Exception:
                logger.exception("Failed while checking uploaded FCS column consistency.")
                consistency_message = "Could not verify whether all uploaded FCS files share the same list of columns."
                consistency_is_open = True

            alert_children, alert_color, alert_is_open = self._build_success_alert_payload(
                saved_paths=saved_paths,
                consistency_report=consistency_report,
            )

            logger.debug(
                "Upload handling succeeded with saved_paths=%r alert_color=%r alert_is_open=%r",
                [str(path) for path in saved_paths],
                alert_color,
                alert_is_open,
            )

            return FilePickerResult(
                uploaded_fcs_path_store=[str(path) for path in saved_paths],
                alert_children=alert_children,
                alert_color=alert_color,
                alert_is_open=alert_is_open,
            ).to_tuple()

    def _save_uploaded_files(
        self,
        *,
        contents_list: list[str],
        filenames: list[str],
    ) -> list[Path]:
        saved_paths: list[Path] = []

        for contents, filename in zip(contents_list, filenames):
            saved_path = self._save_single_uploaded_file(
                contents=contents,
                filename=filename,
            )
            saved_paths.append(saved_path)

        return saved_paths

    def _save_single_uploaded_file(
        self,
        *,
        contents: str,
        filename: str,
    ) -> Path:
        logger.debug(
            "_save_single_uploaded_file called with filename=%r",
            filename,
        )

        _, encoded_payload = contents.split(",", 1)
        raw_bytes = base64.b64decode(encoded_payload)

        original_path = Path(str(filename))
        safe_stem = original_path.stem.strip() or "uploaded_file"
        safe_suffix = original_path.suffix if original_path.suffix else ".fcs"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = self._upload_dir / f"{safe_stem}_{timestamp}{safe_suffix}"
        output_path.write_bytes(raw_bytes)

        logger.debug(
            "Saved uploaded file successfully to output_path=%r byte_count=%r",
            str(output_path),
            len(raw_bytes),
        )

        return output_path

    def _build_success_alert_payload(
        self,
        *,
        saved_paths: list[Path],
        consistency_report: dict[str, Any],
    ) -> tuple[str, str, bool]:
        if not consistency_report.get("are_all_files_consistent", True):
            mismatch_details = consistency_report.get("mismatch_details", [])
            preview = ", ".join(mismatch_details[:3]) if mismatch_details else "Uploaded files are inconsistent."
            return preview, "warning", True

        if not saved_paths:
            return "Upload canceled.", "danger", True

        if len(saved_paths) == 1:
            return f'Uploaded 1 FCS file: {saved_paths[0].name}', "success", True

        return f"Uploaded {len(saved_paths)} FCS files.", "success", True
