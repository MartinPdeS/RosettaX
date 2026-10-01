"""Scattering calibration builder."""

import logging
from typing import Any

import numpy as np

from . import mie_relation
from .calibration_models import (
    OpticalParameters,
    ScatteringCalibration,
    ScatteringCalibrationBuildResult,
)
from .fitting import fit_linear_instrument_response
from .mie_relation import MieRelation
from .numerical_arrays import _as_flat_float_array, _validate_same_size
from .standard_rows import (
    build_reference_table_from_rows,
    parse_core_shell_rows_for_fit,
    parse_sphere_rows_for_fit,
    write_expected_coupling_into_table,
)

logger = logging.getLogger(__name__)


def build_calibration_standard_mie_relation(
    *,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    fallback_particle_diameters_nm: np.ndarray,
    fallback_expected_coupling_values: np.ndarray,
    mie_model: str,
    optical_parameters: OpticalParameters,
    fallback_core_diameters_nm: np.ndarray | None = None,
    fallback_shell_thicknesses_nm: np.ndarray | None = None,
) -> MieRelation:
    """
    Build the calibration standard Mie relation stored in the calibration payload.

    The relation itself is one dimensional and maps outer diameter to modeled
    coupling for core shell standards. The core shell geometry arrays are stored
    in the parameter payload for provenance.
    """
    logger.debug(
        "build_calibration_standard_mie_relation called with mie_model=%r",
        mie_model,
    )

    dense_particle_diameters_nm = _as_flat_float_array(
        name="dense_particle_diameters_nm",
        values=dense_particle_diameters_nm,
    )

    dense_expected_coupling_values = _as_flat_float_array(
        name="dense_expected_coupling_values",
        values=dense_expected_coupling_values,
    )

    fallback_particle_diameters_nm = _as_flat_float_array(
        name="fallback_particle_diameters_nm",
        values=fallback_particle_diameters_nm,
    )

    fallback_expected_coupling_values = _as_flat_float_array(
        name="fallback_expected_coupling_values",
        values=fallback_expected_coupling_values,
    )

    if dense_particle_diameters_nm.size >= 2 and dense_expected_coupling_values.size >= 2:
        logger.debug(
            "build_calibration_standard_mie_relation using dense relation arrays."
        )

        diameter_values = dense_particle_diameters_nm
        coupling_values = dense_expected_coupling_values

    else:
        logger.debug(
            "build_calibration_standard_mie_relation using fallback standard arrays because "
            "dense sizes are diameter=%r coupling=%r.",
            dense_particle_diameters_nm.size,
            dense_expected_coupling_values.size,
        )

        diameter_values = fallback_particle_diameters_nm
        coupling_values = fallback_expected_coupling_values

    _validate_same_size(
        first_values=diameter_values,
        second_values=coupling_values,
        first_name="mie_relation_diameter_values",
        second_name="mie_relation_coupling_values",
    )

    core_diameter_nm: list[float] | None = None
    shell_thickness_nm: list[float] | None = None

    if fallback_core_diameters_nm is not None:
        fallback_core_diameters_nm = _as_flat_float_array(
            name="fallback_core_diameters_nm",
            values=fallback_core_diameters_nm,
        )

        core_diameter_nm = [
            float(value)
            for value in fallback_core_diameters_nm
        ]

    if fallback_shell_thicknesses_nm is not None:
        fallback_shell_thicknesses_nm = _as_flat_float_array(
            name="fallback_shell_thicknesses_nm",
            values=fallback_shell_thicknesses_nm,
        )

        shell_thickness_nm = [
            float(value)
            for value in fallback_shell_thicknesses_nm
        ]

    parameter_payload = optical_parameters.to_parameter_payload(
        mie_model=mie_model,
        particle_diameter_nm=[
            float(value)
            for value in fallback_particle_diameters_nm
        ],
        core_diameter_nm=core_diameter_nm,
        shell_thickness_nm=shell_thickness_nm,
        outer_diameter_nm=[
            float(value)
            for value in fallback_particle_diameters_nm
        ],
    )

    logger.debug(
        "build_calibration_standard_mie_relation calling build_mie_relation_from_arrays "
        "with diameter_count=%r coupling_count=%r parameter_keys=%r",
        diameter_values.size,
        coupling_values.size,
        sorted(parameter_payload.keys()),
    )

    return mie_relation.build_mie_relation_from_arrays(
        diameter_nm=diameter_values,
        theoretical_coupling=coupling_values,
        mie_model=mie_model,
        parameters=parameter_payload,
        relation_role="calibration_standard",
    )


