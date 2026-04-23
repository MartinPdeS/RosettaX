# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Any

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import casting, directories


def build_profile_options() -> list[dict[str, str]]:
    profile_names = directories.list_profiles()
    return [{"label": profile_name, "value": profile_name} for profile_name in profile_names]


def resolve_default_profile_value(profile_options: list[dict[str, str]]) -> str | None:
    if not profile_options:
        return None
    return str(profile_options[0]["value"])


def get_saved_profile(profile_name: str) -> dict[str, Any] | None:
    profile_path = Path(directories.profiles) / f"{profile_name}.json"
    if not profile_path.exists():
        return None

    runtime_config = RuntimeConfig.from_json_path(profile_path)
    return runtime_config.to_dict()


def flatten_runtime_config(runtime_config: RuntimeConfig) -> dict[str, Any]:
    return {
        "medium_refractive_index": runtime_config.get_float("optics.medium_refractive_index", default=1.334),
        "core_refractive_index": runtime_config.get_float("particle_model.core_refractive_index", default=1.5),
        "shell_refractive_index": runtime_config.get_float("particle_model.shell_refractive_index", default=1.5),
        "shell_thickness_nm": runtime_config.get_path("particle_model.shell_thickness_nm", default=[]),
        "core_diameter_nm": runtime_config.get_path("particle_model.core_diameter_nm", default=[]),
        "particle_diameter_nm": runtime_config.get_path("particle_model.particle_diameter_nm", default=[]),
        "particle_refractive_index": runtime_config.get_float("particle_model.particle_refractive_index", default=1.59),
        "wavelength_nm": runtime_config.get_float("optics.wavelength_nm", default=488.0),
        "max_events_for_analysis": runtime_config.get_int("calibration.max_events_for_analysis", default=100),
        "n_bins_for_plots": runtime_config.get_int("calibration.n_bins_for_plots", default=100),
        "peak_count": runtime_config.get_int("calibration.peak_count", default=4),
        "mie_model": runtime_config.get_str("particle_model.mie_model", default="Solid Sphere"),
        "mesf_values": runtime_config.get_path("calibration.mesf_values", default=[]),
        "fluorescence_fcs_file_path": runtime_config.get_path("files.fluorescence_fcs_file_path", default=None),
        "scattering_fcs_file_path": runtime_config.get_path("files.scattering_fcs_file_path", default=None),
        "default_gating_channel": runtime_config.get_path("calibration.default_gating_channel", default=None),
        "default_gating_threshold": runtime_config.get_path("calibration.default_gating_threshold", default=None),
        "show_calibration_plot_by_default": runtime_config.get_bool(
            "calibration.show_calibration_plot_by_default",
            default=False,
        ),
        "histogram_scale": runtime_config.get_str("calibration.histogram_scale", default="log"),
        "default_output_suffix": runtime_config.get_str("calibration.default_output_suffix", default="_calibrated"),
        "operator_name": runtime_config.get_str("metadata.operator_name", default=""),
        "instrument_name": runtime_config.get_str("metadata.instrument_name", default=""),
        "theme_mode": runtime_config.get_theme_mode(default="dark"),
        "show_graphs": runtime_config.get_show_graphs(default=False),
        "default_marker_size": runtime_config.get_float("visualization.default_marker_size", default=8.0),
        "default_line_width": runtime_config.get_float("visualization.default_line_width", default=2.0),
        "show_grid_by_default": runtime_config.get_bool("visualization.show_grid_by_default", default=True),
    }


