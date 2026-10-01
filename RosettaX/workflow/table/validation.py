"""Cell-level feedback for editable calibration reference values."""

from dataclasses import dataclass
from typing import Any

import dash

from RosettaX.utils import casting, styling
from RosettaX.workflow.table.services import value_is_not_empty


@dataclass(frozen=True)
class ReferenceCellIssue:
    row_index: int
    column_id: str
    column_label: str
    message: str


def validate_reference_table_cells(
    rows: list[dict[str, Any]] | None,
    columns: list[dict[str, Any]] | None,
) -> list[ReferenceCellIssue]:
    """Check populated editable values; empty cells can be filled later."""
    issues = []
    for row_index, row in enumerate(rows or []):
        for column in columns or []:
            if not column.get("editable", False):
                continue
            column_id = column["id"]
            value = row.get(column_id)
            if not value_is_not_empty(value):
                continue
            parsed = casting.as_float(value)
            if isinstance(value, bool) or parsed is None:
                message = "Enter a finite number."
            elif parsed <= 0:
                message = "Enter a value greater than zero."
            else:
                continue
            label = column.get("name", column_id)
            if isinstance(label, list):
                label = " / ".join(str(part) for part in label)
            issues.append(ReferenceCellIssue(row_index, column_id, str(label), message))
    return issues


def build_reference_table_feedback(rows, columns, active_cell=None):
    """Return cell highlights, tooltips, and visible explanations."""
    issues = validate_reference_table_cells(rows, columns)
    styles = list(styling.DATATABLE["style_data_conditional"])
    tooltips = [{} for _ in rows or []]
    for issue in issues:
        styles.append({
            "if": {"row_index": issue.row_index, "column_id": issue.column_id},
            "boxShadow": "inset 0 0 0 2px var(--bs-danger)",
        })
        tooltips[issue.row_index][issue.column_id] = {"value": issue.message, "type": "text"}

    if active_cell:
        issues.sort(key=lambda issue: (
            issue.row_index != active_cell.get("row")
            or issue.column_id != active_cell.get("column_id")
        ))
    messages = [
        dash.html.Div(f"Row {issue.row_index + 1} · {issue.column_label}: {issue.message}")
        for issue in issues[:5]
    ]
    if len(issues) > 5:
        messages.append(dash.html.Div(f"{len(issues) - 5} more invalid cells. Select a marked cell to see its message."))
    return styles, tooltips, messages


def register_reference_table_validation(ids) -> None:
    """Refresh feedback after edits, presets, or a switch of particle model."""
    @dash.callback(
        dash.Output(ids.bead_table, "style_data_conditional"),
        dash.Output(ids.bead_table, "tooltip_data"),
        dash.Output(ids.bead_table_validation, "children"),
        dash.Input(ids.bead_table, "data"),
        dash.Input(ids.bead_table, "columns"),
        dash.Input(ids.bead_table, "active_cell"),
    )
    def update_reference_table_feedback(rows, columns, active_cell):
        return build_reference_table_feedback(rows, columns, active_cell)
