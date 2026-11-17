"""Tests for adding custom scattering particle dimensions."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import pytest
from RosettaX.pages.p03_scattering.sections.s04_table.services import (
    add_custom_diameter_rows,
)


def test_add_solid_sphere_diameters():
    """Append all diameters while preserving existing rows."""
    rows = add_custom_diameter_rows(mie_model="Solid Sphere", diameters="100, 200", shell_thicknesses="", current_rows=[{"particle_diameter_nm": "50"}])
    assert [row["particle_diameter_nm"] for row in rows] == ["50", "100", "200"]


@pytest.mark.parametrize("thicknesses,expected", [("10", ["10", "10"]), ("10, 20", ["10", "20"])])
def test_add_core_shell_dimensions(thicknesses, expected):
    """Pair core diameters with one shared or individually specified thickness."""
    rows = add_custom_diameter_rows(mie_model="Core/Shell Sphere", diameters="100, 200", shell_thicknesses=thicknesses, current_rows=[])
    assert [row["core_diameter_nm"] for row in rows] == ["100", "200"]
    assert [row["shell_thickness_nm"] for row in rows] == expected
    assert [row["outer_diameter_nm"] for row in rows] == [str(100 + 2 * int(expected[0])), str(200 + 2 * int(expected[1]))]


@pytest.mark.parametrize("diameters,thicknesses", [("", "10"), ("-1", "10"), ("nan", "10"), ("100, 200", "1, 2, 3"), ("100", "-1")])
def test_invalid_dimensions_are_rejected(diameters, thicknesses):
    """Reject missing, nonphysical, or unmatched dimensions."""
    with pytest.raises(ValueError):
        add_custom_diameter_rows(mie_model="Core/Shell Sphere", diameters=diameters, shell_thicknesses=thicknesses, current_rows=[])
