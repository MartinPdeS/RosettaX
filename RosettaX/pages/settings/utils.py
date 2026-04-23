from pathlib import Path
import json

from RosettaX.utils import directories


def normalize_profile_filename(filename: str) -> str:
    """
    Normalize a profile filename so that all profile operations use the same
    '.json' suffix convention.

    Parameters
    ----------
    filename : str
        Raw profile name or filename.

    Returns
    -------
    str
        Normalized filename ending with '.json'.
    """
    normalized_filename = str(filename or "").strip()

    if not normalized_filename:
        raise ValueError("Profile filename cannot be empty.")

    if not normalized_filename.endswith(".json"):
        normalized_filename = f"{normalized_filename}.json"

    return normalized_filename


def get_profile_path(filename: str) -> Path:
    """
    Resolve the absolute path of a profile file in the profiles directory.

    Parameters
    ----------
    filename : str
        Raw profile name or filename.

    Returns
    -------
    Path
        Absolute profile path.
    """
    normalized_filename = normalize_profile_filename(filename)
    return directories.profiles / normalized_filename


def get_saved_profile(filename: str):
    """
    Load a saved profile from the profiles directory.

    Parameters
    ----------
    filename : str
        Profile name or filename.

    Returns
    -------
    dict | None
        Parsed JSON profile content if the file exists, otherwise None.
    """
    profile_path = get_profile_path(filename)

    if profile_path.exists() and profile_path.is_file():
        with profile_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    return None

