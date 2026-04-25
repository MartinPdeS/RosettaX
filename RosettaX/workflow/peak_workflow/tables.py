# -*- coding: utf-8 -*-

from typing import Any, Callable, Optional
import logging

import numpy as np


def append_positions_to_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: list[Any],
    column_name: str,
    empty_row_factory: Callable[[], dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Append peak positions to a Dash DataTable column.

    Dash DataTable cells must contain JSON safe scalar values. This function
    therefore converts NumPy scalars, zero dimensional arrays, and single item
    arrays into Python scalar values before writing them into rows.
    """
    rows = [
        normalize_table_row(
            row=row,
        )
        for row in (table_data or [])
    ]

    normalized_peak_positions = normalize_peak_positions(
        peak_positions=peak_positions,
        logger=logger,
    )

    for peak_position in normalized_peak_positions:
        target_row_index = find_first_empty_row_index(
            rows=rows,
            column_name=column_name,
        )

        if target_row_index is None:
            rows.append(
                normalize_table_row(
                    row=empty_row_factory(),
                )
            )
            target_row_index = len(rows) - 1

        rows[target_row_index][column_name] = peak_position

    return rows


def clear_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    column_name: str,
) -> list[dict[str, Any]]:
    """
    Clear one DataTable column while preserving all rows.
    """
    rows = [
        normalize_table_row(
            row=row,
        )
        for row in (table_data or [])
    ]

    for row in rows:
        row[column_name] = ""

    return rows


def find_first_empty_row_index(
    *,
    rows: list[dict[str, Any]],
    column_name: str,
) -> Optional[int]:
    """
    Return the first row index whose target column is empty.
    """
    for row_index, row in enumerate(rows):
        value = row.get(
            column_name,
            "",
        )

        if value is None:
            return row_index

        if isinstance(value, str) and not value.strip():
            return row_index

    return None


def normalize_table_row(
    *,
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert all row values to Dash DataTable safe values.
    """
    return {
        str(key): normalize_datatable_value(
            value=value,
        )
        for key, value in dict(row).items()
    }


def normalize_peak_positions(
    *,
    peak_positions: list[Any],
    logger: logging.Logger,
) -> list[Any]:
    """
    Convert a peak position collection into JSON safe scalar values.
    """
    normalized_peak_positions: list[Any] = []

    for peak_position in flatten_peak_positions(
        value=peak_positions,
    ):
        normalized_value = normalize_datatable_value(
            value=peak_position,
        )

        if normalized_value is None:
            logger.debug(
                "Ignored peak position because it could not be converted to a DataTable scalar: %r",
                peak_position,
            )
            continue

        normalized_peak_positions.append(
            normalized_value,
        )

    return normalized_peak_positions


def flatten_peak_positions(
    *,
    value: Any,
) -> list[Any]:
    """
    Flatten common peak position containers.

    This intentionally flattens NumPy arrays and nested lists because a single
    DataTable cell must not receive a list or array.
    """
    if value is None:
        return []

    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return [
                value.item(),
            ]

        return [
            item
            for item in value.reshape(-1).tolist()
        ]

    if isinstance(value, (list, tuple)):
        flattened_values: list[Any] = []

        for item in value:
            flattened_values.extend(
                flatten_peak_positions(
                    value=item,
                )
            )

        return flattened_values

    return [
        value,
    ]


def normalize_datatable_value(
    *,
    value: Any,
) -> Any:
    """
    Convert one value to a Dash DataTable compatible scalar.

    Accepted return types are string, int, float, bool, or None.
    """
    if value is None:
        return ""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        if isinstance(value, float) and not np.isfinite(value):
            return ""

        return value

    if isinstance(value, np.generic):
        return normalize_datatable_value(
            value=value.item(),
        )

    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return normalize_datatable_value(
                value=value.item(),
            )

        if value.size == 1:
            return normalize_datatable_value(
                value=value.reshape(-1)[0],
            )

        return ""

    if hasattr(value, "item"):
        try:
            return normalize_datatable_value(
                value=value.item(),
            )

        except Exception:
            return str(value)

    return str(value)