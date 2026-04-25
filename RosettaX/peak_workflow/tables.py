# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np


def collect_existing_float_values_from_rows(
    *,
    rows: list[dict[str, Any]],
    column_name: str,
) -> list[float]:
    """
    Collect existing numeric values from a table column.

    Parameters
    ----------
    rows:
        Table rows.

    column_name:
        Column to inspect.

    Returns
    -------
    list[float]
        Existing numeric values.
    """
    existing_values: list[float] = []

    for row in rows:
        raw_value = row.get(
            column_name,
        )

        if raw_value in ("", None):
            continue

        try:
            existing_values.append(
                float(raw_value),
            )

        except Exception:
            continue

    return existing_values


def position_already_exists(
    *,
    position_value: float,
    existing_positions: list[float],
    relative_tolerance: float = 1e-9,
    absolute_tolerance: float = 1e-9,
) -> bool:
    """
    Return whether a position is already present.

    Parameters
    ----------
    position_value:
        Candidate value.

    existing_positions:
        Existing values.

    relative_tolerance:
        Relative tolerance.

    absolute_tolerance:
        Absolute tolerance.

    Returns
    -------
    bool
        True if the position already exists.
    """
    for existing_position in existing_positions:
        if np.isclose(
            position_value,
            existing_position,
            rtol=relative_tolerance,
            atol=absolute_tolerance,
        ):
            return True

    return False


def append_positions_to_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[Any],
    column_name: str,
    empty_row_factory: Any,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Append peak positions to the first empty cells of a table column.

    Parameters
    ----------
    table_data:
        Existing table rows.

    peak_positions:
        New peak positions.

    column_name:
        Target column name.

    empty_row_factory:
        Callable returning an empty row.

    logger:
        Logger.

    Returns
    -------
    list[dict[str, Any]]
        Updated rows.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    existing_positions = collect_existing_float_values_from_rows(
        rows=rows,
        column_name=column_name,
    )

    formatted_positions: list[str] = []

    for peak_position in peak_positions:
        try:
            position_value = float(
                extract_x_position(
                    peak_position,
                )
            )

        except Exception:
            logger.debug(
                "Ignoring invalid peak position=%r for column_name=%r",
                peak_position,
                column_name,
            )
            continue

        if position_already_exists(
            position_value=position_value,
            existing_positions=existing_positions,
        ):
            continue

        existing_positions.append(
            position_value,
        )

        formatted_positions.append(
            f"{position_value:.6g}",
        )

    if not formatted_positions:
        return rows

    empty_row_indices: list[int] = []

    for row_index, row in enumerate(rows):
        if row.get(column_name) in ("", None):
            empty_row_indices.append(
                row_index,
            )

    for formatted_position in formatted_positions:
        if empty_row_indices:
            row_index = empty_row_indices.pop(0)
            rows[row_index][column_name] = formatted_position
            continue

        row = empty_row_factory()
        row[column_name] = formatted_position
        rows.append(row)

    return rows


def clear_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    column_name: str,
) -> list[dict[str, Any]]:
    """
    Clear one table column.

    Parameters
    ----------
    table_data:
        Existing table rows.

    column_name:
        Column to clear.

    Returns
    -------
    list[dict[str, Any]]
        Updated rows.
    """
    rows = [
        dict(row)
        for row in (table_data or [])
    ]

    for row in rows:
        row[column_name] = ""

    return rows


def extract_x_position(
    peak_position: Any,
) -> float:
    """
    Extract the x coordinate from either a scalar or a 2D point.

    Parameters
    ----------
    peak_position:
        Scalar value or mapping with x.

    Returns
    -------
    float
        X position.
    """
    if isinstance(peak_position, dict):
        return float(
            peak_position["x"],
        )

    return float(
        peak_position,
    )