"""Regression tests for pages fluorescence reference table callbacks."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import dash

from RosettaX.pages.p02_fluorescence.sections.s03_table import callbacks


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
