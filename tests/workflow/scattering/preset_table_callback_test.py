"""Regression checks that compute coupling no longer uses a scatterer preset."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

from RosettaX.pages.p03_scattering.sections.s04_table.main import ReferenceTable


def test_compute_coupling_has_no_scatterer_preset_table_callback() -> None:
    """The compute coupling section relies on editable user supplied rows."""
    assert not hasattr(ReferenceTable, "_register_scatterer_preset_table_callback")
