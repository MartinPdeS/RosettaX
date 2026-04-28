# -*- coding: utf-8 -*-

import base64
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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
    """
    Input FCS file picker section.

    Responsibilities
    ----------------
    - Render the FCS upload widget.
    - Save uploaded FCS files to the local RosettaX upload directory.
    - Store saved FCS file paths in a Dash store.
    - Check multi file FCS consistency using ``FCSMultiFileConsistencyChecker``.
    - Display upload and consistency status.

    Development rule
    ----------------
    Programming errors must fail loudly. Missing IDs, missing checker classes,
    missing checker methods, malformed callback dependencies, and failed file
    writes are not swallowed.
    """

    def __init__(self, page) -> None:
        self.page = page
        self._validate_page_contract()

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
        self._validate_checks_contract()

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

            self._validate_upload_payload(
                contents_list=contents_list,
                filenames=filenames,
            )

            saved_paths = self._save_uploaded_files(
                contents_list=contents_list,
                filenames=filenames,
            )

            consistency_report = self._check_saved_files_consistency(
                saved_paths=saved_paths,
            )

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

    def _validate_page_contract(self) -> None:
        required_attributes = [
            "ids",
            "ids.FilePicker",
            "ids.FilePicker.upload",
            "ids.FilePicker.column_consistency_alert",
            "ids.Stores",
            "ids.Stores.uploaded_fcs_path_store",
        ]

        for required_attribute in required_attributes:
            current_object = self.page

            for attribute_name in required_attribute.split("."):
                if not hasattr(current_object, attribute_name):
                    raise AttributeError(
                        f"FilePicker requires page.{required_attribute}, "
                        f"but missing attribute {attribute_name!r} while resolving "
                        f"{required_attribute!r}."
                    )

                current_object = getattr(current_object, attribute_name)

    @staticmethod
    def _validate_checks_contract() -> None:
        if not hasattr(checks, "FCSMultiFileConsistencyChecker"):
            raise AttributeError(
                "RosettaX.utils.checks must expose FCSMultiFileConsistencyChecker. "
                "The old check_multifiles_consistency helper is no longer used here."
            )

        checker_class = checks.FCSMultiFileConsistencyChecker

        if not hasattr(checker_class, "check_multifiles_consistency"):
            raise AttributeError(
                "FCSMultiFileConsistencyChecker must define "
                "check_multifiles_consistency()."
            )

    @staticmethod
    def _validate_upload_payload(
        *,
        contents_list: list[str],
        filenames: list[str],
    ) -> None:
        if len(contents_list) != len(filenames):
            raise ValueError(
                "Upload payload is malformed because contents_list and filenames "
                f"have different lengths: {len(contents_list)} != {len(filenames)}."
            )

        for filename in filenames:
            if not str(filename).strip():
                raise ValueError("Upload payload contains an empty filename.")

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

        if not saved_paths:
            raise RuntimeError("No uploaded FCS files were saved.")

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

        if "," not in contents:
            raise ValueError(
                f"Uploaded file {filename!r} has malformed Dash contents payload."
            )

        _, encoded_payload = contents.split(",", 1)
        raw_bytes = base64.b64decode(encoded_payload, validate=True)

        original_path = Path(str(filename))
        safe_stem = original_path.stem.strip() or "uploaded_file"
        safe_suffix = original_path.suffix if original_path.suffix else ".fcs"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = self._upload_dir / f"{safe_stem}_{timestamp}{safe_suffix}"

        output_path.write_bytes(raw_bytes)

        if not output_path.exists():
            raise FileNotFoundError(
                f"Uploaded file was not written successfully: {output_path}"
            )

        if output_path.stat().st_size == 0:
            raise ValueError(
                f"Uploaded file was written but is empty: {output_path}"
            )

        logger.debug(
            "Saved uploaded file successfully to output_path=%r byte_count=%r",
            str(output_path),
            len(raw_bytes),
        )

        return output_path

    @staticmethod
    def _check_saved_files_consistency(
        *,
        saved_paths: list[Path],
    ) -> dict[str, Any]:
        checker = checks.FCSMultiFileConsistencyChecker(
            file_paths=[
                str(path)
                for path in saved_paths
            ]
        )

        consistency_report = checker.check_multifiles_consistency()

        if not isinstance(consistency_report, dict):
            raise TypeError(
                "FCSMultiFileConsistencyChecker.check_multifiles_consistency() "
                f"must return a dict, got {type(consistency_report).__name__}."
            )

        if "are_all_files_consistent" not in consistency_report:
            raise KeyError(
                "Consistency report is missing required key "
                "'are_all_files_consistent'."
            )

        return consistency_report

    def _build_success_alert_payload(
        self,
        *,
        saved_paths: list[Path],
        consistency_report: dict[str, Any],
    ) -> tuple[str, str, bool]:
        if not saved_paths:
            raise ValueError("Cannot build upload success payload without saved files.")

        if not consistency_report.get("are_all_files_consistent", True):
            mismatch_details = consistency_report.get("mismatch_details", [])

            if mismatch_details:
                preview = ", ".join(
                    str(detail)
                    for detail in mismatch_details[:3]
                )
            else:
                preview = "Uploaded files are inconsistent."

            return preview, "warning", True

        if len(saved_paths) == 1:
            return f"Uploaded 1 FCS file: {saved_paths[0].name}", "success", True

        return f"Uploaded {len(saved_paths)} FCS files.", "success", True