# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

from RosettaX.utils import directories


logger = logging.getLogger(__name__)


FOLDER_DISPLAY_ORDER: list[tuple[str, str]] = [
    ("fluorescence", "Fluorescence"),
    ("scattering", "Scattering"),
]


def normalize_profile_filename(filename: str) -> str:
    """
    Normalize a profile file name to a .json file name.
    """
    normalized_filename = str(filename or "").strip()

    if not normalized_filename:
        raise ValueError("Profile filename cannot be empty.")

    if not normalized_filename.endswith(".json"):
        normalized_filename = f"{normalized_filename}.json"

    return normalized_filename


def resolve_selected_profile(selected_profile: str | None) -> tuple[str | None, str]:
    """
    Resolve a selected profile name into a normalized file name and status message.
    """
    if not selected_profile:
        return None, "No profile selected."

    selected_profile_name = str(selected_profile).strip()

    if not selected_profile_name:
        return None, "No profile selected."

    selected_profile_file_name = normalize_profile_filename(selected_profile_name)
    resolved_profile_path = Path(directories.profiles).resolve() / selected_profile_file_name

    if not resolved_profile_path.exists():
        raise FileNotFoundError(f"Profile does not exist: {resolved_profile_path}")

    return selected_profile_file_name, f"Selected profile: {selected_profile_file_name}"


def list_saved_calibrations() -> dict[str, list[str]]:
    """
    List saved calibration files from disk.
    """
    logger.debug("Listing saved calibrations from disk.")

    saved_calibrations: dict[str, list[str]] = {
        "fluorescence": [],
        "scattering": [],
    }

    folder_to_directory = {
        "fluorescence": Path(directories.fluorescence_calibration),
        "scattering": Path(directories.scattering_calibration),
    }

    for folder_name, directory_path in folder_to_directory.items():
        try:
            directory_path.mkdir(parents=True, exist_ok=True)

            file_names = sorted(
                [
                    path.name
                    for path in directory_path.glob("*.json")
                    if path.is_file()
                ],
                key=str.lower,
            )

            saved_calibrations[folder_name] = file_names

            logger.debug(
                "Found %d calibration files in folder=%r directory=%r",
                len(file_names),
                folder_name,
                str(directory_path),
            )

        except Exception:
            logger.exception(
                "Failed to list calibration files for folder=%r directory=%r",
                folder_name,
                str(directory_path),
            )
            saved_calibrations[folder_name] = []

    return saved_calibrations


def build_saved_profile_options() -> list[dict[str, str]]:
    """
    Build saved profile dropdown options from disk.
    """
    logger.debug("Building saved profile options from disk.")

    try:
        setting_files = directories.list_profiles()
        options = [{"label": file_name, "value": file_name} for file_name in setting_files]
        logger.debug("Built %d saved profile options.", len(options))
        return options

    except Exception:
        logger.exception("Failed to build saved profile options.")
        return []


def build_apply_href(folder: str, file_name: str) -> str:
    """
    Build the internal apply calibration link.
    """
    selected_calibration_value = f"{folder}/{file_name}"
    return f"/calibrate?selected_calibration={quote(selected_calibration_value, safe='')}"


def open_saved_calibrations_root() -> str:
    """
    Open the root folder that contains the calibration directories.
    """
    calibration_root_directory = Path(directories.fluorescence_calibration).resolve().parent
    directories.open_directory(calibration_root_directory)
    return f"Opened calibration folder: {calibration_root_directory}"


def open_profiles_directory() -> str:
    """
    Open the profiles directory.
    """
    resolved_profile_directory = Path(directories.profiles).resolve()
    directories.open_directory(resolved_profile_directory)
    return f"Opened profile folder: {resolved_profile_directory}"


def build_saved_calibrations_empty_state() -> str:
    return "No calibration found."


def build_saved_profiles_load_message_for_missing_selection() -> str:
    return "No profile selected."