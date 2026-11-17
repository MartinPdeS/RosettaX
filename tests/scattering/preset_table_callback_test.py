"""Regression tests for scatterer preset table updates."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash
import pytest
from RosettaX.pages.p03_scattering.sections.s04_table.main import ReferenceTable
from RosettaX.workflow.scattering.model import ROSETTA_MIX_PRESET_NAME
from types import SimpleNamespace


@pytest.mark.parametrize(
    ("preset", "trigger", "expected"),
    [
        ("", "preset", "empty"),
        (None, "preset", "empty"),
        ("Custom", "preset", "empty"),
        ("Custom", "wavelength", "unchanged"),
        ("", "wavelength", "unchanged"),
        (ROSETTA_MIX_PRESET_NAME, "preset", "replaced"),
        (ROSETTA_MIX_PRESET_NAME, "wavelength", "preserved"),
    ],
)
def test_preset_table_updates(monkeypatch, preset, trigger, expected):
    """Clear or preserve rows according to the selected preset and trigger."""
    callbacks = []
    monkeypatch.setattr(dash, "callback", lambda *args, **kwargs: lambda function: callbacks.append(function))
    monkeypatch.setattr(dash, "ctx", SimpleNamespace(triggered_prop_ids={f"{trigger}.value": trigger}))
    section = ReferenceTable.__new__(ReferenceTable)
    section.ids = SimpleNamespace(bead_table="table")
    section.page = SimpleNamespace(ids=SimpleNamespace(Parameters=SimpleNamespace(scatterer_preset="preset", wavelength_nm="wavelength")))
    section._register_scatterer_preset_table_callback()

    columns, rows = callbacks[0](preset, 488, [{"measured_peak_position": "123"}])

    if expected == "empty":
        assert columns is dash.no_update
        assert rows == []
    elif expected == "unchanged":
        assert columns is dash.no_update
        assert rows is dash.no_update
    else:
        assert rows[0]["particle_diameter_nm"] == "994"
        assert rows[0]["measured_peak_position"] == ("123" if expected == "preserved" else "")
