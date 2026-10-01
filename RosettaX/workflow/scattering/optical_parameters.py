"""Scattering optical parameters."""

import logging
from typing import Any

from RosettaX.utils import casting
from RosettaX.workflow import detector

from .calibration_models import OpticalParameters
from .validation import validate_optical_parameters

logger = logging.getLogger(__name__)


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Normalize the selected Mie model name.
    """
    mie_model_string = "" if mie_model is None else str(mie_model).strip()

    if mie_model_string == "Core/Shell Sphere":
        resolved_mie_model = "Core/Shell Sphere"
    else:
        resolved_mie_model = "Solid Sphere"

    logger.debug(
        "resolve_mie_model called with mie_model=%r resolved_mie_model=%r",
        mie_model,
        resolved_mie_model,
    )

    return resolved_mie_model


def parse_optical_parameters(
    *,
    medium_refractive_index: Any,
    particle_refractive_index: Any,
    core_refractive_index: Any,
    shell_refractive_index: Any,
    wavelength_nm: Any,
    detector_numerical_aperture: Any,
    detector_cache_numerical_aperture: Any,
    blocker_bar_numerical_aperture: Any,
    detector_sampling: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
    detector_configuration_preset: Any = None,
    detector_angular_weighting_json: Any = None,
) -> OpticalParameters:
    """
    Parse raw callback values into typed optical parameters.
    """
    logger.debug(
        "parse_optical_parameters called with medium_refractive_index=%r "
        "particle_refractive_index=%r core_refractive_index=%r "
        "shell_refractive_index=%r wavelength_nm=%r "
        "detector_numerical_aperture=%r detector_cache_numerical_aperture=%r "
        "blocker_bar_numerical_aperture=%r detector_sampling=%r "
        "detector_phi_angle_degree=%r detector_gamma_angle_degree=%r "
        "detector_configuration_preset=%r detector_angular_weighting_json=%r",
        medium_refractive_index,
        particle_refractive_index,
        core_refractive_index,
        shell_refractive_index,
        wavelength_nm,
        detector_numerical_aperture,
        detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture,
        detector_sampling,
        detector_phi_angle_degree,
        detector_gamma_angle_degree,
        detector_configuration_preset,
        detector_angular_weighting_json,
    )

    resolved_detector_sampling = casting.as_required_int(
        detector_sampling,
        "detector_sampling",
    )
    resolved_detector_configuration_preset_name = (
        ""
        if detector_configuration_preset is None
        else str(detector_configuration_preset)
    )
    resolved_detector_cache_numerical_aperture = (
        casting.as_optional_float(detector_cache_numerical_aperture) or 0.0
    )
    resolved_blocker_bar_numerical_aperture = (
        casting.as_optional_float(blocker_bar_numerical_aperture) or 0.0
    )
    effective_detector_cache_numerical_aperture, effective_blocker_bar_numerical_aperture = (
        detector.resolve_detector_modeling_geometry_values(
            preset_name=resolved_detector_configuration_preset_name,
            current_detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
        )
    )

    optical_parameters = OpticalParameters(
        medium_refractive_index=casting.as_required_float(
            medium_refractive_index,
            "medium_refractive_index",
        ),
        particle_refractive_index=casting.as_optional_float(
            particle_refractive_index,
        ),
        core_refractive_index=casting.as_optional_float(
            core_refractive_index,
        ),
        shell_refractive_index=casting.as_optional_float(
            shell_refractive_index,
        ),
        wavelength_nm=casting.as_required_float(
            wavelength_nm,
            "wavelength_nm",
        ),
        detector_numerical_aperture=casting.as_required_float(
            detector_numerical_aperture,
            "detector_numerical_aperture",
        ),
        detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
        detector_sampling=resolved_detector_sampling,
        detector_phi_angle_degree=casting.as_required_float(
            detector_phi_angle_degree,
            "detector_phi_angle_degree",
        ),
        detector_gamma_angle_degree=casting.as_required_float(
            detector_gamma_angle_degree,
            "detector_gamma_angle_degree",
        ),
        detector_configuration_preset_name=resolved_detector_configuration_preset_name,
        detector_angular_weights=detector.resolve_detector_angular_weights(
            preset_name=detector_configuration_preset,
            detector_sampling=resolved_detector_sampling,
            current_detector_numerical_aperture=casting.as_required_float(
                detector_numerical_aperture,
                "detector_numerical_aperture",
            ),
            current_detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
            current_detector_phi_angle_degree=casting.as_required_float(
                detector_phi_angle_degree,
                "detector_phi_angle_degree",
            ),
            current_detector_gamma_angle_degree=casting.as_required_float(
                detector_gamma_angle_degree,
                "detector_gamma_angle_degree",
            ),
            current_medium_refractive_index=casting.as_required_float(
                medium_refractive_index,
                "medium_refractive_index",
            ),
            current_detector_angular_weighting=detector_angular_weighting_json,
        ),
        effective_detector_cache_numerical_aperture=float(
            effective_detector_cache_numerical_aperture
        ),
        effective_blocker_bar_numerical_aperture=float(
            effective_blocker_bar_numerical_aperture
        ),
    )

    validate_optical_parameters(optical_parameters)

    logger.debug(
        "parse_optical_parameters returning optical_parameters=%r",
        optical_parameters,
    )

    return optical_parameters
