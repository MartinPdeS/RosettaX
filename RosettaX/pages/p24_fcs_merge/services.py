
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.upload import services as upload_services

DEFAULT_UPLOAD_DIRECTORY = Path.home() / ".rosettax" / "uploads" / "fcs-merge"


def save_uploaded_batch(
    *,
    contents: Any,
    filenames: Any,
    upload_directory: Path = DEFAULT_UPLOAD_DIRECTORY,
) -> tuple[list[Path], list[str]]:
    """Save one FCS merge batch in the merge workflow upload directory."""
    return upload_services.save_uploaded_batch(
        contents=contents,
        filenames=filenames,
        upload_directory=upload_directory,
    )


def validate_merge_input_paths(
    file_paths: Iterable[str | Path],
) -> tuple[list[Path], dict[str, Any]]:
    """Validate that a multi-file FCS batch can be merged safely."""
    normalized_paths = [Path(file_path) for file_path in file_paths if str(file_path).strip()]
    if len(normalized_paths) < 2:
        raise ValueError("Select at least two FCS files to merge.")

    consistency_report = upload_services.inspect_compatible_fcs_batch(normalized_paths)
    if not consistency_report.get("are_all_files_consistent", False):
        raise ValueError(upload_services.build_consistency_error_text(consistency_report))

    return normalized_paths, consistency_report


def build_merged_fcs_bytes(
    *,
    file_paths: Iterable[str | Path],
) -> bytes:
    """Concatenate compatible FCS events in input order using the first file as template."""
    normalized_paths, consistency_report = validate_merge_input_paths(file_paths)
    columns = [str(name) for name in consistency_report["reference_column_names"]]

    with FCSFile(str(normalized_paths[0]), writable=False) as template_fcs_file:
        dataframes = [
            template_fcs_file.dataframe_copy(
                columns=columns,
                dtype=None,
                deep=True,
            )
        ]
        for input_path in normalized_paths[1:]:
            with FCSFile(str(input_path), writable=False) as input_fcs_file:
                dataframes.append(
                    input_fcs_file.dataframe_copy(
                        columns=columns,
                        dtype=None,
                        deep=True,
                    )
                )

        merged_dataframe = pd.concat(dataframes, ignore_index=True, copy=False)
        builder = FCSFile.builder_from_dataframe(
            merged_dataframe,
            template=template_fcs_file,
            force_float32=False,
        )
        return builder.build_bytes()


def build_merged_export_filename(first_filename: str) -> str:
    """Build the merged download filename from the first uploaded file name."""
    stem = Path(str(first_filename)).stem
    return f"{stem or 'rosettax'}_merged.fcs"
