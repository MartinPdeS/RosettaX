# -*- coding: utf-8 -*-

from typing import Any

import numpy as np


def validate_optical_parameters(optical_parameters: Any) -> None:
    """Validate the physical domain of scattering optical parameters."""
    positive_fields = (
        "medium_refractive_index",
        "wavelength_nm",
        "detector_numerical_aperture",
        "particle_refractive_index",
        "core_refractive_index",
        "shell_refractive_index",
    )

    for field_name in positive_fields:
        value = getattr(optical_parameters, field_name)
        if value is None:
            continue
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{field_name} must be a finite value greater than zero. "
                f"Received {value!r}."
            )

    if optical_parameters.detector_sampling < 2:
        raise ValueError(
            "detector_sampling must be an integer of at least 2. "
            f"Received {optical_parameters.detector_sampling!r}."
        )

    for field_name in (
        "detector_cache_numerical_aperture",
        "blocker_bar_numerical_aperture",
        "source_numerical_aperture",
        "optical_power_watt",
    ):
        value = getattr(optical_parameters, field_name)
        if not np.isfinite(value) or value < 0.0:
            raise ValueError(
                f"{field_name} must be a finite non-negative value. "
                f"Received {value!r}."
            )

    if optical_parameters.optical_power_watt == 0.0:
        raise ValueError("optical_power_watt must be greater than zero.")

    if (
        optical_parameters.detector_cache_numerical_aperture
        > optical_parameters.detector_numerical_aperture
    ):
        raise ValueError(
            "detector_cache_numerical_aperture cannot exceed "
            "detector_numerical_aperture."
        )

    if (
        optical_parameters.blocker_bar_numerical_aperture
        > optical_parameters.detector_numerical_aperture
    ):
        raise ValueError(
            "blocker_bar_numerical_aperture cannot exceed "
            "detector_numerical_aperture."
        )

    for field_name in (
        "detector_phi_angle_degree",
        "detector_gamma_angle_degree",
        "polarization_angle_degree",
    ):
        value = getattr(optical_parameters, field_name)
        if not np.isfinite(value):
            raise ValueError(
                f"{field_name} must be finite. Received {value!r}."
            )
