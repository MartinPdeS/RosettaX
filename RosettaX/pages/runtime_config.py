from dataclasses import dataclass, field
from typing import Optional
import json
from pathlib import Path
from RosettaX.pages.settings.ids import Ids

class LoadSettings():
    def __init__(self, json_file: str = "default_profile.json"):
        self.json_file = json_file
        base_dir = Path(__file__).resolve().parents[1]
        settings_path = Path(self.json_file) if self.json_file else (base_dir / "data" / "settings" / "default_profile.json")

        with settings_path.open("r", encoding="utf-8") as f:
            self.settings = json.load(f)

    def type_cast(self, value, target_type):
        if target_type == bool:
            if self.settings[value]:
                return True
            else:
                return False
        elif target_type == int:
            return int(self.settings[value])
        elif target_type == float:
            return float(self.settings[value])
        elif target_type == None:
            if self.settings[value] == "none" or self.settings[value] == "":
                return None
            else:
                return self.settings[value]
        elif target_type == str:
            return str(self.settings[value])
        return self.settings[value]


@dataclass
class RuntimeConfig:
    def __init__(self, json_file: Optional[str] = None):
        base_dir = Path(__file__).resolve().parents[1]
        if json_file is not None:
            self.json_file = str(base_dir / "data" / "settings" / json_file)
        else:
            self.json_file = str(base_dir / "data" / "settings" / "default_profile.json")
        self._explicit = set()

    settings = LoadSettings(json_file=None)
    default_debug: bool = settings.type_cast(Ids.Default.default_debug, bool)

    # Fluorescence calibration page, visibility
    fluorescence_show_scattering_controls: bool = settings.type_cast(Ids.Default.default_fluorescence_show_scattering_controls, bool)
    default_fluorescence_show_threshold_controls: bool = settings.type_cast(Ids.Default.default_fluorescence_show_threshold_controls, bool)
    default_fluorescence_show_fluorescence_controls: bool = settings.type_cast(Ids.Default.default_fluorescence_show_fluorescence_controls, bool)


    # Fluorescence calibration page, debug outputs
    default_fluorescence_debug_scattering: bool = settings.type_cast(Ids.Default.default_fluorescence_debug_scattering, bool)
    default_fluorescence_debug_fluorescence: bool = settings.type_cast(Ids.Default.default_fluorescence_debug_fluorescence, bool)
    default_fluorescence_debug_load: bool = settings.type_cast(Ids.Default.default_fluorescence_debug_load, bool)

    # General analysis parameters
    default_max_events_for_analysis: Optional[int] = settings.type_cast(Ids.Default.default_max_events_for_analysis, int)
    default_n_bins_for_plots: Optional[int] = settings.type_cast(Ids.Default.default_n_bins_for_plots, int)
    default_peak_count: Optional[int] = settings.type_cast(Ids.Default.default_peak_count, int)

    # Fluorescence calibration page defaults
    default_fcs_file_path: Optional[str] = settings.type_cast(Ids.Default.default_fcs_file_path, str)
    default_fluorescence_page_scattering_detector: Optional[str] = settings.type_cast(Ids.Default.default_fluorescence_page_scattering_detector, None)
    default_fluorescence_page_fluorescence_detector: Optional[str] = settings.type_cast(Ids.Default.default_fluorescence_page_fluorescence_detector, None)

    # Optical properties for Mie theory calculations
    default_particle_diameter_nm = settings.type_cast(Ids.Default.default_particle_diameter_nm, int)
    default_particle_index = settings.type_cast(Ids.Default.default_particle_index, float)
    default_medium_index = settings.type_cast(Ids.Default.default_medium_index, float)

    default_core_index = settings.type_cast(Ids.Default.default_core_index, float)
    default_shell_index = settings.type_cast(Ids.Default.default_shell_index, float)
    default_shell_thickness_nm = settings.type_cast(Ids.Default.default_shell_thickness_nm, int)
    default_core_diameter_nm = settings.type_cast(Ids.Default.default_core_diameter_nm, int)

    # default MESF Bead Table Value
    default_mesf_values = settings.type_cast(Ids.Default.default_mesf_values, str)

    _explicit: set[str] = field(default_factory=set, init=False, repr=False)

    def mark_explicit(self, field_name: str) -> None:
        self._explicit.add(field_name)

    def is_explicit(self, field_name: str) -> bool:
        return field_name in self._explicit

    def apply_policy(self) -> None:
        """
        Apply global policy based on `debug`, without overriding values explicitly set by CLI.
        """
        if self.default_debug:
            if not self.is_explicit("default_fluorescence_show_scattering_controls"):
                self.default_fluorescence_show_scattering_controls = True
            if not self.is_explicit("default_fluorescence_show_threshold_controls"):
                self.default_fluorescence_show_threshold_controls = True

            if not self.is_explicit("default_fluorescence_debug_scattering"):
                self.default_fluorescence_debug_scattering = True
            if not self.is_explicit("default_fluorescence_debug_fluorescence"):
                self.default_fluorescence_debug_fluorescence = True
        else:
            if not self.is_explicit("default_fluorescence_show_scattering_controls"):
                self.default_fluorescence_show_scattering_controls = False
            if not self.is_explicit("default_fluorescence_show_threshold_controls"):
                self.default_fluorescence_show_threshold_controls = False

            if not self.is_explicit("default_fluorescence_debug_scattering"):
                self.default_fluorescence_debug_scattering = False
            if not self.is_explicit("default_fluorescence_debug_fluorescence"):
                self.default_fluorescence_debug_fluorescence = False
    
def list_setting_files():
    """
    Gets list of saved profiles from the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function returns a list of filenames.
    """
    list_of_filenames = []
    profiles_dir = Path("RosettaX/data/settings")
    if profiles_dir.exists() and profiles_dir.is_dir():
        for file in profiles_dir.iterdir():
            if file.is_file() and file.suffix == ".json":
                list_of_filenames.append(file.name.replace(".json", ""))
    return list_of_filenames

def get_saved_profile(jsonfilename: str):
    """
    Gets a saved profile from the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function returns a dictionary containing the filename and path of the profile.
    """
    profiles_dir = Path("RosettaX/data/settings")
    if profiles_dir.exists() and profiles_dir.is_dir():
        profile_path = profiles_dir / jsonfilename
        if profile_path.exists() and profile_path.is_file():
            with profile_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return None

def save_profile(jsonfilename: str, profile_data: dict):
    """
    Saves a profile to the settings directory. Each profile is a json file that contains a set of default values for the fluorescence calibration page. This function takes a dictionary containing the filename and path of the profile, as well as the profile data to be saved.
    """
    try:
        profiles_dir = Path("RosettaX/data/settings")
        if profiles_dir.exists() and profiles_dir.is_dir():
            profile_path = profiles_dir / jsonfilename
            with profile_path.open("w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=4)
    except Exception as e:
        return f"Error saving profile: {e}"
    
    return "Profile saved successfully."

_runtime_config: Optional[RuntimeConfig] = None

def get_runtime_config(default="default_profile.json") -> RuntimeConfig:
    global _runtime_config
    if _runtime_config is None:
        _runtime_config = RuntimeConfig(default)
        _runtime_config.apply_policy()
    return _runtime_config