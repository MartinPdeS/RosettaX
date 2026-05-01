# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

from RosettaX.workflow import apply_calibration


logger = logging.getLogger(__name__)


def resolve_target_mie_model(
    target_mie_model: Any,
) -> str:
    """
    Normalize the target Mie model value.
    """
    target_mie_model_string = str(
        target_mie_model or "Solid Sphere",
    ).strip()

    normalized_target_mie_model = target_mie_model_string.lower()

    if normalized_target_mie_model in {
        "core/shell sphere",
        "core shell sphere",
        "core-shell sphere",
        "coreshell sphere",
        "core_shell_sphere",
    }:
        return "Core/Shell Sphere"

    return "Solid Sphere"


def build_scattering_target_model_parameters_if_required(
    *,
    selected_calibration_summary: Any,
    target_mie_model: Any,
    target_medium_refractive_index: Any,
    target_particle_refractive_index: Any,
    target_solid_sphere_diameter_min_nm: Any,
    target_solid_sphere_diameter_max_nm: Any,
    target_solid_sphere_diameter_count: Any,
    target_core_refractive_index: Any,
    target_shell_refractive_index: Any,
    target_shell_thickness_nm: Any,
    target_core_shell_core_diameter_min_nm: Any,
    target_core_shell_core_diameter_max_nm: Any,
    target_core_shell_core_diameter_count: Any,
) -> Optional[apply_calibration.ScatteringTargetModelParameters]:
    """
    Build scattering target model parameters when the selected calibration requires them.
    """
    logger.debug(
        "build_scattering_target_model_parameters_if_required called with "
        "selected_calibration_summary=%r target_mie_model=%r "
        "target_medium_refractive_index=%r target_particle_refractive_index=%r "
        "target_solid_sphere_diameter_min_nm=%r "
        "target_solid_sphere_diameter_max_nm=%r "
        "target_solid_sphere_diameter_count=%r "
        "target_core_refractive_index=%r target_shell_refractive_index=%r "
        "target_shell_thickness_nm=%r "
        "target_core_shell_core_diameter_min_nm=%r "
        "target_core_shell_core_diameter_max_nm=%r "
        "target_core_shell_core_diameter_count=%r",
        selected_calibration_summary,
        target_mie_model,
        target_medium_refractive_index,
        target_particle_refractive_index,
        target_solid_sphere_diameter_min_nm,
        target_solid_sphere_diameter_max_nm,
        target_solid_sphere_diameter_count,
        target_core_refractive_index,
        target_shell_refractive_index,
        target_shell_thickness_nm,
        target_core_shell_core_diameter_min_nm,
        target_core_shell_core_diameter_max_nm,
        target_core_shell_core_diameter_count,
    )

    if not isinstance(
        selected_calibration_summary,
        dict,
    ):
        logger.debug(
            "No scattering target model parameters required because selected_calibration_summary is not a dict."
        )

        return None

    requires_target_model = bool(
        selected_calibration_summary.get(
            "requires_target_model",
            False,
        )
    )

    if not requires_target_model:
        logger.debug(
            "No scattering target model parameters required because requires_target_model=False."
        )

        return None

    resolved_target_mie_model = resolve_target_mie_model(
        target_mie_model,
    )

    is_core_shell_model = resolved_target_mie_model == "Core/Shell Sphere"

    if is_core_shell_model:
        resolved_target_diameter_min_nm = target_core_shell_core_diameter_min_nm
        resolved_target_diameter_max_nm = target_core_shell_core_diameter_max_nm
        resolved_target_diameter_count = target_core_shell_core_diameter_count

    else:
        resolved_target_diameter_min_nm = target_solid_sphere_diameter_min_nm
        resolved_target_diameter_max_nm = target_solid_sphere_diameter_max_nm
        resolved_target_diameter_count = target_solid_sphere_diameter_count

    logger.debug(
        "Resolved scattering target diameter controls for mie_model=%r "
        "diameter_min_nm=%r diameter_max_nm=%r diameter_count=%r",
        resolved_target_mie_model,
        resolved_target_diameter_min_nm,
        resolved_target_diameter_max_nm,
        resolved_target_diameter_count,
    )

    target_model_parameters = apply_calibration.ScatteringTargetModelParameters.from_raw_values(
        target_mie_model=resolved_target_mie_model,
        target_medium_refractive_index=target_medium_refractive_index,
        target_particle_refractive_index=target_particle_refractive_index,
        target_core_refractive_index=target_core_refractive_index,
        target_shell_refractive_index=target_shell_refractive_index,
        target_shell_thickness_nm=target_shell_thickness_nm,
        target_diameter_min_nm=resolved_target_diameter_min_nm,
        target_diameter_max_nm=resolved_target_diameter_max_nm,
        target_diameter_count=resolved_target_diameter_count,
    )

    logger.debug(
        "Built scattering target model parameters=%r",
        target_model_parameters,
    )

    return target_model_parameters


