from pathlib import Path
import json

from RosettaX.utils import directories

def get_saved_profile(filename: str):
    """
    Gets a saved profile from the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function returns a dictionary containing the filename and path of the profile.
    """
    profile_path = directories.profiles / Path(filename)
    if profile_path.exists() and profile_path.is_file():
        with profile_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(filename: str, profile_data: dict) -> str:
    """
    Saves a profile to the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function takes a dictionary containing the filename and path of the profile, as well as the profile data to be saved.
    """
    try:
        profile_path = directories.profiles / Path(filename)
        with profile_path.open("w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)
    except Exception as e:
        return f"Error saving profile: {e}"

    return "Profile saved successfully."

def delete_profile(filename: str) -> str:
    """
    Deletes a profile from the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function takes a dictionary containing the filename and path of the profile to be deleted.
    """
    try:
        profile_path = directories.profiles / Path(filename)
        if profile_path.exists() and profile_path.is_file():
            if filename == "default_profile.json":
                return f"Cannot delete default profile. Please choose a different profile to delete."
            profile_path.unlink()
            return f"Profile '{filename}' deleted successfully."
        else:
            return f"Profile '{filename}' not found."
    except Exception as e:
        return f"Error deleting profile: {e}"

def create_profile(filename: str) -> str:
    """
    Creates a new profile in the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function takes a dictionary containing the filename and path of the profile to be created.
    """
    try:
        source = directories.default_profile
        destination = directories.profiles / Path(filename)
        if not destination.exists():
            with open(source, "r") as f_src, open(destination.with_suffix(".json"), "w") as f_dst:
                f_dst.write(f_src.read())
            return f"Profile '{filename}' created successfully."
        else:
            return f"Profile '{filename}' already exists."
    except Exception as e:
        return f"Error creating profile: {e}"


