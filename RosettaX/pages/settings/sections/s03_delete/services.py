from RosettaX.utils import directories
from RosettaX.pages.settings.utils import normalize_profile_filename

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
        normalized_filename = normalize_profile_filename(filename)
        profile_path = directories.profiles / normalized_filename

        if normalized_filename == "default_profile.json":
            return "Cannot delete default profile. Please choose a different profile to delete."

        if profile_path.exists() and profile_path.is_file():
            profile_path.unlink()
            return f"Profile '{normalized_filename}' deleted successfully."

        return f"Profile '{normalized_filename}' not found."

    except Exception as exc:
        return f"Error deleting profile: {exc}"