def build_flat_runtime_payload_from_form_values(form_values: tuple[Any, ...]) -> dict[str, Any]:
    if len(form_values) != 27:
        raise ValueError(f"Expected 27 form values, received {len(form_values)}.")

    (
        medium_refractive_index,
        core_refractive_index,
        shell_refractive_index,
        shell_thickness_nm,
        core_diameter_nm,
        particle_diameter_nm,
        particle_refractive_index,
        wavelength_nm,
        max_events_for_analysis,
        n_bins_for_plots,
        peak_count,
        mie_model,
        mesf_values,
        fluorescence_fcs_file_path,
        scattering_fcs_file_path,
        default_gating_channel,
        default_gating_threshold,
        show_calibration_plot_by_default,
        histogram_scale,
        default_output_suffix,
        operator_name,
        instrument_name,
        theme_mode,
        show_graphs,
        default_marker_size,
        default_line_width,
        show_grid_by_default,
    ) = form_values

    return {
        "medium_refractive_index": casting.as_optional_float(medium_refractive_index),
        "core_refractive_index": casting.as_optional_float(core_refractive_index),
        "shell_refractive_index": casting.as_optional_float(shell_refractive_index),
        "shell_thickness_nm": casting.parse_float_list(shell_thickness_nm),
        "core_diameter_nm": casting.parse_float_list(core_diameter_nm),
        "particle_diameter_nm": casting.parse_float_list(particle_diameter_nm),
        "particle_refractive_index": casting.as_optional_float(particle_refractive_index),
        "wavelength_nm": casting.as_optional_float(wavelength_nm),
        "max_events_for_analysis": casting.as_optional_int(max_events_for_analysis),
        "n_bins_for_plots": casting.as_optional_int(n_bins_for_plots),
        "peak_count": casting.as_optional_int(peak_count),
        "mie_model": casting.coerce_optional_string(mie_model),
        "mesf_values": casting.parse_float_list(mesf_values),
        "fluorescence_fcs_file_path": casting.coerce_optional_string(fluorescence_fcs_file_path),
        "scattering_fcs_file_path": casting.coerce_optional_string(scattering_fcs_file_path),
        "default_gating_channel": casting.coerce_optional_string(default_gating_channel),
        "default_gating_threshold": casting.as_optional_float(default_gating_threshold),
        "show_calibration_plot_by_default": str(show_calibration_plot_by_default).strip().lower() == "yes",
        "histogram_scale": casting.coerce_optional_string(histogram_scale) or "log",
        "default_output_suffix": casting.coerce_optional_string(default_output_suffix),
        "operator_name": casting.coerce_optional_string(operator_name),
        "instrument_name": casting.coerce_optional_string(instrument_name),
        "theme_mode": casting.coerce_optional_string(theme_mode) or "dark",
        "show_graphs": str(show_graphs).strip().lower() == "yes",
        "default_marker_size": casting.as_optional_float(default_marker_size),
        "default_line_width": casting.as_optional_float(default_line_width),
        "show_grid_by_default": str(show_grid_by_default).strip().lower() == "yes",
    }


def build_nested_profile_payload(flat_runtime_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "optics": {
            "medium_refractive_index": flat_runtime_payload.get("medium_refractive_index"),
            "wavelength_nm": flat_runtime_payload.get("wavelength_nm"),
        },
        "particle_model": {
            "core_refractive_index": flat_runtime_payload.get("core_refractive_index"),
            "shell_refractive_index": flat_runtime_payload.get("shell_refractive_index"),
            "shell_thickness_nm": flat_runtime_payload.get("shell_thickness_nm"),
            "core_diameter_nm": flat_runtime_payload.get("core_diameter_nm"),
            "particle_diameter_nm": flat_runtime_payload.get("particle_diameter_nm"),
            "particle_refractive_index": flat_runtime_payload.get("particle_refractive_index"),
            "mie_model": flat_runtime_payload.get("mie_model"),
        },
        "calibration": {
            "mesf_values": flat_runtime_payload.get("mesf_values"),
            "max_events_for_analysis": flat_runtime_payload.get("max_events_for_analysis"),
            "n_bins_for_plots": flat_runtime_payload.get("n_bins_for_plots"),
            "peak_count": flat_runtime_payload.get("peak_count"),
            "default_gating_channel": flat_runtime_payload.get("default_gating_channel"),
            "default_gating_threshold": flat_runtime_payload.get("default_gating_threshold"),
            "show_calibration_plot_by_default": flat_runtime_payload.get("show_calibration_plot_by_default"),
            "histogram_scale": flat_runtime_payload.get("histogram_scale"),
            "default_output_suffix": flat_runtime_payload.get("default_output_suffix"),
        },
        "metadata": {
            "operator_name": flat_runtime_payload.get("operator_name"),
            "instrument_name": flat_runtime_payload.get("instrument_name"),
        },
        "files": {
            "fluorescence_fcs_file_path": flat_runtime_payload.get("fluorescence_fcs_file_path"),
            "scattering_fcs_file_path": flat_runtime_payload.get("scattering_fcs_file_path"),
        },
        "ui": {
            "theme_mode": flat_runtime_payload.get("theme_mode"),
            "show_graphs": flat_runtime_payload.get("show_graphs"),
        },
        "visualization": {
            "default_marker_size": flat_runtime_payload.get("default_marker_size"),
            "default_line_width": flat_runtime_payload.get("default_line_width"),
            "show_grid_by_default": flat_runtime_payload.get("show_grid_by_default"),
        },
    }


def save_profile(profile_name: str, nested_profile_payload: dict[str, Any]) -> None:
    profile_path = Path(directories.profiles) / f"{profile_name}.json"
    runtime_config = RuntimeConfig.from_dict(nested_profile_payload)
    runtime_config.to_json_path(profile_path)