"""Regression tests for workflow reference table validation."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

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
    """Check invalid editable values are reported without changing rows."""
    rows = [{"diameter": value, "coupling": "not yet computed"}]
    issues = validate_reference_table_cells(rows, COLUMNS)
    assert len(issues) == 1
    assert issues[0].column_id == "diameter"
    assert issues[0].row_index == 0
    assert rows[0]["diameter"] == value


@pytest.mark.parametrize("value", [None, "", " ", "1,45", "1e3", 100.0])
def test_partial_rows_and_valid_numeric_formats_remain_unmarked(value):
    """Check partial rows and valid numeric formats remain unmarked."""
    assert validate_reference_table_cells([{"diameter": value}], COLUMNS) == []


def test_feedback_clears_after_correction_and_column_changes():
    """Check feedback clears after correction and column changes."""
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
    """Check selected invalid cell message remains visible in long tables."""
    rows = [{"diameter": -1} for _ in range(10)]
    _, _, messages = build_reference_table_feedback(rows, COLUMNS, {"row": 9, "column_id": "diameter"})
    assert messages[0].children.startswith("Row 10 ·")
    assert "5 more invalid cells" in messages[-1].children


@pytest.mark.parametrize(
    "column_id",
    [
        "particle_refractive_index",
        "medium_refractive_index",
        "core_refractive_index",
        "shell_refractive_index",
    ],
)
def test_material_labels_are_valid_for_refractive_index_columns(column_id):
    """Preset labels are accepted for every scattering refractive index."""
    columns = [{"id": column_id, "name": "Refractive index", "editable": True}]
    rows = [{column_id: "Polystyrene(1.59796)"}, {column_id: "Water(1.33698)"}]

    assert validate_reference_table_cells(rows, columns) == []
    assert build_reference_table_feedback(rows, columns)[2] == []


@pytest.mark.parametrize("value", ["Water(NaN)", "Water(inf)", "Water(0)", "Water(-1)", "Water(1.3) extra"])
def test_invalid_material_labels_are_reported(value):
    """Malformed, non-finite, and nonpositive labeled indices remain invalid."""
    columns = [{"id": "medium_refractive_index", "editable": True}]

    assert len(validate_reference_table_cells([{"medium_refractive_index": value}], columns)) == 1


def test_material_labels_are_not_valid_in_numeric_columns():
    """Material labels are restricted to refractive-index columns."""
    assert len(validate_reference_table_cells([{"diameter": "Water(1.33698)"}], COLUMNS)) == 1
