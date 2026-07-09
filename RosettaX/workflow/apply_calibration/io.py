# -*- coding: utf-8 -*-

import io
import json
import zipfile
from pathlib import Path
from typing import Any, Callable, Optional

from RosettaX.utils.paths import resolve_selected_calibration_file_path
from RosettaX.utils.reader import FCSFile


def resolve_first_uploaded_fcs_path(
    uploaded_fcs_path: Any,
) -> Optional[str]:
    """
    Resolve the first uploaded FCS path.
    """
    resolved_uploaded_fcs_paths = resolve_uploaded_fcs_paths(
        uploaded_fcs_path,
    )

    if not resolved_uploaded_fcs_paths:
        return None

    return resolved_uploaded_fcs_paths[0]


def resolve_uploaded_fcs_paths(
    uploaded_fcs_path: Any,
) -> list[str]:
    """
    Normalize uploaded FCS path payload into a list of paths.
    """
    if uploaded_fcs_path is None:
        return []

    if isinstance(uploaded_fcs_path, list):
        return [str(path) for path in uploaded_fcs_path if str(path).strip()]

    resolved_single_path = str(
        uploaded_fcs_path,
    ).strip()

    if not resolved_single_path:
        return []

    return [
        resolved_single_path,
    ]


def normalize_export_columns(
    export_columns: Any,
) -> list[str]:
    """
    Normalize extra export columns.
    """
    if not isinstance(export_columns, list):
        return []

    return [str(column) for column in export_columns if str(column).strip()]


def build_input_export_columns(
    *,
    source_channels: list[str],
    export_columns: list[str],
) -> list[str]:
    """
    Build input columns required to read from the source FCS file.

    The source channels are always included. Additional export columns are
    copied unchanged.
    """
    input_export_columns: list[str] = []

    for source_channel in source_channels:
        source_channel_string = str(
            source_channel,
        )

        if source_channel_string and source_channel_string not in input_export_columns:
            input_export_columns.append(
                source_channel_string,
            )

    for column_name in export_columns:
        column_name_string = str(
            column_name,
        )

        if (
            column_name_string
            and column_name_string not in input_export_columns
        ):
            input_export_columns.append(
                column_name_string,
            )

    return input_export_columns


def resolve_calibration_file_path(
    selected_calibration: Any,
) -> Path:
    """
    Resolve a calibration picker value into an on disk path.
    """
    return resolve_selected_calibration_file_path(
        selected_calibration,
    )


def load_calibration_payload(
    calibration_file_path: Path,
) -> dict[str, Any]:
    """
    Load a saved calibration payload from disk.
    """
    record = json.loads(
        calibration_file_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(record, dict):
        raise ValueError("Calibration file root record is invalid.")

    outer_payload = record.get(
        "payload",
    )

    if not isinstance(outer_payload, dict):
        raise ValueError('Calibration file is missing top level "payload".')

    return outer_payload


def get_fcs_column_names(
    *,
    uploaded_fcs_path: str,
) -> list[str]:
    """
    Read FCS column names.
    """
    with FCSFile(str(uploaded_fcs_path), writable=False) as fcs_file:
        return [str(name) for name in fcs_file.get_column_names()]


def build_exported_fcs_bytes(
    *,
    uploaded_fcs_path: str,
    input_export_columns: list[str],
    dataframe_transformer: Callable[[Any], Any],
) -> bytes:
    """
    Build exported FCS bytes after applying a dataframe transformer.
    """
    with FCSFile(str(uploaded_fcs_path), writable=False) as input_fcs_file:
        input_dataframe = input_fcs_file.dataframe_copy(
            columns=input_export_columns,
            dtype=float,
            deep=True,
        )

        output_dataframe = dataframe_transformer(
            input_dataframe,
        )

        builder = FCSFile.builder_from_dataframe(
            output_dataframe,
            template=input_fcs_file,
            force_float32=True,
        )

        return builder.build_bytes()


def build_zip_of_exported_fcs_files(
    *,
    uploaded_fcs_paths: list[str],
    input_export_columns: list[str],
    output_channels: list[str],
    dataframe_transformer_factory: Callable[[str], Callable[[Any], Any]],
) -> bytes:
    """
    Build a ZIP file containing exported FCS files.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for uploaded_fcs_path in uploaded_fcs_paths:
            exported_bytes = build_exported_fcs_bytes(
                uploaded_fcs_path=uploaded_fcs_path,
                input_export_columns=input_export_columns,
                dataframe_transformer=dataframe_transformer_factory(
                    uploaded_fcs_path,
                ),
            )

            member_filename = build_export_filename(
                uploaded_fcs_path=uploaded_fcs_path,
                output_channels=output_channels,
            )

            zip_file.writestr(
                member_filename,
                exported_bytes,
            )

    zip_buffer.seek(
        0,
    )

    return zip_buffer.getvalue()


def append_files_to_zip_bytes(
    *,
    zip_bytes: bytes,
    extra_files: dict[str, bytes],
) -> bytes:
    """
    Append extra in-memory files to an existing ZIP payload.
    """
    source_buffer = io.BytesIO(
        zip_bytes,
    )
    output_buffer = io.BytesIO()
    existing_names: set[str] = set()

    with zipfile.ZipFile(source_buffer, mode="r") as source_zip:
        with zipfile.ZipFile(
            output_buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as output_zip:
            for zip_info in source_zip.infolist():
                existing_names.add(
                    zip_info.filename,
                )
                output_zip.writestr(
                    zip_info,
                    source_zip.read(zip_info.filename),
                )

            for member_name, member_bytes in extra_files.items():
                resolved_member_name = _resolve_extra_zip_member_name(
                    member_name=str(member_name),
                    existing_names=existing_names,
                )
                output_zip.writestr(
                    resolved_member_name,
                    member_bytes,
                )
                existing_names.add(
                    resolved_member_name,
                )

    output_buffer.seek(
        0,
    )

    return output_buffer.getvalue()


def build_export_filename(
    *,
    uploaded_fcs_path: str,
    output_channels: list[str],
) -> str:
    """
    Build an exported FCS filename.
    """
    input_path = Path(
        str(
            uploaded_fcs_path,
        )
    )
    return f"{input_path.stem}_RosettaX.fcs"


def build_zip_filename(
    *,
    output_channels: list[str],
    file_count: int,
) -> str:
    """
    Build an exported ZIP filename.
    """
    if len(output_channels) == 1:
        safe_output_channel = safe_filename_fragment(
            output_channels[0],
        )

    else:
        safe_output_channel = "scattering_calibrated"

    return f"calibrated_{file_count}_files_{safe_output_channel}_RosettaX.zip"


def safe_filename_fragment(
    value: Any,
) -> str:
    """
    Convert a string into a filename safe fragment.
    """
    return (
        str(
            value,
        )
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )


def _resolve_extra_zip_member_name(
    *,
    member_name: str,
    existing_names: set[str],
) -> str:
    candidate = str(member_name).strip() or "report.pdf"
    path = Path(
        candidate,
    )
    stem = path.stem or "report"
    suffix = path.suffix or ".pdf"
    deduplicated_name = f"{stem}{suffix}"
    counter = 2

    while deduplicated_name in existing_names:
        deduplicated_name = f"{stem}_{counter}{suffix}"
        counter += 1

    return deduplicated_name
