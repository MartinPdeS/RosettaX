from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RuntimeConfig:
    debug: bool = False

    # Fluorescence calibration page, visibility
    fluorescence_show_scattering_controls: bool = True
    fluorescence_show_threshold_controls: bool = True
    fluorescence_show_fluorescence_controls: bool = True


    # Fluorescence calibration page, debug outputs
    fluorescence_debug_scattering: bool = False
    fluorescence_debug_fluorescence: bool = False
    fluorescence_debug_load: bool = False

    # General analysis parameters
    max_events_for_analysis: Optional[int] = 200_000
    n_bins_for_plots: Optional[int] = 400
    default_peak_count: Optional[int] = 3

    # Fluorescence calibration page defaults
    fcs_file_path: Optional[str] = None
    fluorescence_page_scattering_detector: Optional[str] = None
    fluorescence_page_fluorescence_detector: Optional[str] = None

    # Optical properties for Mie theory calculations
    default_particle_diameter_nm = 100
    default_particle_index = 1.59
    default_medium_index = 1.33

    default_core_index = 1.59
    default_shell_index = 1.40
    default_shell_thickness_nm = 20
    default_core_diameter_nm = 100


    _explicit: set[str] = field(default_factory=set, init=False, repr=False)

    def mark_explicit(self, field_name: str) -> None:
        self._explicit.add(field_name)

    def is_explicit(self, field_name: str) -> bool:
        return field_name in self._explicit

    def apply_policy(self) -> None:
        """
        Apply global policy based on `debug`, without overriding values explicitly set by CLI.
        """
        if self.debug:
            if not self.is_explicit("fluorescence_show_scattering_controls"):
                self.fluorescence_show_scattering_controls = True
            if not self.is_explicit("fluorescence_show_threshold_controls"):
                self.fluorescence_show_threshold_controls = True

            if not self.is_explicit("fluorescence_debug_scattering"):
                self.fluorescence_debug_scattering = True
            if not self.is_explicit("fluorescence_debug_fluorescence"):
                self.fluorescence_debug_fluorescence = True
        else:
            if not self.is_explicit("fluorescence_show_scattering_controls"):
                self.fluorescence_show_scattering_controls = False
            if not self.is_explicit("fluorescence_show_threshold_controls"):
                self.fluorescence_show_threshold_controls = False

            if not self.is_explicit("fluorescence_debug_scattering"):
                self.fluorescence_debug_scattering = False
            if not self.is_explicit("fluorescence_debug_fluorescence"):
                self.fluorescence_debug_fluorescence = False


_runtime_config: Optional[RuntimeConfig] = None


def get_runtime_config() -> RuntimeConfig:
    global _runtime_config
    if _runtime_config is None:
        _runtime_config = RuntimeConfig()
        _runtime_config.apply_policy()
    return _runtime_config