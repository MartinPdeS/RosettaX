"""Named input and output state for target Mie relation previews."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TargetMiePreviewControls:
    selected_calibration_summary: Any
    target_mie_model: Any
    target_medium_refractive_index: Any
    target_particle_refractive_index: Any
    target_solid_sphere_diameter_min_nm: Any
    target_solid_sphere_diameter_max_nm: Any
    target_solid_sphere_diameter_count: Any
    target_core_refractive_index: Any
    target_shell_refractive_index: Any
    target_shell_thickness_nm: Any
    target_core_shell_core_diameter_min_nm: Any
    target_core_shell_core_diameter_max_nm: Any
    target_core_shell_core_diameter_count: Any
    target_model_preset: Any
    advanced_monotonic_mode_enabled: Any
    use_monotonic_smoothing_kernel: Any
    monotonic_smoothing_sigma_points: Any
    axis_scale_toggle_values: Any


@dataclass(frozen=True)
class TargetMiePreviewResult:
    figure: Any
    status: str
    color: str

    def to_callback_values(self) -> tuple[Any, str, str]:
        return self.figure, self.status, self.color