def build_export_column_options_and_values(
    *,
    uploaded_fcs_path: Any,
    current_export_columns: Any,
) -> tuple[list[dict[str, str]], list[str]]:
    """
    Build export column dropdown options and preserve still valid selected values.
    """
    logger.debug(
        "build_export_column_options_and_values called with uploaded_fcs_path=%r "
        "current_export_columns=%r",
        uploaded_fcs_path,
        current_export_columns,
    )

    first_uploaded_fcs_path = apply_calibration.io.resolve_first_uploaded_fcs_path(
        uploaded_fcs_path,
    )

    if not first_uploaded_fcs_path:
        logger.debug(
            "No uploaded FCS path available. Returning empty export dropdown."
        )

        return [], []

    column_names = apply_calibration.io.get_fcs_column_names(
        uploaded_fcs_path=first_uploaded_fcs_path,
    )

    options = [
        {
            "label": column_name,
            "value": column_name,
        }
        for column_name in column_names
    ]

    allowed_values = {
        option["value"]
        for option in options
    }

    if isinstance(
        current_export_columns,
        list,
    ):
        resolved_values = [
            str(value)
            for value in current_export_columns
            if str(value) in allowed_values
        ]

    else:
        resolved_values = []

    logger.debug(
        "Resolved export columns dropdown with option_count=%r values=%r",
        len(options),
        resolved_values,
    )

    return options, resolved_values


def build_apply_calibration_request(
    *,
    uploaded_fcs_path: Any,
    selected_calibration: Any,
    export_columns: Any,
    selected_calibration_summary: Any,
    target_mie_model: Any,
    target_medium_refractive_index: Any,
    target_particle_refractive_index: Any,
    target_solid_sphere_diameter_min_nm: Any,
    target_solid_sphere_diameter_max_nm: Any,
    target_solid_sphere_diameter_count: Any,
    target_core_refractive_index: Any,
    target_shell_refractive_index: Any,
    target_shell_thickness_nm: Any,
    target_core_shell_core_diameter_min_nm: Any,
    target_core_shell_core_diameter_max_nm: Any,
    target_core_shell_core_diameter_count: Any,
) -> apply_calibration.ApplyCalibrationRequest:
    """
    Build an apply calibration request from Dash callback values.
    """
    resolved_uploaded_fcs_paths = apply_calibration.io.resolve_uploaded_fcs_paths(
        uploaded_fcs_path,
    )

    if not resolved_uploaded_fcs_paths:
        raise ValueError("Upload at least one input FCS file first.")

    if not selected_calibration:
        raise ValueError("Select a calibration first.")

    resolved_export_columns = apply_calibration.io.normalize_export_columns(
        export_columns,
    )

    scattering_target_model_parameters = build_scattering_target_model_parameters_if_required(
        selected_calibration_summary=selected_calibration_summary,
        target_mie_model=target_mie_model,
        target_medium_refractive_index=target_medium_refractive_index,
        target_particle_refractive_index=target_particle_refractive_index,
        target_solid_sphere_diameter_min_nm=target_solid_sphere_diameter_min_nm,
        target_solid_sphere_diameter_max_nm=target_solid_sphere_diameter_max_nm,
        target_solid_sphere_diameter_count=target_solid_sphere_diameter_count,
        target_core_refractive_index=target_core_refractive_index,
        target_shell_refractive_index=target_shell_refractive_index,
        target_shell_thickness_nm=target_shell_thickness_nm,
        target_core_shell_core_diameter_min_nm=target_core_shell_core_diameter_min_nm,
        target_core_shell_core_diameter_max_nm=target_core_shell_core_diameter_max_nm,
        target_core_shell_core_diameter_count=target_core_shell_core_diameter_count,
    )

    request = apply_calibration.ApplyCalibrationRequest(
        uploaded_fcs_paths=resolved_uploaded_fcs_paths,
        selected_calibration=str(
            selected_calibration,
        ),
        export_columns=resolved_export_columns,
        scattering_target_model_parameters=scattering_target_model_parameters,
    )

    logger.debug(
        "build_apply_calibration_request returning request=%r",
        request,
    )

    return request