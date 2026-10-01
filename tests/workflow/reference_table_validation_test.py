import pytest

from RosettaX.workflow.table.validation import (
    build_reference_table_feedback,
    validate_reference_table_cells,
)

COLUMNS = [
    {"id": "diameter", "name": "Diameter [nm]", "editable": True},
    {"id": "coupling", "name": "Coupling [W]", "editable": False},
]


@pytest.mark.parametrize("value", ["bad", "NaN", "inf", True, 0, -1])
def test_invalid_editable_values_are_reported_without_changing_rows(value):
    rows = [{"diameter": value, "coupling": "not yet computed"}]
    issues = validate_reference_table_cells(rows, COLUMNS)
    assert len(issues) == 1
    assert issues[0].column_id == "diameter"
    assert issues[0].row_index == 0
    assert rows[0]["diameter"] == value


@pytest.mark.parametrize("value", [None, "", " ", "1,45", "1e3", 100.0])
def test_partial_rows_and_valid_numeric_formats_remain_unmarked(value):
    assert validate_reference_table_cells([{"diameter": value}], COLUMNS) == []


def test_feedback_clears_after_correction_and_column_changes():
    styles, tooltips, messages = build_reference_table_feedback([{"diameter": -1}], COLUMNS)
    assert tooltips[0]["diameter"]["value"] == "Enter a value greater than zero."
    assert messages[0].children.startswith("Row 1 · Diameter [nm]")
    assert styles[-1]["if"] == {"row_index": 0, "column_id": "diameter"}
    corrected_styles, corrected_tooltips, corrected_messages = build_reference_table_feedback(
        [{"diameter": 100}], COLUMNS,
    )
    assert len(corrected_styles) == len(styles) - 1
    assert corrected_tooltips == [{}]
    assert corrected_messages == []
    assert validate_reference_table_cells([{"diameter": -1}], []) == []


def test_selected_invalid_cell_message_remains_visible_in_long_tables():
    rows = [{"diameter": -1} for _ in range(10)]
    _, _, messages = build_reference_table_feedback(rows, COLUMNS, {"row": 9, "column_id": "diameter"})
    assert messages[0].children.startswith("Row 10 ·")
    assert "5 more invalid cells" in messages[-1].children
