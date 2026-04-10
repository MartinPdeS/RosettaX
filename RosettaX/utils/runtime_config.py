from dataclasses import dataclass
from typing import Optional, ClassVar
import json


@dataclass
class RuntimeConfig:
    _instance: ClassVar[Optional["RuntimeConfig"]] = None
    _initialized: ClassVar[bool] = False

    # General analysis parameters
    max_events_for_analysis: Optional[int] = 200_000
    n_bins_for_plots: Optional[int] = 400
    peak_count: Optional[int] = 3

    # Fluorescence calibration page defaults
    fcs_file_path: Optional[str] = None
    fluorescence_page_scattering_detector: Optional[str] = None
    fluorescence_page_fluorescence_detector: Optional[str] = None

    mesf_values: Optional[str] = "1"

    # Optical properties for Mie theory calculations
    particle_diameter_nm: float = 100
    particle_refractive_index: float = 1.59
    medium_refractive_index: float = 1.33

    core_refractive_index: float = 1.59
    shell_refractive_index: float = 1.40
    shell_thickness_nm: float = 20
    core_diameter_nm: float = 100

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, *args, **kwargs):
        if self.__class__._initialized:
            return

        self.__class__._initialized = True

    def update(self, **kwargs) -> None:
        """
        Update the runtime configuration with new values. This function takes keyword arguments corresponding to the fields of the RuntimeConfig dataclass. Only fields that are explicitly provided will be updated; others will remain unchanged.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                print(f"Updated config {key} to value: {value}")
            else:
                print(f"Ignored unknown config key: {key}")

    @classmethod
    def get_instance(cls) -> "RuntimeConfig":
        return cls()

    def load_json(self, json_filename: str) -> dict:
        from RosettaX.pages.settings.utils import profile_directory

        try:
            with open(profile_directory / json_filename, "r", encoding="utf-8") as file:
                data = json.load(file)

            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    print(f"Loaded {key} from JSON with value: {value}")
                else:
                    print(f"Ignored unknown config key: {key}")

            return data

        except Exception as error:
            print(f"Error loading JSON config: {error}")
            return {}

    def __repr__(self) -> str:
        return (
            f"RuntimeConfig(max_events_for_analysis={self.max_events_for_analysis}, "
            f"n_bins_for_plots={self.n_bins_for_plots}, "
            f"peak_count={self.peak_count}, "
            f"fcs_file_path={self.fcs_file_path}, "
            f"fluorescence_page_scattering_detector={self.fluorescence_page_scattering_detector}, "
            f"fluorescence_page_fluorescence_detector={self.fluorescence_page_fluorescence_detector}, "
            f"mesf_values={self.mesf_values}, "
            f"particle_diameter_nm={self.particle_diameter_nm}, "
            f"particle_refractive_index={self.particle_refractive_index}, "
            f"medium_refractive_index={self.medium_refractive_index}, "
            f"core_refractive_index={self.core_refractive_index}, "
            f"shell_refractive_index={self.shell_refractive_index}, "
            f"shell_thickness_nm={self.shell_thickness_nm}, "
            f"core_diameter_nm={self.core_diameter_nm}"
        )

    def to_dict(self) -> dict:
        return {
            "max_events_for_analysis": self.max_events_for_analysis,
            "n_bins_for_plots": self.n_bins_for_plots,
            "peak_count": self.peak_count,
            "fcs_file_path": self.fcs_file_path,
            "fluorescence_page_scattering_detector": self.fluorescence_page_scattering_detector,
            "fluorescence_page_fluorescence_detector": self.fluorescence_page_fluorescence_detector,
            "mesf_values": self.mesf_values,
            "particle_diameter_nm": self.particle_diameter_nm,
            "particle_refractive_index": self.particle_refractive_index,
            "medium_refractive_index": self.medium_refractive_index,
            "core_refractive_index": self.core_refractive_index,
            "shell_refractive_index": self.shell_refractive_index,
            "shell_thickness_nm": self.shell_thickness_nm,
            "core_diameter_nm": self.core_diameter_nm,
        }