# -*- coding: utf-8 -*-

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from RosettaX.utils import checks


logger = logging.getLogger(__name__)


def build_upload_directory() -> Path:
    """
    Build and create the local upload directory.

    Returns
    -------
    Path
        Local upload directory used by the apply calibration file picker.
    """
    upload_directory = Path.home() / ".rosettax" / "uploads"

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.debug(
        "Resolved FilePicker upload_directory=%r",
        str(upload_directory),
    )

    return upload_directory


def validate_page_contract(
    *,
    page: Any,
) -> None:
    """
    Validate the page ID contract required by the file picker section.

    Programming errors must fail loudly. Missing IDs indicate an invalid page
    integration.
    """
    required_attributes = [
        "ids",
        "ids.FilePicker",
        "ids.FilePicker.upload",
        "ids.FilePicker.column_consistency_alert",
        "ids.Stores",
        "ids.Stores.uploaded_fcs_path_store",
    ]

    for required_attribute in required_attributes:
        current_object = page

        for attribute_name in required_attribute.split("."):
            if not hasattr(current_object, attribute_name):
                raise AttributeError(
                    f"FilePicker requires page.{required_attribute}, "
                    f"but missing attribute {attribute_name!r} while resolving "
                    f"{required_attribute!r}."
                )

            current_object = getattr(
                current_object,
                attribute_name,
            )


def validate_checks_contract() -> None:
    """
    Validate the FCS consistency checker contract.

    Programming errors must fail loudly. The file picker relies on the current
    ``FCSMultiFileConsistencyChecker`` API.
    """
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


def validate_upload_payload(
    *,
    contents_list: list[str],
    filenames: list[str],
) -> None:
    """
    Validate Dash upload payload consistency.
    """
    if len(contents_list) != len(filenames):
        raise ValueError(
            "Upload payload is malformed because contents_list and filenames "
            f"have different lengths: {len(contents_list)} != {len(filenames)}."
        )

    for filename in filenames:
        if not str(filename).strip():
            raise ValueError("Upload payload contains an empty filename.")


def save_uploaded_files(
    *,
    upload_directory: Path,
    contents_list: list[str],
    filenames: list[str],
) -> list[Path]:
    """
    Save all uploaded files.

    Parameters
    ----------
    upload_directory:
        Directory where uploaded files are written.
    contents_list:
        Dash upload contents payloads.
    filenames:
        Original upload filenames.

    Returns
    -------
    list[Path]
        Saved local file paths.
    """
    saved_paths: list[Path] = []

    for contents, filename in zip(
        contents_list,
        filenames,
        strict=False,
    ):
        saved_path = save_single_uploaded_file(
            upload_directory=upload_directory,
            contents=contents,
            filename=filename,
        )

        saved_paths.append(
            saved_path,
        )

    if not saved_paths:
        raise RuntimeError("No uploaded FCS files were saved.")

    return saved_paths


def save_single_uploaded_file(
    *,
    upload_directory: Path,
    contents: str,
    filename: str,
) -> Path:
    """
    Save one uploaded file to the local upload directory.
    """
    logger.debug(
        "save_single_uploaded_file called with filename=%r upload_directory=%r",
        filename,
        str(upload_directory),
    )

    if "," not in contents:
        raise ValueError(
            f"Uploaded file {filename!r} has malformed Dash contents payload."
        )

    _, encoded_payload = contents.split(
        ",",
        1,
    )

    raw_bytes = base64.b64decode(
        encoded_payload,
        validate=True,
    )

    original_path = Path(
        str(filename),
    )

    safe_stem = original_path.stem.strip() or "uploaded_file"
    safe_suffix = original_path.suffix if original_path.suffix else ".fcs"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f",
    )

    output_path = upload_directory / f"{safe_stem}_{timestamp}{safe_suffix}"

    output_path.write_bytes(
        raw_bytes,
    )

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


def check_saved_files_consistency(
    *,
    saved_paths: list[Path],
) -> dict[str, Any]:
    """
    Check uploaded FCS files for consistency.
    """
    validate_checks_contract()

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

    logger.debug(
        "check_saved_files_consistency returning consistency_report=%r",
        consistency_report,
    )

    return consistency_report


def build_success_alert_payload(
    *,
    saved_paths: list[Path],
    consistency_report: dict[str, Any],
) -> tuple[Any, str, bool]:
    """
    Build the upload success or warning alert payload.
    """
    if not saved_paths:
        raise ValueError("Cannot build upload success payload without saved files.")

    if not consistency_report.get(
        "are_all_files_consistent",
        True,
    ):
        mismatch_details = consistency_report.get(
            "mismatch_details",
            [],
        )

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