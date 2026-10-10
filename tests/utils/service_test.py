"""Regression tests for utils service."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import json
from pathlib import Path

import pytest
from typing_extensions import Self

from RosettaX.utils import service


class _FakeFCSFile:
    """Test double for fake fcsfile."""

    def __init__(self, file_path: str, writable: bool = False) -> None:
        """Initialize the state required by this test double."""
        self.file_path = file_path
        self.writable = writable
        self.text = {
            "Detectors": {
                1: {"N": "FSC-A"},
                2: {},
                3: {"N": "FL1-A"},
            },
            "Keywords": {"$PAR": "3"},
        }

    def __enter__(self) -> Self:
        """Return the test reader when entering its context."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Handle context cleanup for the test reader."""
        return None


class Test_Service:
    """Regression checks for service."""

    @pytest.mark.parametrize(
        ("raw_name", "expected_name"),
        [
            ("  My calibration?.json  ", "My_calibration.json"),
            ("", "calibration"),
            (None, "calibration"),
        ],
    )
    def test_sanitize_filename_normalizes_values(
        self,
        raw_name: str | None,
        expected_name: str,
    ) -> None:
        """Check sanitize filename normalizes values."""
        assert service.sanitize_filename(raw_name) == expected_name

    def test_get_detector_column_names_from_file_reads_fcs_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Check get detector column names from file reads FCS metadata."""
        monkeypatch.setattr(service, "FCSFile", _FakeFCSFile)

        assert service.get_detector_column_names_from_file("/tmp/example.fcs") == [
            "FSC-A",
            "P2",
            "FL1-A",
        ]

    @pytest.mark.parametrize(
        ("column_name", "is_scatter", "is_invalid"),
        [
            (" FSC-A ", True, False),
            ("Time", False, True),
            ("FL1-A", False, False),
        ],
    )
    def test_detector_channel_helpers(
        self,
        column_name: str,
        is_scatter: bool,
        is_invalid: bool,
    ) -> None:
        """Check detector channel helpers."""
        assert service.is_scatter_channel(column_name) is is_scatter
        assert service.is_invalid_detector_channel(column_name) is is_invalid

    def test_resolve_default_dropdown_value_prefers_matching_value(self) -> None:
        """Check resolve default dropdown value prefers matching value."""
        options = [
            {"label": "FSC-A", "value": "FSC-A"},
            {"label": "FL1-A", "value": "FL1-A"},
        ]

        assert service.resolve_default_dropdown_value(
            options=options,
            preferred_value=" FL1-A ",
        ) == "FL1-A"

    def test_resolve_default_dropdown_value_falls_back_to_first_option(self) -> None:
        """Check resolve default dropdown value falls back to first option."""
        options = [{"label": "FSC-A", "value": "FSC-A"}]

        assert service.resolve_default_dropdown_value(
            options=options,
            preferred_value="missing",
        ) == "FSC-A"
        assert service.resolve_default_dropdown_value(
            options=[],
            preferred_value="missing",
        ) is None

    def test_save_calibration_to_file_writes_expected_json_record(
        self,
        tmp_path: Path,
    ) -> None:
        """Check save calibration to file writes expected JSON record."""
        payload = {"gain": 42, "channels": ["FSC-A"]}

        saved_calibration = service.save_calibration_to_file(
            name=" Test Calibration! ",
            payload=payload,
            calibration_kind="fluorescence",
            output_directory=tmp_path,
        )

        assert saved_calibration.folder == "fluorescence"
        assert saved_calibration.filename == "Test_Calibration.json"
        assert saved_calibration.path == tmp_path / "Test_Calibration.json"

        record = json.loads(saved_calibration.path.read_text(encoding="utf-8"))

        assert record["schema"] == "rosettax_calibration_v1"
        assert record["kind"] == "fluorescence"
        assert record["name"] == " Test Calibration! "
        assert record["payload"] == payload
        assert record["created_at"]
        assert record["reproducibility"]["fingerprint"]
        assert service.verify_reproducibility_metadata(
            calibration_kind=record["kind"],
            payload=record["payload"],
            metadata=record["reproducibility"],
        ) is True

    def test_reproducibility_fingerprint_is_stable_and_detects_payload_changes(self) -> None:
        """Check reproducibility fingerprint is stable and detects payload changes."""
        payload = {"gain": 42, "channels": ["FSC-A"]}

        first = service.build_reproducibility_metadata(
            calibration_kind="fluorescence",
            payload=payload,
        )
        second = service.build_reproducibility_metadata(
            calibration_kind="fluorescence",
            payload={"channels": ["FSC-A"], "gain": 42},
        )
        changed = service.build_reproducibility_metadata(
            calibration_kind="fluorescence",
            payload={"gain": 43, "channels": ["FSC-A"]},
        )

        assert first == second
        assert first["fingerprint"] != changed["fingerprint"]
        assert service.verify_reproducibility_metadata(
            calibration_kind="fluorescence",
            payload=payload,
            metadata=changed,
        ) is False

    def test_list_saved_calibrations_from_directory_returns_sorted_json_files(
        self,
        tmp_path: Path,
    ) -> None:
        """Check list saved calibrations from directory returns sorted JSON files."""
        (tmp_path / "b.json").write_text("{}", encoding="utf-8")
        (tmp_path / "a.json").write_text("{}", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

        assert service.list_saved_calibrations_from_directory(directory=tmp_path) == [
            "a.json",
            "b.json",
        ]

    def test_list_saved_calibrations_from_directory_returns_empty_list_when_empty(
        self,
        tmp_path: Path,
    ) -> None:
        """Check list saved calibrations from directory returns empty list when empty."""
        assert service.list_saved_calibrations_from_directory(directory=tmp_path) == []

    @pytest.mark.parametrize(
        ("uploaded_fcs_path_data", "expected_path"),
        [
            (None, None),
            (" /tmp/data.fcs ", "/tmp/data.fcs"),
            ([["/tmp/nested.fcs"]], "/tmp/nested.fcs"),
            ([[]], None),
            ([None], None),
            ("   ", None),
        ],
    )
    def test_resolve_first_fcs_path(
        self,
        uploaded_fcs_path_data: object,
        expected_path: str | None,
    ) -> None:
        """Check resolve first FCS path."""
        assert service.resolve_first_fcs_path(uploaded_fcs_path_data) == expected_path
