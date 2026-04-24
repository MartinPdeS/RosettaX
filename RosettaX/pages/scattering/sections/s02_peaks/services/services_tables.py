# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging


def write_measured_positions_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[Any],
    mie_model: str,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Write 1D or 2D measured positions into the calibration reference table.
    """
    if peak_positions and isinstance(peak_positions[0], dict):
        return write_measured_2d_peaks_into_table(
            table_data=table_data,
            peak_positions=peak_positions,
            mie_model=mie_model,
            logger=logger,
        )

    return write_measured_1d_peaks_into_table(
        table_data=table_data,
        peak_positions=[
            float(value)
            for value in peak_positions
        ],
        mie_model=mie_model,
        logger=logger,
    )


def write_measured_1d_peaks_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[float],
    mie_model: str,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Write 1D measured peak positions into the calibration reference table.
    """
    rows = [dict(row) for row in (table_data or [])]

    required_row_count = max(
        3,
        len(rows),
        len(peak_positions),
    )

    while len(rows) < required_row_count:
        rows.append(
            build_empty_table_row(
                mie_model=mie_model,
            )
        )

    for row_index, row in enumerate(rows):
        if row_index < len(peak_positions):
            row["measured_peak_position"] = f"{float(peak_positions[row_index]):.6g}"
        else:
            row["measured_peak_position"] = ""

    logger.debug(
        "Wrote 1D measured peaks into table peak_positions=%r row_count=%d",
        peak_positions,
        len(rows),
    )

    return rows


def write_measured_2d_peaks_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[dict[str, float]],
    mie_model: str,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Write 2D measured peak positions into the calibration reference table.

    Only the x coordinate is written because the calibration reference table
    expects one measured peak position.
    """
    rows = [dict(row) for row in (table_data or [])]

    required_row_count = max(
        3,
        len(rows),
        len(peak_positions),
    )

    while len(rows) < required_row_count:
        rows.append(
            build_empty_table_row(
                mie_model=mie_model,
            )
        )

    for row_index, row in enumerate(rows):
        if row_index < len(peak_positions):
            position = peak_positions[row_index]
            row["measured_peak_position"] = f"{float(position['x']):.6g}"
        else:
            row["measured_peak_position"] = ""

    logger.debug(
        "Wrote 2D measured peaks into table using x coordinate only "
        "peak_positions=%r row_count=%d",
        peak_positions,
        len(rows),
    )

    return rows


def build_empty_table_row(
    *,
    mie_model: str,
) -> dict[str, str]:
    """
    Build an empty calibration table row for the selected Mie model.
    """
    if mie_model == "Core/Shell Sphere":
        return {
            "core_diameter_nm": "",
            "shell_thickness_nm": "",
            "outer_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
        }

    return {
        "particle_diameter_nm": "",
        "measured_peak_position": "",
        "expected_coupling": "",
    }