from __future__ import annotations

import logging
from dataclasses import asdict, replace
from typing import TYPE_CHECKING, Any

from RosettaX.utils import RuntimeConfig, casting, styling
from RosettaX.workflow.constants import DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE
from RosettaX.workflow.peak.core import detectors as peak_detectors
from RosettaX.workflow.plotting import optical_preview
from RosettaX.workflow.scattering import ModelConfiguration

from .models import (
    DetectorGeometryValues,
    OpticalPreviewControls,
    OpticalPreviewUpdate,
    ProfileParameterState,
)

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)

DETECTOR_NUMERICAL_APERTURE_EPSILON = 1e-6


def resolve_profile_parameter_state(
    runtime_config_data: Any,
    *,
    configuration: type[ModelConfiguration] = ModelConfiguration,
) -> ProfileParameterState:
    """Resolve profile controls by name before translating them to Dash outputs."""
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None,
    )
    values = configuration.build_defaults_from_runtime_config(runtime_config_data)
    detector_preset = configuration.resolve_runtime_detector_preset(
        runtime_config.get_str("optics.detector_configuration_preset", default=""),
    )
    geometry = DetectorGeometryValues(
        *configuration.resolve_detector_configuration_values(
            preset_name=detector_preset,
            current_detector_numerical_aperture=values.detector_numerical_aperture,
            current_detector_cache_numerical_aperture=values.detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=values.blocker_bar_numerical_aperture,
            current_detector_sampling=values.detector_sampling,
            current_detector_phi_angle_degree=values.detector_phi_angle_degree,
            current_detector_gamma_angle_degree=values.detector_gamma_angle_degree,
        )
    )
    values = replace(
        values,
        wavelength_nm=configuration.resolve_detector_preset_wavelength_nm(
            preset_name=detector_preset,
            current_wavelength_nm=values.wavelength_nm,
        ),
        **asdict(geometry),
    )
    scatterer_preset = configuration.resolve_runtime_scatterer_preset(
        runtime_config.get_str("particle_model.scatterer_preset", default=""),
    )
    if configuration.scatterer_preset_disables_manual_controls(
        preset_name=scatterer_preset
    ):
        (
            mie_model,
            _medium_source,
            medium_refractive_index,
            _particle_source,
            particle_refractive_index,
            _core_source,
            core_refractive_index,
            _shell_source,
            shell_refractive_index,
        ) = configuration.resolve_scatterer_preset_values(
            preset_name=scatterer_preset,
            current_mie_model=values.mie_model,
            current_medium_refractive_index_source=None,
            current_medium_refractive_index=values.medium_refractive_index,
            current_particle_refractive_index_source=None,
            current_particle_refractive_index=values.particle_refractive_index,
            current_core_refractive_index_source=None,
            current_core_refractive_index=values.core_refractive_index,
            current_shell_refractive_index_source=None,
            current_shell_refractive_index=values.shell_refractive_index,
            wavelength_nm=values.wavelength_nm,
        )
        values = replace(
            values,
            mie_model=mie_model,
            medium_refractive_index=medium_refractive_index,
            particle_refractive_index=particle_refractive_index,
            core_refractive_index=core_refractive_index,
            shell_refractive_index=shell_refractive_index,
        )
    values = replace(
        values,
        detector_cache_numerical_aperture=clamp_detector_cache_numerical_aperture(
            values.detector_numerical_aperture,
            values.detector_cache_numerical_aperture,
        ),
    )
    return ProfileParameterState(detector_preset or "", scatterer_preset, values)


def build_optical_preview_update(
    controls: OpticalPreviewControls,
    *,
    previous_signature: Any,
    relayout_data: Any,
    configuration: type[ModelConfiguration] = ModelConfiguration,
) -> OpticalPreviewUpdate | None:
    """Build a changed preview while retaining the browser's camera orientation."""
    preview_parameters = configuration.resolve_optical_configuration_preview_parameters(
        **controls.to_workflow_parameters(),
        polarization_angle_degree=DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
        camera=optical_preview.resolve_locked_camera_from_relayout_data(
            relayout_data=relayout_data
        ),
    )
    signature = optical_preview.build_optical_configuration_preview_signature(
        preview_parameters
    )
    if signature == previous_signature:
        return None
    figure = optical_preview.build_optical_configuration_preview_figure(
        **preview_parameters
    )
    return OpticalPreviewUpdate(figure, signature)


def build_parameter_group_style(
    *,
    is_visible: bool,
) -> dict[str, str]:
    """
    Build a consistent layout style for model-specific parameter groups.
    """
    return {
        "display": "flex" if is_visible else "none",
        "flexDirection": "column",
        "gap": styling.get_spacing_token("xs"),
        "overflow": "visible",
    }


def resolve_show_preset_configuration(
    runtime_config_data: Any,
) -> bool:
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    return runtime_config.get_bool(
        "ui.show_preset_configuration",
        default=False,
    )


def should_show_detector_preset_configuration(
    section: Model,
    *,
    preset_name: Any,
    show_preset_configuration: bool,
) -> bool:
    normalized_preset_name = str(preset_name or "").strip()

    if (
        normalized_preset_name
        == section.model_configuration.custom_detector_preset_name
    ):
        return True

    return bool(show_preset_configuration and normalized_preset_name)


def should_show_scatterer_preset_configuration(
    section: Model,
    *,
    preset_name: Any,
    show_preset_configuration: bool,
) -> bool:
    normalized_preset_name = str(preset_name or "").strip()

    if (
        normalized_preset_name
        == section.model_configuration.custom_scatterer_preset_name
    ):
        return True

    return bool(show_preset_configuration and normalized_preset_name)


def clamp_detector_cache_numerical_aperture(
    detector_numerical_aperture: Any,
    detector_cache_numerical_aperture: Any,
) -> Any:
    """
    Keep detector cache numerical aperture within the detector aperture.
    """
    resolved_detector_numerical_aperture = casting.as_optional_float(
        detector_numerical_aperture
    )
    resolved_detector_cache_numerical_aperture = casting.as_optional_float(
        detector_cache_numerical_aperture
    )

    if resolved_detector_numerical_aperture is None:
        return detector_cache_numerical_aperture

    if resolved_detector_cache_numerical_aperture is None:
        return detector_cache_numerical_aperture

    strict_upper_bound = max(
        0.0,
        resolved_detector_numerical_aperture - DETECTOR_NUMERICAL_APERTURE_EPSILON,
    )

    if (
        resolved_detector_cache_numerical_aperture
        < resolved_detector_numerical_aperture
    ):
        return detector_cache_numerical_aperture

    logger.debug(
        "Clamping detector cache numerical aperture from %r to strict upper bound %r below detector numerical aperture %r.",
        detector_cache_numerical_aperture,
        strict_upper_bound,
        detector_numerical_aperture,
    )

    return strict_upper_bound


def resolve_selected_peak_detector_channel(
    *,
    selected_peak_process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
) -> Any:
    """
    Resolve the peak detector channel currently driving scattering calibration.
    """
    channel_values = peak_detectors.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=selected_peak_process_name,
    )

    for channel_name in ("primary", "scattering", "scattering_axis", "x_axis", "x"):
        resolved_channel = channel_values.get(channel_name)

        if resolved_channel:
            return resolved_channel

    return None


def build_section(*args, **kwargs) -> Model:
    """Build the optical configuration section."""
    from .main import Model

    return Model(*args, **kwargs)
