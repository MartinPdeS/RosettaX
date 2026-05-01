# -*- coding: utf-8 -*-

from typing import Any
import logging

import numpy as np

from RosettaX.pages.p03_scattering.backend import BackEnd
from RosettaX.workflow.calibration.mie_relation import MieRelation
from RosettaX.workflow.calibration.mie_relation import build_diameter_grid
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload
from RosettaX.workflow.calibration.mie_relation import build_mie_relation_from_arrays
from RosettaX.workflow.apply_calibration.scattering.models import (
    CORE_SHELL_SPHERE_MODEL_NAME,
    CoreShellSphereTargetModel,
    ScatteringTargetModelParameters,
    SolidSphereTargetModel,
)


logger = logging.getLogger(__name__)


def build_target_mie_relation(
    *,
    calibration_payload: dict[str, Any],
    target_model_parameters: ScatteringTargetModelParameters,
) -> MieRelation:
    """
    Build the target particle Mie relation used for diameter inversion.

    Solid Sphere
    ------------
    The diameter axis is the full particle diameter.

    Core/Shell Sphere
    -----------------
    The diameter axis is the core diameter. The shell thickness is constant and
    supplied by the user.
    """
    logger.debug(
        "build_target_mie_relation called with target_model_parameters=%r",
        target_model_parameters,
    )

    calibration_standard_parameters = get_calibration_standard_parameters(
        calibration_payload,
    )

    logger.debug(
        "build_target_mie_relation resolved calibration_standard_parameter_keys=%r",
        sorted(calibration_standard_parameters.keys()),
    )

    if isinstance(
        target_model_parameters.target_model,
        CoreShellSphereTargetModel,
    ):
        return build_core_shell_target_mie_relation(
            calibration_standard_parameters=calibration_standard_parameters,
            target_model=target_model_parameters.target_model,
        )

    if isinstance(
        target_model_parameters.target_model,
        SolidSphereTargetModel,
    ):
        return build_solid_sphere_target_mie_relation(
            calibration_standard_parameters=calibration_standard_parameters,
            target_model=target_model_parameters.target_model,
        )

    raise TypeError(
        f"Unsupported target model type: {type(target_model_parameters.target_model).__name__}."
    )


