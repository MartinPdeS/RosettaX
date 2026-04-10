from dataclasses import dataclass
from typing import Optional, ClassVar
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class RuntimeConfig:
    _instance: ClassVar[Optional["RuntimeConfig"]] = None
    _initialized: ClassVar[bool] = False

    class Default:
        # General analysis parameters
        max_events_for_analysis: Optional[int] = 200_000
        n_bins_for_plots: Optional[int] = 400
        peak_count: Optional[int] = 3

        # Fluorescence calibration page defaults
        fluorescence_page_scattering_detector: Optional[str] = None
        fluorescence_page_fluorescence_detector: Optional[str] = None
        particle_diameter = 100
        particle_refractive_index = 1.59
        medium_refractive_index = 1.33
        core_refractive_index = 1.59
        shell_refractive_index = 1.40
        shell_thickness = 20
        core_diameter = 100
        mesf_values: Optional[str] = "1, 10, 100"
        fcs_file_path: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("Created new RuntimeConfig singleton instance.")
        else:
            logger.debug("Reusing existing RuntimeConfig singleton instance.")

        return cls._instance

    def __init__(self, *args, **kwargs):
        if self.__class__._initialized:
            logger.debug("RuntimeConfig already initialized. Skipping __init__.")
            return

        self.__class__._initialized = True
        logger.debug("Initialized RuntimeConfig singleton.")

    def update(self, **kwargs) -> None:
        """
        Update the runtime configuration with new values.

        This function takes keyword arguments corresponding to the fields of the
        RuntimeConfig.Default class. Only fields that are explicitly provided
        will be updated. Unknown keys are ignored.
        """
        logger.debug("RuntimeConfig.update called with kwargs=%r", kwargs)

        for key, value in kwargs.items():
            if hasattr(self.Default, key):
                old_value = getattr(self.Default, key)
                setattr(self.Default, key, value)
                logger.debug(
                    "Updated RuntimeConfig.Default.%s from %r to %r",
                    key,
                    old_value,
                    value,
                )
            else:
                logger.warning("Ignored unknown RuntimeConfig key=%r value=%r", key, value)

    @classmethod
    def get_instance(cls) -> "RuntimeConfig":
        logger.debug("RuntimeConfig.get_instance called.")
        return cls()

    def load_json(self, json_filename: str) -> dict:
        from RosettaX.pages.settings.utils import profile_directory

        json_path = profile_directory / json_filename
        logger.debug("RuntimeConfig.load_json called with json_path=%r", str(json_path))

        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            logger.debug("Loaded JSON config data=%r", data)

            for key, value in data.items():
                if hasattr(self.Default, key):
                    old_value = getattr(self.Default, key)
                    setattr(self.Default, key, value)
                    logger.debug(
                        "Loaded RuntimeConfig.Default.%s from JSON. Old value=%r new value=%r",
                        key,
                        old_value,
                        value,
                    )
                else:
                    logger.warning(
                        "Ignored unknown RuntimeConfig key from JSON: key=%r value=%r",
                        key,
                        value,
                    )

            return data

        except Exception:
            logger.exception("Failed to load JSON config from json_path=%r", str(json_path))
            return {}

    def __repr__(self) -> str:
        representation = (
            f"RuntimeConfig("
            f"max_events_for_analysis={self.Default.max_events_for_analysis}, "
            f"n_bins_for_plots={self.Default.n_bins_for_plots}, "
            f"peak_count={self.Default.peak_count}, "
            f"fcs_file_path={self.Default.fcs_file_path}, "
            f"fluorescence_page_scattering_detector={self.Default.fluorescence_page_scattering_detector}, "
            f"fluorescence_page_fluorescence_detector={self.Default.fluorescence_page_fluorescence_detector}, "
            f"mesf_values={self.Default.mesf_values}, "
            f"particle_diameter={self.Default.particle_diameter}, "
            f"particle_refractive_index={self.Default.particle_refractive_index}, "
            f"medium_refractive_index={self.Default.medium_refractive_index}, "
            f"core_refractive_index={self.Default.core_refractive_index}, "
            f"shell_refractive_index={self.Default.shell_refractive_index}, "
            f"shell_thickness={self.Default.shell_thickness}, "
            f"core_diameter={self.Default.core_diameter})"
        )
        logger.debug("RuntimeConfig.__repr__ returning %r", representation)
        return representation

    def to_dict(self) -> dict:
        runtime_config_dict = {
            "max_events_for_analysis": self.Default.max_events_for_analysis,
            "n_bins_for_plots": self.Default.n_bins_for_plots,
            "peak_count": self.Default.peak_count,
            "fcs_file_path": self.Default.fcs_file_path,
            "fluorescence_page_scattering_detector": self.Default.fluorescence_page_scattering_detector,
            "fluorescence_page_fluorescence_detector": self.Default.fluorescence_page_fluorescence_detector,
            "mesf_values": self.Default.mesf_values,
            "particle_diameter": self.Default.particle_diameter,
            "particle_refractive_index": self.Default.particle_refractive_index,
            "medium_refractive_index": self.Default.medium_refractive_index,
            "core_refractive_index": self.Default.core_refractive_index,
            "shell_refractive_index": self.Default.shell_refractive_index,
            "shell_thickness": self.Default.shell_thickness,
            "core_diameter": self.Default.core_diameter,
        }
        logger.debug("RuntimeConfig.to_dict returning %r", runtime_config_dict)
        return runtime_config_dict