# -*- coding: utf-8 -*-

from typing import Any, Optional


def get_column_ids(
    *,
    columns: Optional[list[dict[str, Any]]],
) -> list[str]:
    """
    Extract column IDs from Dash DataTable column definitions.
    """
    if not isinstance(columns, list):
        return []

    column_ids: list[str] = []

    for column in columns:
        if not isinstance(column, dict):
            continue

        column_id = column.get("id")

        if column_id in ("", None):
            continue

        column_ids.append(str(column_id))

    return column_ids


def get_editable_column_ids(
    *,
    columns: Optional[list[dict[str, Any]]],
) -> list[str]:
    """
    Extract editable column IDs from Dash DataTable column definitions.
    """
    if not isinstance(columns, list):
        return []

    column_ids: list[str] = []

    for column in columns:
        if not isinstance(column, dict):
            continue

        if not bool(column.get("editable", False)):
            continue

        column_id = column.get("id")

        if column_id in ("", None):
            continue

        column_ids.append(str(column_id))

    return column_ids


def copy_table_rows(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Build a shallow JSON safe copy of table rows.
    """
    if not isinstance(rows, list):
        return []

    copied_rows: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        copied_rows.append(
            {
                str(key): value
                for key, value in row.items()
            }
        )

    return copied_rows


def normalize_table_rows(
    *,
    rows: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Normalize arbitrary table rows into dictionary rows with string keys.
    """
    return copy_table_rows(
        rows=rows,
    )


def value_is_not_empty(
    value: Any,
) -> bool:
    """
    Return whether a table cell value should count as populated.
    """
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def row_has_data(
    *,
    row: dict[str, Any],
    user_data_column_ids: list[str],
) -> bool:
    """
    Return whether a row contains user data in the selected columns.
    """
    for column_id in user_data_column_ids:
        if value_is_not_empty(
            row.get(
                column_id,
            )
        ):
            return True

    return False


def table_is_effectively_empty(
    *,
    rows: Optional[list[dict[str, Any]]],
    user_data_column_ids: list[str],
) -> bool:
    """
    Return whether a table contains no useful user data.
    """
    normalized_rows = normalize_table_rows(
        rows=rows,
    )

    if not normalized_rows:
        return True

    if not user_data_column_ids:
        return True

    for row in normalized_rows:
        if row_has_data(
            row=row,
            user_data_column_ids=user_data_column_ids,
        ):
            return False

    return True


def profile_load_was_requested(
    *,
    profile_load_event_data: Any,
) -> bool:
    """
    Return whether a sidebar profile load event was requested.
    """
    return (
        isinstance(profile_load_event_data, dict)
        and bool(profile_load_event_data.get("profile_name"))
    )


def should_rebuild_table_from_runtime_config(
    *,
    profile_load_was_requested: bool,
    current_rows: Optional[list[dict[str, Any]]],
    user_data_column_ids: list[str],
) -> bool:
    """
    Decide whether a runtime configuration update should overwrite table data.

    Profile loads always rebuild the table. Ordinary runtime config updates only
    rebuild the table when the current table has no user data.
    """
    if profile_load_was_requested:
        return True

    return table_is_effectively_empty(
        rows=current_rows,
        user_data_column_ids=user_data_column_ids,
    )


def build_empty_row_from_column_ids(
    *,
    column_ids: list[str],
) -> dict[str, str]:
    """
    Build one empty row from column IDs.
    """
    return {
        str(column_id): ""
        for column_id in column_ids
    }


def build_empty_rows_from_column_ids(
    *,
    column_ids: list[str],
    row_count: int,
) -> list[dict[str, str]]:
    """
    Build empty rows from column IDs.
    """
    resolved_row_count = max(
        0,
        int(row_count),
    )

    return [
        build_empty_row_from_column_ids(
            column_ids=column_ids,
        )
        for _ in range(resolved_row_count)
    ]


def append_empty_row(
    *,
    rows: Optional[list[dict[str, Any]]],
    empty_row: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Return table rows with one extra empty row appended.
    """
    next_rows = copy_table_rows(
        rows=rows,
    )

    next_rows.append(
        {
            str(key): value
            for key, value in empty_row.items()
        }
    )

    return next_rows


def append_empty_row_from_columns(
    *,
    rows: Optional[list[dict[str, Any]]],
    columns: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """
    Return table rows with one extra empty row based on table columns.
    """
    return append_empty_row(
        rows=rows,
        empty_row=build_empty_row_from_column_ids(
            column_ids=get_column_ids(
                columns=columns,
            )
        ),
    )


def clear_columns(
    *,
    rows: Optional[list[dict[str, Any]]],
    column_ids: list[str],
) -> list[dict[str, Any]]:
    """
    Clear selected columns in every row.
    """
    next_rows = copy_table_rows(
        rows=rows,
    )

    selected_column_ids = {
        str(column_id)
        for column_id in column_ids
    }

    for row in next_rows:
        for column_id in selected_column_ids:
            if column_id in row:
                row[column_id] = ""

    return next_rows


def clear_rows(
    *,
    rows: Optional[list[dict[str, Any]]],
    row_indices: Optional[list[int]],
    columns: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """
    Clear selected rows while preserving row count.

    If columns are provided, cleared rows are rebuilt with all known columns.
    Otherwise only the keys already present in the selected row are cleared.
    """
    next_rows = copy_table_rows(
        rows=rows,
    )

    if not isinstance(row_indices, list):
        return next_rows

    column_ids = get_column_ids(
        columns=columns,
    )

    for row_index in row_indices:
        try:
            resolved_row_index = int(row_index)
        except Exception:
            continue

        if resolved_row_index < 0:
            continue

        if resolved_row_index >= len(next_rows):
            continue

        if column_ids:
            next_rows[resolved_row_index] = build_empty_row_from_column_ids(
                column_ids=column_ids,
            )

        else:
            next_rows[resolved_row_index] = {
                str(key): ""
                for key in next_rows[resolved_row_index]
            }

    return next_rows


def delete_rows(
    *,
    rows: Optional[list[dict[str, Any]]],
    row_indices: Optional[list[int]],
) -> list[dict[str, Any]]:
    """
    Delete selected rows.
    """
    next_rows = copy_table_rows(
        rows=rows,
    )

    if not isinstance(row_indices, list):
        return next_rows

    selected_indices: set[int] = set()

    for row_index in row_indices:
        try:
            selected_indices.add(int(row_index))
        except Exception:
            continue

    return [
        row
        for index, row in enumerate(next_rows)
        if index not in selected_indices
    ]


def reset_rows_from_columns(
    *,
    columns: Optional[list[dict[str, Any]]],
    row_count: int = 3,
) -> list[dict[str, str]]:
    """
    Build a reset table using current column definitions.
    """
    return build_empty_rows_from_column_ids(
        column_ids=get_column_ids(
            columns=columns,
        ),
        row_count=row_count,
    )