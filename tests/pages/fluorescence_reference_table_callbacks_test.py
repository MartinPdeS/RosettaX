"""Regression tests for pages fluorescence reference table callbacks."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import dash
import pytest
from RosettaX.pages.p02_fluorescence.ids import CalibrationSectionIds
from RosettaX.pages.p02_fluorescence.sections.s03_table import callbacks
from types import SimpleNamespace


class Test_FluorescenceReferenceTableCallbacks:
    """Regression checks for fluorescence reference table callbacks."""

    def test_first_detector_selection_only_updates_page_state(self) -> None:
        """Check first detector selection only updates page state."""
        table_result, page_state_result = callbacks.resolve_detector_change_reset(
            detector_dropdown_values=["B1-H"],
            page_state_payload=None,
            current_table_rows=[
                {"col1": "100", "col2": "200"},
                {"col1": "", "col2": ""},
            ],
        )

        assert table_result is dash.no_update
        assert page_state_result["last_detector_channels"] == ["B1-H"]

    def test_detector_change_resets_reference_table_rows(self) -> None:
        """Check detector change resets reference table rows."""
        table_result, page_state_result = callbacks.resolve_detector_change_reset(
            detector_dropdown_values=["R1-H"],
            page_state_payload={
                "last_detector_channels": ["B1-H"],
                "reference_table_rows": [
                    {"col1": "100", "col2": "200"},
                    {"col1": "300", "col2": "400"},
                ],
            },
            current_table_rows=[
                {"col1": "100", "col2": "200"},
                {"col1": "300", "col2": "400"},
            ],
        )

        assert table_result == [
            {"col1": "", "col2": ""},
            {"col1": "", "col2": ""},
            {"col1": "", "col2": ""},
        ]
        assert page_state_result["last_detector_channels"] == ["R1-H"]
        assert page_state_result["reference_table_rows"] == table_result

    def test_add_row_preserves_current_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Clicking Add row appends one blank row to the table."""
        registered = []
        monkeypatch.setattr(
            dash, "callback", lambda *args, **kwargs: registered.append,
        )
        section = SimpleNamespace(ids=CalibrationSectionIds(prefix="test"))
        callbacks._register_add_row_callback(section)

        current_rows = [{"col1": "100", "col2": "200"}]
        assert registered[0](1, current_rows) == [
            {"col1": "100", "col2": "200"},
            {"col1": "", "col2": ""},
        ]
        assert registered[0](1, []) == [{"col1": "", "col2": ""}]

    def test_profile_load_populates_standard_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Loading a profile populates the table with its saved intensities."""
        registered = []
        monkeypatch.setattr(
            dash, "callback", lambda *args, **kwargs: registered.append,
        )
        monkeypatch.setattr(dash, "ctx", SimpleNamespace(triggered_id="runtime-config-store"))
        section = SimpleNamespace(ids=CalibrationSectionIds(prefix="test"))
        callbacks._register_runtime_table_sync_callback(section)

        profile_config = {"calibration": {"mesf_values": [123, 456]}}
        current_rows = [{"col1": "100", "col2": "200"}]
        assert registered[0](profile_config, None, current_rows) is dash.no_update
        assert registered[0](profile_config, {"profile_name": "Custom"}, current_rows) == [
            {"col1": "123", "col2": ""},
            {"col1": "456", "col2": ""},
        ]
