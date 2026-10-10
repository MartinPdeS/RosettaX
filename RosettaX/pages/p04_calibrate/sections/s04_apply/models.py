"""Named controls and prepared downloads for calibration export."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplyCalibrationControls:
    uploaded_fcs_path: Any
    export_columns: Any
    selected_calibration_summary: Any
    target_model_preset: Any
    advanced_monotonic_mode_enabled: Any
    use_monotonic_smoothing_kernel: Any
    monotonic_smoothing_sigma_points: Any
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


@dataclass(frozen=True)
class CalibrationExportResult:
    status: str
    payload_bytes: bytes | None = None
    download_filename: str | None = None
    report_payload: dict[str, Any] | None = None
