"""Scattering standard rows."""

import logging
from typing import Any

import numpy as np

from .calibration_models import ParsedCoreShellStandardRows, ParsedSphereStandardRows
from .numerical_arrays import _log_array_summary

logger = logging.getLogger(__name__)


def parse_sphere_rows_for_fit(
    *,
    rows: list[dict[str, Any]] | None,
) -> ParsedSphereStandardRows:
    """
    Extract valid solid sphere calibration standard rows.
    """
    row_indices: list[int] = []
    particle_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    total_row_count = 0
    skipped_row_count = 0

    for row_index, row in enumerate(rows or []):
        total_row_count += 1

        if not isinstance(row, dict):
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        try:
            raw_particle_diameter_nm = row.get(
                "particle_diameter_nm",
            )

            raw_measured_peak_position = row.get(
                "measured_peak_position",
            )

            if raw_particle_diameter_nm in ("", None):
                logger.debug(
                    "parse_sphere_rows_for_fit skipped row_index=%r because particle_diameter_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_measured_peak_position in ("", None):
                logger.debug(
                    "parse_sphere_rows_for_fit skipped row_index=%r because measured_peak_position is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            particle_diameter_nm = float(
                raw_particle_diameter_nm,
            )

            measured_peak_position = float(
                raw_measured_peak_position,
            )

        except Exception:
            logger.exception(
                "parse_sphere_rows_for_fit skipped row_index=%r because conversion failed. row=%r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        if particle_diameter_nm <= 0.0:
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because particle_diameter_nm=%r is not positive.",
                row_index,
                particle_diameter_nm,
            )
            skipped_row_count += 1
            continue

        if measured_peak_position <= 0.0:
            logger.debug(
                "parse_sphere_rows_for_fit skipped row_index=%r because measured_peak_position=%r is not positive.",
                row_index,
                measured_peak_position,
            )
            skipped_row_count += 1
            continue

        row_indices.append(
            row_index,
        )

        particle_diameters_nm.append(
            particle_diameter_nm,
        )

        measured_peak_positions.append(
            measured_peak_position,
        )

    parsed_rows = ParsedSphereStandardRows(
        row_indices=row_indices,
        particle_diameters_nm=np.asarray(
            particle_diameters_nm,
            dtype=float,
        ),
        measured_peak_positions=np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    )

    logger.debug(
        "parse_sphere_rows_for_fit parsed total_row_count=%r valid_row_count=%r "
        "skipped_row_count=%r row_indices=%r",
        total_row_count,
        parsed_rows.row_count,
        skipped_row_count,
        parsed_rows.row_indices,
    )

    _log_array_summary(
        name="parsed_sphere_particle_diameters_nm",
        values=parsed_rows.particle_diameters_nm,
    )

    _log_array_summary(
        name="parsed_sphere_measured_peak_positions",
        values=parsed_rows.measured_peak_positions,
    )

    return parsed_rows


def parse_core_shell_rows_for_fit(
    *,
    rows: list[dict[str, Any]] | None,
) -> ParsedCoreShellStandardRows:
    """
    Extract valid core shell calibration standard rows.
    """
    row_indices: list[int] = []
    core_diameters_nm: list[float] = []
    shell_thicknesses_nm: list[float] = []
    outer_diameters_nm: list[float] = []
    measured_peak_positions: list[float] = []

    total_row_count = 0
    skipped_row_count = 0

    for row_index, row in enumerate(rows or []):
        total_row_count += 1

        if not isinstance(row, dict):
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        try:
            raw_core_diameter_nm = row.get(
                "core_diameter_nm",
            )

            raw_shell_thickness_nm = row.get(
                "shell_thickness_nm",
            )

            raw_measured_peak_position = row.get(
                "measured_peak_position",
            )

            if raw_core_diameter_nm in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because core_diameter_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_shell_thickness_nm in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because shell_thickness_nm is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            if raw_measured_peak_position in ("", None):
                logger.debug(
                    "parse_core_shell_rows_for_fit skipped row_index=%r because measured_peak_position is missing.",
                    row_index,
                )
                skipped_row_count += 1
                continue

            core_diameter_nm = float(
                raw_core_diameter_nm,
            )

            shell_thickness_nm = float(
                raw_shell_thickness_nm,
            )

            measured_peak_position = float(
                raw_measured_peak_position,
            )

        except Exception:
            logger.exception(
                "parse_core_shell_rows_for_fit skipped row_index=%r because conversion failed. row=%r",
                row_index,
                row,
            )
            skipped_row_count += 1
            continue

        if core_diameter_nm <= 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because core_diameter_nm=%r is not positive.",
                row_index,
                core_diameter_nm,
            )
            skipped_row_count += 1
            continue

        if shell_thickness_nm < 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because shell_thickness_nm=%r is negative.",
                row_index,
                shell_thickness_nm,
            )
            skipped_row_count += 1
            continue

        if measured_peak_position <= 0.0:
            logger.debug(
                "parse_core_shell_rows_for_fit skipped row_index=%r because measured_peak_position=%r is not positive.",
                row_index,
                measured_peak_position,
            )
            skipped_row_count += 1
            continue

        outer_diameter_nm = core_diameter_nm + 2.0 * shell_thickness_nm

        row_indices.append(
            row_index,
        )

        core_diameters_nm.append(
            core_diameter_nm,
        )

        shell_thicknesses_nm.append(
            shell_thickness_nm,
        )

        outer_diameters_nm.append(
            outer_diameter_nm,
        )

        measured_peak_positions.append(
            measured_peak_position,
        )

    parsed_rows = ParsedCoreShellStandardRows(
        row_indices=row_indices,
        core_diameters_nm=np.asarray(
            core_diameters_nm,
            dtype=float,
        ),
        shell_thicknesses_nm=np.asarray(
            shell_thicknesses_nm,
            dtype=float,
        ),
        outer_diameters_nm=np.asarray(
            outer_diameters_nm,
            dtype=float,
        ),
        measured_peak_positions=np.asarray(
            measured_peak_positions,
            dtype=float,
        ),
    )

    logger.debug(
        "parse_core_shell_rows_for_fit parsed total_row_count=%r valid_row_count=%r "
        "skipped_row_count=%r row_indices=%r",
        total_row_count,
        parsed_rows.row_count,
        skipped_row_count,
        parsed_rows.row_indices,
    )

    _log_array_summary(
        name="parsed_core_shell_core_diameters_nm",
        values=parsed_rows.core_diameters_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_shell_thicknesses_nm",
        values=parsed_rows.shell_thicknesses_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_outer_diameters_nm",
        values=parsed_rows.outer_diameters_nm,
    )

    _log_array_summary(
        name="parsed_core_shell_measured_peak_positions",
        values=parsed_rows.measured_peak_positions,
    )

    return parsed_rows


