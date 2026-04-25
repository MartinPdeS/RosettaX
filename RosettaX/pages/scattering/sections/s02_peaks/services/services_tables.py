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
    Append measured peak positions into the calibration reference table.

    This function expects peak_positions to represent the delta produced by the
    current peak process action, not the full cumulative graph payload.

    For 1D peaks, each value is written directly.

    For 2D peaks, only the x coordinate is written because the calibration
    reference table expects one measured peak position.
    """
    if not peak_positions:
        return [
            dict(row)
            for row in (table_data or [])
        ]

    measured_peak_positions = extract_measured_peak_positions(
        peak_positions=peak_positions,
        logger=logger,
    )

    return append_measured_peak_positions_into_table(
        table_data=table_data,
        measured_peak_positions=measured_peak_positions,
        mie_model=mie_model,
        logger=logger,
    )


def extract_measured_peak_positions(
    *,
    peak_positions: list[Any],
    logger: logging.Logger,
) -> list[float]:
    """
    Extract scalar measured peak positions from 1D or 2D peak position payloads.

    Parameters
    ----------
    peak_positions:
        Peak position delta returned by a peak process.

    logger:
        Logger instance.

    Returns
    -------
    list[float]
        Scalar measured peak positions.
    """
    measured_peak_positions: list[float] = []

    for peak_position in peak_positions:
        try:
            if isinstance(peak_position, dict):
                measured_peak_positions.append(
                    float(peak_position["x"]),
                )

            else:
                measured_peak_positions.append(
                    float(peak_position),
                )

        except Exception:
            logger.debug(
                "Ignoring invalid measured peak position=%r",
                peak_position,
            )

    return measured_peak_positions


def append_measured_peak_positions_into_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    measured_peak_positions: list[float],
    mie_model: str,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Append measured peak positions into the calibration reference table.

    Existing measured peak positions are preserved. New positions fill the first
    empty measured_peak_position rows, then new rows are appended if needed.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for measured_peak_position in measured_peak_positions:
        formatted_peak_position = f"{float(measured_peak_position):.6g}"

        row_index = find_first_empty_measured_peak_position_row_index(
            rows=rows,
        )

        if row_index is None:
            new_row = build_empty_table_row(
                mie_model=mie_model,
            )

            new_row["measured_peak_position"] = formatted_peak_position
            rows.append(new_row)

        else:
            rows[row_index]["measured_peak_position"] = formatted_peak_position

    ensure_minimum_table_row_count(
        rows=rows,
        mie_model=mie_model,
        minimum_row_count=3,
    )

    logger.debug(
        "Appended measured peaks into table measured_peak_positions=%r row_count=%d",
        measured_peak_positions,
        len(rows),
    )

    return rows


def clear_measured_positions_from_table(
    *,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: str,
) -> list[dict[str, Any]]:
    """
    Clear measured peak positions from the calibration reference table.

    Geometry and expected coupling values are preserved.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    ensure_minimum_table_row_count(
        rows=rows,
        mie_model=mie_model,
        minimum_row_count=3,
    )

    for row in rows:
        row["measured_peak_position"] = ""

    return rows


def find_first_empty_measured_peak_position_row_index(
    *,
    rows: list[dict[str, Any]],
) -> Optional[int]:
    """
    Find the first row where measured_peak_position is empty.
    """
    for row_index, row in enumerate(rows):
        if row.get("measured_peak_position") in ("", None):
            return row_index

    return None


def ensure_minimum_table_row_count(
    *,
    rows: list[dict[str, Any]],
    mie_model: str,
    minimum_row_count: int,
) -> None:
    """
    Ensure the table has at least minimum_row_count rows.

    The list is modified in place.
    """
    while len(rows) < int(minimum_row_count):
        rows.append(
            build_empty_table_row(
                mie_model=mie_model,
            )
        )


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