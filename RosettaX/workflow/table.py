# -*- coding: utf-8 -*-

from typing import Any, Iterable, Optional


def normalize_table_rows(
    *,
    rows: Any,
) -> list[dict[str, Any]]:
    """
    Normalize arbitrary Dash DataTable row payloads into dictionary rows.

    Invalid rows are ignored. Keys are converted to strings so downstream table
    logic can safely compare column identifiers.
    """
    if not isinstance(rows, list):
        return []

    normalized_rows: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        normalized_rows.append(
            {
                str(key): value
                for key, value in row.items()
            }
        )

    return normalized_rows


def copy_table_rows(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Return a shallow copy of table rows.

    This prevents callbacks from mutating Dash state payloads in place.
    """
    return [
        dict(row)
        for row in (rows or [])
        if isinstance(row, dict)
    ]


def value_is_not_empty(
    value: Any,
) -> bool:
    """
    Return whether a table cell value should be considered populated.
    """
    if value is None:
        return False

    if isinstance(value, str):
        return bool(
            value.strip()
        )

    return True


def row_has_user_data(
    *,
    row: dict[str, Any],
    column_ids: Iterable[str],
) -> bool:
    """
    Return whether a row contains useful user data in any selected column.
    """
    for column_id in column_ids:
        if value_is_not_empty(
            row.get(
                column_id,
                "",
            )
        ):
            return True

    return False


def table_is_effectively_empty(
    *,
    rows: list[dict[str, Any]],
    user_data_column_ids: Iterable[str],
) -> bool:
    """
    Return whether a table contains no useful user data.

    Only the supplied columns are considered. This allows each workflow to
    define which columns indicate user input.
    """
    normalized_rows = normalize_table_rows(
        rows=rows,
    )

    if not normalized_rows:
        return True

    for row in normalized_rows:
        if row_has_user_data(
            row=row,
            column_ids=user_data_column_ids,
        ):
            return False

    return True


def profile_load_was_requested(
    *,
    profile_load_event_data: Any,
) -> bool:
    """
    Return whether a sidebar profile load event was emitted.
    """
    return (
        isinstance(profile_load_event_data, dict)
        and bool(
            profile_load_event_data.get(
                "profile_name",
            )
        )
    )


def should_rebuild_table_from_runtime_config(
    *,
    profile_load_was_requested: bool,
    current_rows: Any,
    user_data_column_ids: Iterable[str],
) -> bool:
    """
    Decide whether a runtime configuration update should overwrite table rows.

    A profile load is an explicit user request, so it always rebuilds the table.
    Ordinary runtime store updates only rebuild the table if it is effectively
    empty. This preserves user edits during normal application updates.
    """
    if profile_load_was_requested:
        return True

    normalized_current_rows = normalize_table_rows(
        rows=current_rows,
    )

    return table_is_effectively_empty(
        rows=normalized_current_rows,
        user_data_column_ids=user_data_column_ids,
    )


def build_empty_rows(
    *,
    column_ids: Iterable[str],
    row_count: int,
) -> list[dict[str, str]]:
    """
    Build generic empty table rows for the given column identifiers.
    """
    resolved_column_ids = [
        str(column_id)
        for column_id in column_ids
    ]

    return [
        {
            column_id: ""
            for column_id in resolved_column_ids
        }
        for _ in range(row_count)
    ]


def get_column_ids(
    *,
    columns: Any,
) -> list[str]:
    """
    Extract column identifiers from Dash DataTable column definitions.
    """
    if not isinstance(columns, list):
        return []

    column_ids: list[str] = []

    for column in columns:
        if not isinstance(column, dict):
            continue

        column_id = column.get(
            "id",
        )

        if column_id is None:
            continue

        column_ids.append(
            str(
                column_id,
            )
        )

    return column_ids


def add_empty_row_from_columns(
    *,
    rows: Any,
    columns: Any,
) -> list[dict[str, Any]]:
    """
    Add one empty row using Dash DataTable column definitions.
    """
    next_rows = copy_table_rows(
        rows=rows,
    )

    next_rows.append(
        {
            column_id: ""
            for column_id in get_column_ids(
                columns=columns,
            )
        }
    )

    return next_rows