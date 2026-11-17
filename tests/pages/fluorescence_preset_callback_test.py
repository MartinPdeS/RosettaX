"""Tests for fluorescence reference preset selection."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash
import pytest
from RosettaX.pages.p02_fluorescence.sections.s03_table import callbacks
from types import SimpleNamespace


@pytest.mark.parametrize("preset", ["", "Custom", "Rosetta Mix"])
def test_selecting_preset_replaces_old_rows(monkeypatch, preset):
    """A user selection clears existing rows before applying its preset."""
    registered = []
    monkeypatch.setattr(dash, "callback", lambda *args, **kwargs: lambda function: registered.append(function))
    monkeypatch.setattr(dash, "ctx", SimpleNamespace(triggered_id="preset"))
    section = SimpleNamespace(ids=SimpleNamespace(bead_table="table", bead_table_preset_dropdown="preset"))
    callbacks._register_runtime_table_sync_callback(section)
    rows, selected = registered[0]({}, None, preset, [{"col1": "1", "col2": "999"}])
    assert selected is dash.no_update
    if preset == "Rosetta Mix":
        assert len(rows) == 6
        assert all(row["col2"] == "" for row in rows)
    else:
        assert rows == []


def test_profile_load_preserves_custom_values(monkeypatch):
    """Loading a profile with custom intensities populates both outputs."""
    registered = []
    monkeypatch.setattr(dash, "callback", lambda *args, **kwargs: lambda function: registered.append(function))
    monkeypatch.setattr(dash, "ctx", SimpleNamespace(triggered_id="runtime-config-store"))
    section = SimpleNamespace(ids=SimpleNamespace(bead_table="table", bead_table_preset_dropdown="preset"))
    callbacks._register_runtime_table_sync_callback(section)
    rows, preset = registered[0]({"calibration": {"mesf_values": [123, 456]}}, {"event": 1}, "Rosetta Mix", [])
    assert preset == "Custom"
    assert [row["col1"] for row in rows] == ["123", "456"]