def build_solid_sphere_target_mie_relation(
    *,
    calibration_standard_parameters: dict[str, Any],
    target_model: SolidSphereTargetModel,
) -> MieRelation:
    """
    Build a solid sphere target Mie relation.

    The relation diameter axis is particle diameter.
    """
    logger.debug(
        "build_solid_sphere_target_mie_relation called with target_model=%r",
        target_model,
    )

    diameter_grid_nm = build_diameter_grid(
        diameter_min_nm=target_model.particle_diameter_min_nm,
        diameter_max_nm=target_model.particle_diameter_max_nm,
        diameter_count=target_model.particle_diameter_count,
    )

    optical_geometry = parse_optical_geometry_from_calibration_standard_parameters(
        calibration_standard_parameters,
    )

    modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
        particle_diameters_nm=diameter_grid_nm,
        wavelength_nm=optical_geometry["wavelength_nm"],
        source_numerical_aperture=optical_geometry["source_numerical_aperture"],
        optical_power_watt=optical_geometry["optical_power_watt"],
        detector_numerical_aperture=optical_geometry["detector_numerical_aperture"],
        medium_refractive_index=target_model.medium_refractive_index,
        particle_refractive_index=target_model.particle_refractive_index,
        detector_cache_numerical_aperture=optical_geometry["detector_cache_numerical_aperture"],
        detector_phi_offset_degree=optical_geometry["detector_phi_angle_degree"],
        detector_gamma_offset_degree=optical_geometry["detector_gamma_angle_degree"],
        polarization_angle_degree=optical_geometry["polarization_angle_degree"],
        detector_sampling=optical_geometry["detector_sampling"],
    )

    relation_diameter_nm = np.asarray(
        modeled_coupling_result.particle_diameters_nm,
        dtype=float,
    ).reshape(-1)

    theoretical_coupling = np.asarray(
        modeled_coupling_result.expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    _validate_same_size(
        first_values=relation_diameter_nm,
        second_values=theoretical_coupling,
        first_name="relation_diameter_nm",
        second_name="theoretical_coupling",
    )

    parameter_payload = build_target_relation_parameter_payload(
        calibration_standard_parameters=calibration_standard_parameters,
        target_model=target_model,
        optical_geometry=optical_geometry,
    )

    logger.debug(
        "build_solid_sphere_target_mie_relation returning relation with point_count=%r",
        relation_diameter_nm.size,
    )

    return build_mie_relation_from_arrays(
        diameter_nm=relation_diameter_nm,
        theoretical_coupling=theoretical_coupling,
        mie_model=target_model.mie_model,
        parameters=parameter_payload,
        relation_role="target_particle",
    )


def build_core_shell_target_mie_relation(
    *,
    calibration_standard_parameters: dict[str, Any],
    target_model: CoreShellSphereTargetModel,
) -> MieRelation:
    """
    Build a core shell target Mie relation.

    The relation diameter axis is core diameter. Shell thickness is fixed.
    """
    logger.debug(
        "build_core_shell_target_mie_relation called with target_model=%r",
        target_model,
    )

    core_diameter_grid_nm = build_diameter_grid(
        diameter_min_nm=target_model.core_diameter_min_nm,
        diameter_max_nm=target_model.core_diameter_max_nm,
        diameter_count=target_model.core_diameter_count,
    )

    shell_thicknesses_nm = np.full(
        core_diameter_grid_nm.size,
        float(target_model.shell_thickness_nm),
        dtype=float,
    )

    optical_geometry = parse_optical_geometry_from_calibration_standard_parameters(
        calibration_standard_parameters,
    )

    modeled_coupling_result = BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
        core_diameters_nm=core_diameter_grid_nm,
        shell_thicknesses_nm=shell_thicknesses_nm,
        wavelength_nm=optical_geometry["wavelength_nm"],
        source_numerical_aperture=optical_geometry["source_numerical_aperture"],
        optical_power_watt=optical_geometry["optical_power_watt"],
        detector_numerical_aperture=optical_geometry["detector_numerical_aperture"],
        medium_refractive_index=target_model.medium_refractive_index,
        core_refractive_index=target_model.core_refractive_index,
        shell_refractive_index=target_model.shell_refractive_index,
        detector_cache_numerical_aperture=optical_geometry["detector_cache_numerical_aperture"],
        detector_phi_offset_degree=optical_geometry["detector_phi_angle_degree"],
        detector_gamma_offset_degree=optical_geometry["detector_gamma_angle_degree"],
        polarization_angle_degree=optical_geometry["polarization_angle_degree"],
        detector_sampling=optical_geometry["detector_sampling"],
    )

    relation_diameter_nm = np.asarray(
        core_diameter_grid_nm,
        dtype=float,
    ).reshape(-1)

    theoretical_coupling = np.asarray(
        modeled_coupling_result.expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    _validate_same_size(
        first_values=relation_diameter_nm,
        second_values=theoretical_coupling,
        first_name="relation_diameter_nm",
        second_name="theoretical_coupling",
    )

    parameter_payload = build_target_relation_parameter_payload(
        calibration_standard_parameters=calibration_standard_parameters,
        target_model=target_model,
        optical_geometry=optical_geometry,
    )

    logger.debug(
        "build_core_shell_target_mie_relation returning relation with point_count=%r "
        "core_diameter_min_nm=%r core_diameter_max_nm=%r shell_thickness_nm=%r",
        relation_diameter_nm.size,
        target_model.core_diameter_min_nm,
        target_model.core_diameter_max_nm,
        target_model.shell_thickness_nm,
    )

    return build_mie_relation_from_arrays(
        diameter_nm=relation_diameter_nm,
        theoretical_coupling=theoretical_coupling,
        mie_model=CORE_SHELL_SPHERE_MODEL_NAME,
        parameters=parameter_payload,
        relation_role="target_particle",
    )


def build_target_relation_parameter_payload(
    *,
    calibration_standard_parameters: dict[str, Any],
    target_model: SolidSphereTargetModel | CoreShellSphereTargetModel,
    optical_geometry: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the serializable parameter payload stored in the target Mie relation.
    """
    parameter_payload = build_mie_parameter_payload(
        mie_model=target_model.mie_model,
        medium_refractive_index=target_model.medium_refractive_index,
        particle_refractive_index=(
            target_model.particle_refractive_index
            if isinstance(target_model, SolidSphereTargetModel)
            else None
        ),
        core_refractive_index=(
            target_model.core_refractive_index
            if isinstance(target_model, CoreShellSphereTargetModel)
            else None
        ),
        shell_refractive_index=(
            target_model.shell_refractive_index
            if isinstance(target_model, CoreShellSphereTargetModel)
            else None
        ),
        wavelength_nm=optical_geometry["wavelength_nm"],
        detector_numerical_aperture=optical_geometry["detector_numerical_aperture"],
        detector_cache_numerical_aperture=optical_geometry["detector_cache_numerical_aperture"],
        blocker_bar_numerical_aperture=calibration_standard_parameters.get(
            "blocker_bar_numerical_aperture",
            None,
        ),
        detector_sampling=optical_geometry["detector_sampling"],
        detector_phi_angle_degree=optical_geometry["detector_phi_angle_degree"],
        detector_gamma_angle_degree=optical_geometry["detector_gamma_angle_degree"],
        diameter_min_nm=target_model.diameter_min_nm,
        diameter_max_nm=target_model.diameter_max_nm,
        diameter_count=target_model.diameter_count,
    )

    parameter_payload.update(
        target_model.to_parameter_payload(),
    )

    parameter_payload.update(
        {
            "optical_power_watt": optical_geometry["optical_power_watt"],
            "source_numerical_aperture": optical_geometry["source_numerical_aperture"],
            "polarization_angle_degree": optical_geometry["polarization_angle_degree"],
            "extrapolation_enabled": True,
            "non_monotonic_policy": "auto_largest_branch",
        }
    )

    return parameter_payload


def parse_optical_geometry_from_calibration_standard_parameters(
    calibration_standard_parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Parse optical geometry parameters from a saved scattering calibration.
    """
    optical_geometry = {
        "optical_power_watt": float(
            calibration_standard_parameters.get(
                "optical_power_watt",
                1.0,
            )
        ),
        "source_numerical_aperture": float(
            calibration_standard_parameters.get(
                "source_numerical_aperture",
                0.1,
            )
        ),
        "wavelength_nm": float(
            calibration_standard_parameters.get(
                "wavelength_nm",
            )
        ),
        "detector_numerical_aperture": float(
            calibration_standard_parameters.get(
                "detector_numerical_aperture",
            )
        ),
        "detector_cache_numerical_aperture": float(
            calibration_standard_parameters.get(
                "detector_cache_numerical_aperture",
                0.0,
            )
        ),
        "detector_phi_angle_degree": float(
            calibration_standard_parameters.get(
                "detector_phi_angle_degree",
                0.0,
            )
        ),
        "detector_gamma_angle_degree": float(
            calibration_standard_parameters.get(
                "detector_gamma_angle_degree",
                0.0,
            )
        ),
        "polarization_angle_degree": float(
            calibration_standard_parameters.get(
                "polarization_angle_degree",
                0.0,
            )
        ),
        "detector_sampling": int(
            calibration_standard_parameters.get(
                "detector_sampling",
                600,
            )
        ),
    }

    logger.debug(
        "parse_optical_geometry_from_calibration_standard_parameters returning optical_geometry=%r",
        optical_geometry,
    )

    return optical_geometry


def get_calibration_standard_parameters(
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve optical geometry parameters stored in a scattering calibration.
    """
    logger.debug(
        "get_calibration_standard_parameters called with payload_keys=%r",
        sorted(calibration_payload.keys()) if isinstance(calibration_payload, dict) else None,
    )

    mie_relation_payload = calibration_payload.get(
        "calibration_standard_mie_relation",
    )

    if isinstance(mie_relation_payload, dict):
        relation_parameters = mie_relation_payload.get(
            "parameters",
        )

        if isinstance(relation_parameters, dict):
            logger.debug(
                "get_calibration_standard_parameters using calibration_standard_mie_relation parameters keys=%r",
                sorted(relation_parameters.keys()),
            )

            return dict(
                relation_parameters,
            )

    metadata = calibration_payload.get(
        "metadata",
    )

    if isinstance(metadata, dict):
        calibration_standard_parameters = metadata.get(
            "calibration_standard_parameters",
        )

        if isinstance(calibration_standard_parameters, dict):
            logger.debug(
                "get_calibration_standard_parameters using metadata calibration_standard_parameters keys=%r",
                sorted(calibration_standard_parameters.keys()),
            )

            return dict(
                calibration_standard_parameters,
            )

    raise ValueError(
        "Scattering calibration payload is missing calibration standard optical parameters."
    )


def _validate_same_size(
    *,
    first_values: Any,
    second_values: Any,
    first_name: str,
    second_name: str,
) -> None:
    """
    Validate that two arrays have the same flattened size.
    """
    first_array = np.asarray(
        first_values,
    ).reshape(-1)

    second_array = np.asarray(
        second_values,
    ).reshape(-1)

    if first_array.size == second_array.size:
        return

    raise ValueError(
        f"{first_name} and {second_name} must have the same length. "
        f"Got {first_array.size} and {second_array.size}."
    )