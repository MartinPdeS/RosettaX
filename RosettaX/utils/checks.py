from pathlib import Path
from typing import Any, Optional

from RosettaX.utils.reader import FCSFile


def _normalize_file_paths(file_paths: list[str]) -> list[str]:
    return [
        str(Path(file_path).expanduser())
        for file_path in file_paths
        if str(file_path).strip()
    ]


def _build_empty_consistency_report() -> dict[str, Any]:
    return {
        "are_all_files_consistent": True,
        "reference_file_path": None,
        "reference_column_names": [],
        "reference_fcs_version": None,
        "invalid_file_paths": [],
        "mismatch_details": [],
        "column_name_consistency": {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_column_names": [],
            "invalid_file_paths": [],
            "mismatch_details": [],
        },
        "version_consistency": {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_fcs_version": None,
            "invalid_file_paths": [],
            "mismatch_details": [],
        },
    }


def _get_fcs_column_names(file_path: str) -> list[str]:
    with FCSFile(str(file_path), writable=False) as fcs_file:
        return [str(column_name) for column_name in fcs_file.get_column_names()]


def _get_fcs_version(file_path: str) -> Optional[str]:
    with FCSFile(str(file_path), writable=False) as fcs_file:
        text_section = getattr(fcs_file, "text", {}) or {}

        for key in ["FCS format", "FCSFORMAT", "$VERSION", "version"]:
            if key in text_section:
                return str(text_section[key])

        keywords = text_section.get("Keywords", {}) or {}
        for key in ["$VERSION", "VERSION"]:
            if key in keywords:
                return str(keywords[key])

    return None


def check_column_name_consistency(file_paths: list[str]) -> dict[str, Any]:
    normalized_file_paths = _normalize_file_paths(file_paths)

    if not normalized_file_paths:
        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_column_names": [],
            "invalid_file_paths": [],
            "mismatch_details": [],
        }

    reference_file_path = normalized_file_paths[0]

    with FCSFile(reference_file_path, writable=False) as reference_fcs_file:
        reference_column_names = list(reference_fcs_file.get_column_names())

    reference_column_name_tuple = tuple(reference_column_names)

    invalid_file_paths: list[str] = []
    mismatch_details: list[str] = []

    for current_file_path in normalized_file_paths[1:]:
        try:
            current_column_names = _get_fcs_column_names(current_file_path)
        except Exception as exc:
            invalid_file_paths.append(current_file_path)
            mismatch_details.append(
                f"{Path(current_file_path).name}: could not read columns "
                f"({type(exc).__name__}: {exc})"
            )
            continue

        current_column_name_tuple = tuple(current_column_names)

        if current_column_name_tuple != reference_column_name_tuple:
            invalid_file_paths.append(current_file_path)
            mismatch_details.append(
                f"{Path(current_file_path).name}: columns do not match "
                f"{Path(reference_file_path).name}"
            )

    return {
        "are_all_files_consistent": len(invalid_file_paths) == 0,
        "reference_file_path": reference_file_path,
        "reference_column_names": [str(name) for name in reference_column_names],
        "invalid_file_paths": invalid_file_paths,
        "mismatch_details": mismatch_details,
    }


def check_version_consistency(file_paths: list[str]) -> dict[str, Any]:
    normalized_file_paths = _normalize_file_paths(file_paths)

    if not normalized_file_paths:
        return {
            "are_all_files_consistent": True,
            "reference_file_path": None,
            "reference_fcs_version": None,
            "invalid_file_paths": [],
            "mismatch_details": [],
        }

    reference_file_path = normalized_file_paths[0]

    try:
        reference_fcs_version = _get_fcs_version(reference_file_path)
    except Exception as exc:
        return {
            "are_all_files_consistent": False,
            "reference_file_path": reference_file_path,
            "reference_fcs_version": None,
            "invalid_file_paths": [reference_file_path],
            "mismatch_details": [
                f"{Path(reference_file_path).name}: could not read FCS version "
                f"({type(exc).__name__}: {exc})"
            ],
        }

    invalid_file_paths: list[str] = []
    mismatch_details: list[str] = []

    for current_file_path in normalized_file_paths[1:]:
        try:
            current_fcs_version = _get_fcs_version(current_file_path)
        except Exception as exc:
            invalid_file_paths.append(current_file_path)
            mismatch_details.append(
                f"{Path(current_file_path).name}: could not read FCS version "
                f"({type(exc).__name__}: {exc})"
            )
            continue

        if current_fcs_version != reference_fcs_version:
            invalid_file_paths.append(current_file_path)
            mismatch_details.append(
                f"{Path(current_file_path).name}: FCS version does not match "
                f"{Path(reference_file_path).name} "
                f"({current_fcs_version} != {reference_fcs_version})"
            )

    return {
        "are_all_files_consistent": len(invalid_file_paths) == 0,
        "reference_file_path": reference_file_path,
        "reference_fcs_version": reference_fcs_version,
        "invalid_file_paths": invalid_file_paths,
        "mismatch_details": mismatch_details,
    }


def check_multifiles_consistency(file_paths: list[str]) -> dict[str, Any]:
    normalized_file_paths = _normalize_file_paths(file_paths)

    if not normalized_file_paths:
        return _build_empty_consistency_report()

    column_name_consistency_report = check_column_name_consistency(normalized_file_paths)
    version_consistency_report = check_version_consistency(normalized_file_paths)

    combined_invalid_file_paths = sorted(
        set(
            column_name_consistency_report["invalid_file_paths"]
            + version_consistency_report["invalid_file_paths"]
        )
    )

    combined_mismatch_details = (
        list(column_name_consistency_report["mismatch_details"])
        + list(version_consistency_report["mismatch_details"])
    )

    return {
        "are_all_files_consistent": (
            column_name_consistency_report["are_all_files_consistent"]
            and version_consistency_report["are_all_files_consistent"]
        ),
        "reference_file_path": column_name_consistency_report["reference_file_path"],
        "reference_column_names": column_name_consistency_report["reference_column_names"],
        "reference_fcs_version": version_consistency_report["reference_fcs_version"],
        "invalid_file_paths": combined_invalid_file_paths,
        "mismatch_details": combined_mismatch_details,
        "column_name_consistency": column_name_consistency_report,
        "version_consistency": version_consistency_report,
    }