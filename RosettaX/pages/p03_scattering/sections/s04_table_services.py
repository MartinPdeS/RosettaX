# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

from RosettaX.pages.p03_scattering.sections.s03_parameters import services as parameter_services
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow import table as workflow_table
from RosettaX.workflow.calibration.mie_relation import build_mie_parameter_payload


logger = logging.getLogger(__name__)


sphere_table_columns = parameter_services.sphere_table_columns
core_shell_table_columns = parameter_services.core_shell_table_columns


def resolve_mie_model(
    mie_model: Any,
) -> str:
    """
    Resolve the Mie model name used by the scattering standard table.
    """
    return parameter_services.resolve_mie_model(
        mie_model,
    )


def get_table_columns_for_model(
    mie_model: Any,
) -> list[dict[str, Any]]:
    """
    Return table columns for the selected Mie model.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return parameter_services.get_table_columns_for_model(
        resolved_mie_model,
    )


def get_user_data_column_ids_for_model(
    mie_model: Any,
) -> list[str]:
    """
    Return table columns that should count as user data for a Mie model.
    """
    columns = get_table_columns_for_model(
        mie_model,
    )

    return workflow_table.get_column_ids(
        columns=columns,
    )


def normalize_table_rows(
    *,
    mie_model: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Normalize scattering standard table rows for the selected Mie model.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return parameter_services.normalize_table_rows(
        mie_model=resolved_mie_model,
        current_rows=current_rows,
    )


def table_is_effectively_empty(
    *,
    mie_model: Any,
    rows: Optional[list[dict[str, Any]]],
) -> bool:
    """
    Return whether the scattering standard table contains no useful user data.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    normalized_rows = normalize_table_rows(
        mie_model=resolved_mie_model,
        current_rows=rows,
    )

    user_data_column_ids = get_user_data_column_ids_for_model(
        resolved_mie_model,
    )

    return workflow_table.table_is_effectively_empty(
        rows=normalized_rows,
        user_data_column_ids=user_data_column_ids,
    )


def should_rebuild_table_from_runtime_config(
    *,
    mie_model: Any,
    profile_load_event_data: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> bool:
    """
    Decide whether a runtime configuration update should overwrite the table.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    profile_load_was_requested = workflow_table.profile_load_was_requested(
        profile_load_event_data=profile_load_event_data,
    )

    normalized_current_rows = normalize_table_rows(
        mie_model=resolved_mie_model,
        current_rows=current_rows,
    )

    user_data_column_ids = get_user_data_column_ids_for_model(
        resolved_mie_model,
    )

    return workflow_table.should_rebuild_table_from_runtime_config(
        profile_load_was_requested=profile_load_was_requested,
        current_rows=normalized_current_rows,
        user_data_column_ids=user_data_column_ids,
    )


def build_table_state_from_runtime_config(
    *,
    runtime_config: RuntimeConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Build scattering standard table columns and rows from runtime configuration.
    """
    resolved_mie_model = resolve_mie_model(
        runtime_config.get_str(
            "particle_model.mie_model",
            default="Solid Sphere",
        )
    )

    columns = get_table_columns_for_model(
        resolved_mie_model,
    )

    rows = parameter_services.populate_table_from_runtime_defaults(
        mie_model=resolved_mie_model,
        runtime_particle_diameters_nm=runtime_config.get_path(
            "particle_model.particle_diameter_nm",
            default=[],
        ),
        runtime_core_diameters_nm=runtime_config.get_path(
            "particle_model.core_diameter_nm",
            default=[],
        ),
        runtime_shell_thicknesses_nm=runtime_config.get_path(
            "particle_model.shell_thickness_nm",
            default=[],
        ),
    )

    if not rows:
        rows = build_empty_rows_for_model(
            resolved_mie_model,
            row_count=3,
        )

    logger.debug(
        "Built scattering standard table state from runtime config. "
        "resolved_mie_model=%r columns=%r rows=%r",
        resolved_mie_model,
        columns,
        rows,
    )

    return columns, rows


def remap_table_rows_to_model(
    *,
    mie_model: Any,
    current_rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """
    Remap current table rows to the selected Mie model schema.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return parameter_services.remap_table_rows_to_model(
        mie_model=resolved_mie_model,
        current_rows=current_rows,
    )


def build_empty_row_for_model(
    mie_model: Any,
) -> dict[str, str]:
    """
    Build one empty scattering standard table row.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return parameter_services.build_empty_row_for_model(
        resolved_mie_model,
    )


def build_empty_rows_for_model(
    mie_model: Any,
    *,
    row_count: int,
) -> list[dict[str, str]]:
    """
    Build empty scattering standard table rows.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return parameter_services.build_empty_rows_for_model(
        resolved_mie_model,
        row_count=row_count,
    )


def add_empty_row_for_model(
    *,
    mie_model: Any,
    rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Add one empty row to the scattering standard table.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    next_rows = workflow_table.copy_table_rows(
        rows=rows,
    )

    next_rows.append(
        build_empty_row_for_model(
            resolved_mie_model,
        )
    )

    return next_rows


def compute_model_for_rows(
    *,
    mie_model: Any,
    current_rows: Optional[list[dict[str, Any]]],
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
    logger: logging.Logger,
) -> list[dict[str, str]]:
    """
    Compute modeled coupling values for the scattering calibration standard rows.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    if not current_rows:
        return build_empty_rows_for_model(
            resolved_mie_model,
            row_count=3,
        )

    return parameter_services.compute_model_for_rows(
        mie_model=resolved_mie_model,
        current_rows=current_rows,
        medium_refractive_index=medium_refractive_index,
        particle_refractive_index=particle_refractive_index,
        core_refractive_index=core_refractive_index,
        shell_refractive_index=shell_refractive_index,
        wavelength_nm=wavelength_nm,
        detector_numerical_aperture=detector_numerical_aperture,
        detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
        detector_sampling=detector_sampling,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
        logger=logger,
    )


def build_scattering_parameters_payload(
    *,
    mie_model: Any,
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
) -> dict[str, Any]:
    """
    Build the serializable scattering standard parameter payload.

    This payload describes the calibration standard model used to compute the
    theoretical coupling values in the table.
    """
    resolved_mie_model = resolve_mie_model(
        mie_model,
    )

    return build_mie_parameter_payload(
        mie_model=resolved_mie_model,
        medium_refractive_index=medium_refractive_index,
        particle_refractive_index=particle_refractive_index,
        core_refractive_index=core_refractive_index,
        shell_refractive_index=shell_refractive_index,
        wavelength_nm=wavelength_nm,
        detector_numerical_aperture=detector_numerical_aperture,
        detector_cache_numerical_aperture=detector_cache_numerical_aperture,
        blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
        detector_sampling=detector_sampling,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
    )