def write_expected_coupling_into_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write modeled coupling values into the calibration standard table rows.
    """
    logger.debug(
        "write_expected_coupling_into_table called with row_count=%r row_indices=%r",
        len(rows),
        row_indices,
    )

    _log_array_summary(
        name="write_expected_coupling_values",
        values=expected_coupling_values,
    )

    updated_rows = [
        dict(row)
        for row in rows
    ]

    expected_coupling_values = np.asarray(
        expected_coupling_values,
        dtype=float,
    ).reshape(-1)

    for row in updated_rows:
        row["expected_coupling"] = ""

    for row_index, expected_coupling_value in zip(
        row_indices,
        expected_coupling_values,
        strict=False,
    ):
        if row_index >= len(updated_rows):
            logger.debug(
                "write_expected_coupling_into_table skipped row_index=%r because updated_rows length is %r.",
                row_index,
                len(updated_rows),
            )
            continue

        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling_value):.6g}"

    serialized_rows = [
        {
            str(key): "" if value is None else str(value)
            for key, value in row.items()
        }
        for row in updated_rows
    ]

    logger.debug(
        "write_expected_coupling_into_table returning row_count=%r",
        len(serialized_rows),
    )

    return serialized_rows


def write_expected_coupling_into_sphere_table(
    *,
    rows: list[dict[str, Any]],
    row_indices: list[int],
    expected_coupling_values: np.ndarray,
) -> list[dict[str, str]]:
    """
    Write modeled coupling values into the solid sphere calibration table rows.

    This wrapper is kept for existing imports and call sites.
    """
    logger.debug("write_expected_coupling_into_sphere_table called.")

    return write_expected_coupling_into_table(
        rows=rows,
        row_indices=row_indices,
        expected_coupling_values=expected_coupling_values,
    )


def build_reference_table_from_rows(
    *,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build a JSON serializable copy of the calibration standard table.
    """
    logger.debug(
        "build_reference_table_from_rows called with row_count=%r",
        len(rows),
    )

    reference_table: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            logger.debug(
                "build_reference_table_from_rows skipped row_index=%r because row is not a dictionary: %r",
                row_index,
                row,
            )
            continue

        reference_table.append(
            {
                str(key): value
                for key, value in row.items()
            }
        )

    logger.debug(
        "build_reference_table_from_rows returning row_count=%r",
        len(reference_table),
    )

    return reference_table