def build_scattering_calibration(
    *,
    measured_peak_values: np.ndarray,
    theoretical_coupling_values: np.ndarray,
    measured_channel: str,
    calibration_standard_mie_relation: MieRelation,
    reference_table: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibration:
    """
    Build a saved scattering calibration from standard data.
    """
    logger.debug(
        "build_scattering_calibration called with measured_channel=%r "
        "reference_table_count=%r metadata_keys=%r force_zero_intercept=%r",
        measured_channel,
        len(reference_table),
        sorted((metadata or {}).keys()),
        force_zero_intercept,
    )

    instrument_response = fit_linear_instrument_response(
        measured_peak_values=measured_peak_values,
        theoretical_coupling_values=theoretical_coupling_values,
        measured_channel=measured_channel,
        force_zero_intercept=force_zero_intercept,
    )

    calibration = ScatteringCalibration(
        instrument_response=instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=[
            dict(row)
            for row in reference_table
        ],
        metadata=dict(
            metadata or {},
        ),
    )

    logger.debug(
        "build_scattering_calibration returning calibration source_channel=%r",
        calibration.source_channel,
    )

    return calibration


def build_solid_sphere_scattering_calibration_from_standard_data(
    *,
    detector_column: str,
    current_table_rows: list[dict[str, Any]],
    measured_peak_positions: np.ndarray,
    particle_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_particle_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    optical_parameters: OpticalParameters,
    metadata: dict[str, Any] | None = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibrationBuildResult:
    """
    Build a solid sphere scattering calibration from already computed standard data.
    """
    logger.debug(
        "build_solid_sphere_scattering_calibration_from_standard_data called with "
        "detector_column=%r current_table_row_count=%r",
        detector_column,
        len(current_table_rows),
    )

    measured_peak_positions = _as_flat_float_array(
        name="solid_measured_peak_positions",
        values=measured_peak_positions,
    )

    particle_diameters_nm = _as_flat_float_array(
        name="solid_particle_diameters_nm",
        values=particle_diameters_nm,
    )

    expected_coupling_values = _as_flat_float_array(
        name="solid_expected_coupling_values",
        values=expected_coupling_values,
    )

    if measured_peak_positions.size < 2:
        logger.error(
            "Solid sphere calibration failed because measured_peak_positions.size=%r.",
            measured_peak_positions.size,
        )
        raise ValueError("At least two measured peak positions are required.")

    _validate_same_size(
        first_values=particle_diameters_nm,
        second_values=measured_peak_positions,
        first_name="particle_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=expected_coupling_values,
        second_values=measured_peak_positions,
        first_name="expected_coupling_values",
        second_name="measured_peak_positions",
    )

    parsed_rows = parse_sphere_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_rows.row_count < 2:
        logger.error(
            "Solid sphere calibration failed because parsed row count=%r.",
            parsed_rows.row_count,
        )
        raise ValueError("At least two valid solid sphere standard rows are required.")

    updated_table_rows = write_expected_coupling_into_table(
        rows=current_table_rows,
        row_indices=parsed_rows.row_indices,
        expected_coupling_values=expected_coupling_values,
    )

    calibration_standard_mie_relation = build_calibration_standard_mie_relation(
        dense_particle_diameters_nm=dense_particle_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        fallback_particle_diameters_nm=particle_diameters_nm,
        fallback_expected_coupling_values=expected_coupling_values,
        mie_model="Solid Sphere",
        optical_parameters=optical_parameters,
    )

    resolved_metadata = dict(
        metadata or {},
    )

    resolved_metadata["measured_channel"] = str(
        detector_column,
    )

    resolved_metadata.setdefault(
        "calibration_standard",
        "Solid Sphere",
    )

    resolved_metadata.setdefault(
        "calibration_standard_parameters",
        optical_parameters.to_parameter_payload(
            mie_model="Solid Sphere",
            particle_diameter_nm=[
                float(value)
                for value in particle_diameters_nm
            ],
        ),
    )

    resolved_metadata.setdefault(
        "application_note",
        (
            "This calibration stores the instrument response inferred from the "
            "calibration standard. When applying it to unknown particles, build "
            "a target Mie relation from the target particle model."
        ),
    )

    logger.debug(
        "Solid sphere calibration metadata_keys=%r",
        sorted(resolved_metadata.keys()),
    )

    calibration = build_scattering_calibration(
        measured_peak_values=measured_peak_positions,
        theoretical_coupling_values=expected_coupling_values,
        measured_channel=str(
            detector_column,
        ),
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=build_reference_table_from_rows(
            rows=updated_table_rows,
        ),
        metadata=resolved_metadata,
        force_zero_intercept=force_zero_intercept,
    )

    build_result = ScatteringCalibrationBuildResult(
        calibration=calibration,
        instrument_response=calibration.instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        updated_table_rows=updated_table_rows,
        measured_peak_positions=measured_peak_positions,
        standard_diameters_nm=particle_diameters_nm,
        standard_coupling_values=expected_coupling_values,
    )

    logger.debug(
        "build_solid_sphere_scattering_calibration_from_standard_data returning "
        "slope=%r intercept=%r r_squared=%r updated_table_row_count=%r",
        build_result.instrument_response.slope,
        build_result.instrument_response.intercept,
        build_result.instrument_response.r_squared,
        len(build_result.updated_table_rows),
    )

    return build_result


def build_core_shell_scattering_calibration_from_standard_data(
    *,
    detector_column: str,
    current_table_rows: list[dict[str, Any]],
    measured_peak_positions: np.ndarray,
    core_diameters_nm: np.ndarray,
    shell_thicknesses_nm: np.ndarray,
    outer_diameters_nm: np.ndarray,
    expected_coupling_values: np.ndarray,
    dense_outer_diameters_nm: np.ndarray,
    dense_expected_coupling_values: np.ndarray,
    optical_parameters: OpticalParameters,
    metadata: dict[str, Any] | None = None,
    force_zero_intercept: bool = True,
) -> ScatteringCalibrationBuildResult:
    """
    Build a core shell scattering calibration from already computed standard data.
    """
    logger.debug(
        "build_core_shell_scattering_calibration_from_standard_data called with "
        "detector_column=%r current_table_row_count=%r",
        detector_column,
        len(current_table_rows),
    )

    measured_peak_positions = _as_flat_float_array(
        name="core_shell_measured_peak_positions",
        values=measured_peak_positions,
    )

    core_diameters_nm = _as_flat_float_array(
        name="core_shell_core_diameters_nm",
        values=core_diameters_nm,
    )

    shell_thicknesses_nm = _as_flat_float_array(
        name="core_shell_shell_thicknesses_nm",
        values=shell_thicknesses_nm,
    )

    outer_diameters_nm = _as_flat_float_array(
        name="core_shell_outer_diameters_nm",
        values=outer_diameters_nm,
    )

    expected_coupling_values = _as_flat_float_array(
        name="core_shell_expected_coupling_values",
        values=expected_coupling_values,
    )

    dense_outer_diameters_nm = _as_flat_float_array(
        name="core_shell_dense_outer_diameters_nm",
        values=dense_outer_diameters_nm,
    )

    dense_expected_coupling_values = _as_flat_float_array(
        name="core_shell_dense_expected_coupling_values",
        values=dense_expected_coupling_values,
    )

    if measured_peak_positions.size < 2:
        logger.error(
            "Core shell calibration failed because measured_peak_positions.size=%r.",
            measured_peak_positions.size,
        )
        raise ValueError("At least two measured peak positions are required.")

    _validate_same_size(
        first_values=core_diameters_nm,
        second_values=measured_peak_positions,
        first_name="core_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=shell_thicknesses_nm,
        second_values=measured_peak_positions,
        first_name="shell_thicknesses_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=outer_diameters_nm,
        second_values=measured_peak_positions,
        first_name="outer_diameters_nm",
        second_name="measured_peak_positions",
    )

    _validate_same_size(
        first_values=expected_coupling_values,
        second_values=measured_peak_positions,
        first_name="expected_coupling_values",
        second_name="measured_peak_positions",
    )

    parsed_rows = parse_core_shell_rows_for_fit(
        rows=current_table_rows,
    )

    if parsed_rows.row_count < 2:
        logger.error(
            "Core shell calibration failed because parsed row count=%r.",
            parsed_rows.row_count,
        )
        raise ValueError("At least two valid core shell standard rows are required.")

    updated_table_rows = write_expected_coupling_into_table(
        rows=current_table_rows,
        row_indices=parsed_rows.row_indices,
        expected_coupling_values=expected_coupling_values,
    )

    calibration_standard_mie_relation = build_calibration_standard_mie_relation(
        dense_particle_diameters_nm=dense_outer_diameters_nm,
        dense_expected_coupling_values=dense_expected_coupling_values,
        fallback_particle_diameters_nm=outer_diameters_nm,
        fallback_expected_coupling_values=expected_coupling_values,
        mie_model="Core/Shell Sphere",
        optical_parameters=optical_parameters,
        fallback_core_diameters_nm=core_diameters_nm,
        fallback_shell_thicknesses_nm=shell_thicknesses_nm,
    )

    resolved_metadata = dict(
        metadata or {},
    )

    resolved_metadata["measured_channel"] = str(
        detector_column,
    )

    resolved_metadata.setdefault(
        "calibration_standard",
        "Core/Shell Sphere",
    )

    resolved_metadata.setdefault(
        "calibration_standard_parameters",
        optical_parameters.to_parameter_payload(
            mie_model="Core/Shell Sphere",
            particle_diameter_nm=[
                float(value)
                for value in outer_diameters_nm
            ],
            core_diameter_nm=[
                float(value)
                for value in core_diameters_nm
            ],
            shell_thickness_nm=[
                float(value)
                for value in shell_thicknesses_nm
            ],
            outer_diameter_nm=[
                float(value)
                for value in outer_diameters_nm
            ],
        ),
    )

    resolved_metadata.setdefault(
        "application_note",
        (
            "This calibration stores the instrument response inferred from the "
            "core shell calibration standard. The calibration standard Mie "
            "relation is stored against outer diameter. When applying it to "
            "unknown particles, build a target Mie relation from the target "
            "particle model."
        ),
    )

    logger.debug(
        "Core shell calibration metadata_keys=%r",
        sorted(resolved_metadata.keys()),
    )

    calibration = build_scattering_calibration(
        measured_peak_values=measured_peak_positions,
        theoretical_coupling_values=expected_coupling_values,
        measured_channel=str(
            detector_column,
        ),
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        reference_table=build_reference_table_from_rows(
            rows=updated_table_rows,
        ),
        metadata=resolved_metadata,
        force_zero_intercept=force_zero_intercept,
    )

    build_result = ScatteringCalibrationBuildResult(
        calibration=calibration,
        instrument_response=calibration.instrument_response,
        calibration_standard_mie_relation=calibration_standard_mie_relation,
        updated_table_rows=updated_table_rows,
        measured_peak_positions=measured_peak_positions,
        standard_diameters_nm=outer_diameters_nm,
        standard_coupling_values=expected_coupling_values,
    )

    logger.debug(
        "build_core_shell_scattering_calibration_from_standard_data returning "
        "slope=%r intercept=%r r_squared=%r updated_table_row_count=%r",
        build_result.instrument_response.slope,
        build_result.instrument_response.intercept,
        build_result.instrument_response.r_squared,
        len(build_result.updated_table_rows),
    )

    return build_result
