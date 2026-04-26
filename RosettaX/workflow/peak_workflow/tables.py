# -*- coding: utf-8 -*-

from typing import Any, Callable, Optional
import logging

import numpy as np


def append_positions_to_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    peak_positions: Any,
    column_name: str,
    empty_row_factory: Callable[[], dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Append numeric peak positions to the next empty cells of a Dash DataTable
    column.

    Existing rows are preserved. New rows are created only when there are more
    peak positions than empty cells.
    """
    rows = normalize_table_rows(
        table_data=table_data,
    )

    numeric_peak_positions = coerce_peak_positions_to_float_list(
        peak_positions=peak_positions,
        logger=logger,
    )

    if not rows:
        rows.append(
            normalize_table_row(
                row=empty_row_factory(),
            )
        )

    for peak_position in numeric_peak_positions:
        row_index = find_first_empty_row_index(
            rows=rows,
            column_name=column_name,
        )

        if row_index is None:
            rows.append(
                normalize_table_row(
                    row=empty_row_factory(),
                )
            )
            row_index = len(rows) - 1

        rows[row_index][column_name] = float(peak_position)

    return rows


def clear_table_column(
    *,
    table_data: Optional[list[dict[str, Any]]],
    column_name: str,
    empty_row_factory: Callable[[], dict[str, Any]] | None = None,
    minimum_row_count: int = 0,
) -> list[dict[str, Any]]:
    """
    Clear one DataTable column while preserving rows.

    Optionally creates empty rows if the table is empty or shorter than
    minimum_row_count.
    """
    rows = normalize_table_rows(
        table_data=table_data,
    )

    if empty_row_factory is not None:
        while len(rows) < int(minimum_row_count):
            rows.append(
                normalize_table_row(
                    row=empty_row_factory(),
                )
            )

    for row in rows:
        row[column_name] = ""

    return rows


def normalize_table_rows(
    *,
    table_data: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Normalize Dash DataTable rows into mutable dictionaries.
    """
    return [
        normalize_table_row(
            row=row,
        )
        for row in (table_data or [])
        if isinstance(row, dict)
    ]


def normalize_table_row(
    *,
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one row into a string keyed dictionary.
    """
    return {
        str(key): normalize_datatable_scalar(
            value=value,
        )
        for key, value in dict(row).items()
    }


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


def coerce_peak_positions_to_float_list(
    *,
    peak_positions: Any,
    logger: logging.Logger,
) -> list[float]:
    """
    Convert peak positions into a flat list of finite floats.

    Accepted inputs include:
    - scalar number
    - NumPy scalar
    - NumPy array
    - list or tuple of numeric values
    - dictionaries with x, position, value, or peak_position
    """
    raw_values = flatten_peak_positions(
        value=peak_positions,
    )

    float_values: list[float] = []

    for raw_value in raw_values:
        float_value = coerce_float(
            value=raw_value,
        )

        if float_value is None:
            logger.debug(
                "Ignored non numeric peak position: %r",
                raw_value,
            )
            continue

        float_values.append(
            float_value,
        )

    return float_values


def flatten_peak_positions(
    *,
    value: Any,
) -> list[Any]:
    """
    Flatten peak position containers into scalar like values.
    """
    if value is None:
        return []

    if isinstance(value, dict):
        for key in (
            "x",
            "clicked_x",
            "clicked_x_position",
            "x_position",
            "position",
            "value",
            "peak_position",
        ):
            if key in value:
                return flatten_peak_positions(
                    value=value[key],
                )

        return []

    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return [
                value.item(),
            ]

        return value.reshape(-1).tolist()

    if isinstance(value, np.generic):
        return [
            value.item(),
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


def coerce_float(
    *,
    value: Any,
) -> float | None:
    """
    Convert one value to a finite float.
    """
    if value is None:
        return None

    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return coerce_float(
                value=value.item(),
            )

        if value.size == 1:
            return coerce_float(
                value=value.reshape(-1)[0],
            )

        return None

    if isinstance(value, np.generic):
        return coerce_float(
            value=value.item(),
        )

    try:
        float_value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(float_value):
        return None

    return float_value


def normalize_datatable_scalar(
    *,
    value: Any,
) -> Any:
    """
    Convert one existing table value to a Dash DataTable compatible scalar.
    """
    if value is None:
        return ""

    if isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not np.isfinite(value):
            return ""

        return value

    if isinstance(value, np.generic):
        return normalize_datatable_scalar(
            value=value.item(),
        )

    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return normalize_datatable_scalar(
                value=value.item(),
            )

        if value.size == 1:
            return normalize_datatable_scalar(
                value=value.reshape(-1)[0],
            )

        return ""

    return str(value)