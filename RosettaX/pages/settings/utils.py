from pathlib import Path
import json

from RosettaX.utils import directories


def _normalize_profile_filename(filename: str) -> str:
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


def _get_profile_path(filename: str) -> Path:
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
    normalized_filename = _normalize_profile_filename(filename)
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
    profile_path = _get_profile_path(filename)

    if profile_path.exists() and profile_path.is_file():
        with profile_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    return None


def save_profile(filename: str, profile_data: dict) -> str:
    """
    Save a profile to the profiles directory.

    Parameters
    ----------
    filename : str
        Profile name or filename.
    profile_data : dict
        Dictionary to serialize as JSON.

    Returns
    -------
    str
        Status message.
    """
    try:
        profile_path = _get_profile_path(filename)
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        with profile_path.open("w", encoding="utf-8") as file_handle:
            json.dump(profile_data, file_handle, indent=4)

    except Exception as exc:
        return f"Error saving profile: {exc}"

    return "Profile saved successfully."


def delete_profile(filename: str) -> str:
    """
    Delete a profile from the profiles directory.

    Parameters
    ----------
    filename : str
        Profile name or filename.

    Returns
    -------
    str
        Status message.
    """
    try:
        normalized_filename = _normalize_profile_filename(filename)
        profile_path = directories.profiles / normalized_filename

        if normalized_filename == "default_profile.json":
            return "Cannot delete default profile. Please choose a different profile to delete."

        if profile_path.exists() and profile_path.is_file():
            profile_path.unlink()
            return f"Profile '{normalized_filename}' deleted successfully."

        return f"Profile '{normalized_filename}' not found."

    except Exception as exc:
        return f"Error deleting profile: {exc}"


def create_profile(filename: str) -> str:
    """
    Create a new profile by copying the default profile.

    Parameters
    ----------
    filename : str
        Profile name or filename.

    Returns
    -------
    str
        Status message.
    """
    try:
        source_path = Path(directories.default_profile)
        destination_path = _get_profile_path(filename)

        if destination_path.exists():
            return f"Profile '{destination_path.name}' already exists."

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        with source_path.open("r", encoding="utf-8") as source_handle:
            default_profile_data = json.load(source_handle)

        with destination_path.open("w", encoding="utf-8") as destination_handle:
            json.dump(default_profile_data, destination_handle, indent=4)

        return f"Profile '{destination_path.name}' created successfully."

    except Exception as exc:
        return f"Error creating profile: {exc}"