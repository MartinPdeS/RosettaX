from pathlib import Path
import json

from RosettaX.utils import directories
from RosettaX.pages.settings.utils import get_profile_path

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
        destination_path = get_profile_path(filename)

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