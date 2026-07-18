# -*- coding: utf-8 -*-

import io
import zipfile
from pathlib import Path
from typing import Any, Iterable

from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.upload.services import (
    build_upload_feedback,
    inspect_compatible_fcs_batch,
    normalize_multiple_upload_values,
    save_uploaded_batch,
)


DEFAULT_UPLOAD_DIRECTORY = Path.home() / ".rosettax" / "uploads" / "fcs-slicer"


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
