# -*- coding: utf-8 -*-

from pathlib import Path

from RosettaX.utils import directories


def build_calibration_directory_map() -> dict[str, Path]:
    """
    Return the supported calibration folders and their resolved directories.
    """
    return {
        "fluorescence": Path(directories.fluorescence_calibration),
        "scattering": Path(directories.scattering_calibration),
    }


def resolve_named_file_within_directory(
    *,
    directory: Path,
    file_name: str,
    description: str,
    allowed_suffixes: tuple[str, ...] | None = None,
) -> Path:
    """
    Resolve a file safely within one allowed directory.
    """
    resolved_directory = Path(directory).expanduser().resolve()
    normalized_file_name = str(file_name).strip()

    if not normalized_file_name:
        raise ValueError(f"{description} path is empty.")

    resolved_path = (resolved_directory / normalized_file_name).resolve()

    if resolved_path == resolved_directory or resolved_directory not in resolved_path.parents:
        raise ValueError(f"Invalid {description} path.")

    if allowed_suffixes is not None:
        normalized_suffixes = tuple(suffix.lower() for suffix in allowed_suffixes)
        if resolved_path.suffix.lower() not in normalized_suffixes:
            raise ValueError(
                f"Invalid {description} file extension: {resolved_path.suffix or '<none>'}."
            )

    return resolved_path


def resolve_calibration_file_path(*, folder: str, file_name: str) -> Path:
    """
    Resolve one calibration JSON file path safely.
    """
    normalized_folder = str(folder).strip().lower()
    calibration_directory_map = build_calibration_directory_map()

    if normalized_folder not in calibration_directory_map:
        raise ValueError(f"Unsupported calibration folder: {folder}")

    return resolve_named_file_within_directory(
        directory=calibration_directory_map[normalized_folder],
        file_name=file_name,
        description="calibration file",
        allowed_suffixes=(".json",),
    )


def resolve_selected_calibration_file_path(selected_calibration: str) -> Path:
    """
    Resolve a ``folder/file.json`` calibration selection safely.
    """
    selected_calibration_string = str(selected_calibration).strip()

    if not selected_calibration_string:
        raise ValueError("Selected calibration path is empty.")

    if "/" not in selected_calibration_string:
        raise ValueError(
            f"Invalid selected calibration value: {selected_calibration_string!r}."
        )

    folder_name, file_name = selected_calibration_string.split("/", 1)

    return resolve_calibration_file_path(
        folder=folder_name,
        file_name=file_name,
    )


def normalize_profile_filename(profile_name: str) -> str:
    """
    Normalize a profile name to a JSON filename.
    """
    normalized_profile_name = str(profile_name or "").strip()

    if not normalized_profile_name:
        raise ValueError("Profile filename cannot be empty.")

    if not normalized_profile_name.endswith(".json"):
        normalized_profile_name = f"{normalized_profile_name}.json"

    return normalized_profile_name


def resolve_profile_file_path(profile_name: str) -> Path:
    """
    Resolve one profile JSON file path safely.
    """
    normalized_profile_name = normalize_profile_filename(profile_name)

    return resolve_named_file_within_directory(
        directory=Path(directories.profiles),
        file_name=normalized_profile_name,
        description="profile file",
        allowed_suffixes=(".json",),
    )
