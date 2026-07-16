# -*- coding: utf-8 -*-

import io
import zipfile
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from RosettaX.utils.checks import FCSMultiFileConsistencyChecker
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.upload.services import (
    DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
    save_uploaded_file,
    validate_upload_filename,
)


DEFAULT_UPLOAD_DIRECTORY = Path.home() / ".rosettax" / "uploads" / "fcs-slicer"


def normalize_multiple_upload_values(value: Any) -> list[str]:
    """Normalize a scalar or multi-file Dash upload value to a string list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def save_uploaded_batch(
    *,
    contents: Any,
    filenames: Any,
    upload_directory: Path = DEFAULT_UPLOAD_DIRECTORY,
) -> tuple[list[Path], list[str]]:
    """Validate and save one Dash multi-file upload in a batch-specific folder."""
    contents_list = normalize_multiple_upload_values(contents)
    filename_list = normalize_multiple_upload_values(filenames)

    if not contents_list:
        raise ValueError("Select at least one FCS file.")
    if len(contents_list) != len(filename_list):
        raise ValueError("The uploaded file payload is malformed.")

    batch_directory = Path(upload_directory) / uuid4().hex
    saved_paths: list[Path] = []
    safe_filenames: list[str] = []
    used_storage_filenames: set[str] = set()

    for index, (file_contents, filename) in enumerate(
        zip(contents_list, filename_list, strict=True),
        start=1,
    ):
        safe_filename = validate_upload_filename(
            filename or f"uploaded_file_{index}.fcs",
            allowed_extensions=DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
        )
        storage_filename = safe_filename
        if storage_filename in used_storage_filenames:
            safe_path = Path(safe_filename)
            storage_filename = f"{safe_path.stem}_{index}{safe_path.suffix}"
        used_storage_filenames.add(storage_filename)

        saved_path = save_uploaded_file(
            contents=file_contents,
            filename=storage_filename,
            upload_directory=batch_directory,
            allowed_extensions=DEFAULT_ALLOWED_UPLOAD_EXTENSIONS,
        )
        saved_paths.append(saved_path)
        safe_filenames.append(safe_filename)

    return saved_paths, safe_filenames


def inspect_compatible_fcs_batch(file_paths: Iterable[str | Path]) -> dict[str, Any]:
    """Return the existing full multi-file consistency report for a batch."""
    normalized_paths = [str(Path(file_path)) for file_path in file_paths]
    if not normalized_paths:
        raise ValueError("Select at least one FCS file.")

    return FCSMultiFileConsistencyChecker(
        file_paths=normalized_paths,
    ).check_multifiles_consistency()


def build_upload_feedback(
    *,
    filenames: list[str],
    consistency_report: dict[str, Any],
) -> tuple[str, str]:
    """Build the user-visible batch validation message and Bootstrap color."""
    if not consistency_report.get("are_all_files_consistent", False):
        mismatch_details = consistency_report.get("mismatch_details") or []
        detail = "; ".join(str(item) for item in mismatch_details[:3])
        message = "The uploaded FCS files are not mutually compatible."
        if detail:
            message = f"{message} {detail}"
        return message, "danger"

    file_count = len(filenames)
    channel_count = len(consistency_report.get("reference_column_names") or [])
    return (
        f"Loaded {file_count} compatible FCS file{'s' if file_count != 1 else ''} "
        f"with {channel_count} channel{'s' if channel_count != 1 else ''}.",
        "success",
    )


def validate_selected_channels(
    *,
    selected_channels: Any,
    available_channels: Iterable[str],
) -> list[str]:
    """Validate selected channels and retain their original FCS column order."""
    available = [str(channel) for channel in available_channels]
    requested = set(normalize_multiple_upload_values(selected_channels))
    selected = [channel for channel in available if channel in requested]

    unknown = sorted(requested.difference(available))
    if unknown:
        raise ValueError(f"Unknown FCS channel selection: {', '.join(unknown)}.")
    if not selected:
        raise ValueError("Select at least one detector channel to export.")

    return selected


def build_sliced_fcs_bytes(
    *,
    input_path: str | Path,
    selected_channels: list[str],
) -> bytes:
    """Build one FCS payload containing only the selected channels."""
    with FCSFile(str(input_path), writable=False) as input_fcs_file:
        available_channels = [str(name) for name in input_fcs_file.get_column_names()]
        ordered_channels = validate_selected_channels(
            selected_channels=selected_channels,
            available_channels=available_channels,
        )
        dataframe = input_fcs_file.dataframe_copy(
            columns=ordered_channels,
            dtype=None,
            deep=True,
        )
        builder = FCSFile.builder_from_dataframe(
            dataframe,
            template=input_fcs_file,
            force_float32=False,
        )
        return builder.build_bytes()


def build_sliced_export_filename(filename: str) -> str:
    """Return the download member name for a sliced FCS file."""
    path = Path(filename)
    return f"{path.stem}_sliced.fcs"


def build_sliced_fcs_zip(
    *,
    file_paths: Iterable[str | Path],
    filenames: Iterable[str],
    selected_channels: Any,
    available_channels: Iterable[str],
) -> bytes:
    """Build a ZIP containing channel-sliced copies of all uploaded FCS files."""
    normalized_paths = [str(Path(file_path)) for file_path in file_paths]
    normalized_filenames = [str(filename) for filename in filenames]
    if len(normalized_paths) != len(normalized_filenames):
        raise ValueError("Stored FCS paths and filenames do not match.")

    ordered_channels = validate_selected_channels(
        selected_channels=selected_channels,
        available_channels=available_channels,
    )
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        used_member_names: set[str] = set()
        for index, (file_path, filename) in enumerate(
            zip(normalized_paths, normalized_filenames, strict=True),
            start=1,
        ):
            member_name = build_sliced_export_filename(filename)
            if member_name in used_member_names:
                member_path = Path(member_name)
                member_name = f"{member_path.stem}_{index}{member_path.suffix}"
            used_member_names.add(member_name)
            archive.writestr(
                member_name,
                build_sliced_fcs_bytes(
                    input_path=file_path,
                    selected_channels=ordered_channels,
                ),
            )

    return zip_buffer.getvalue()
