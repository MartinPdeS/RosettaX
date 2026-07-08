import json
from pathlib import Path

import pytest

from RosettaX.utils import service


class _FakeFCSFile:
    def __init__(self, file_path: str, writable: bool = False) -> None:
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

    def __enter__(self) -> "_FakeFCSFile":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class Test_Service:
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
        assert service.sanitize_filename(raw_name) == expected_name

    def test_get_detector_column_names_from_file_reads_fcs_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
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
        assert service.is_scatter_channel(column_name) is is_scatter
        assert service.is_invalid_detector_channel(column_name) is is_invalid

    def test_resolve_default_dropdown_value_prefers_matching_value(self) -> None:
        options = [
            {"label": "FSC-A", "value": "FSC-A"},
            {"label": "FL1-A", "value": "FL1-A"},
        ]

        assert service.resolve_default_dropdown_value(
            options=options,
            preferred_value=" FL1-A ",
        ) == "FL1-A"

    def test_resolve_default_dropdown_value_falls_back_to_first_option(self) -> None:
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

    def test_list_saved_calibrations_from_directory_returns_sorted_json_files(
        self,
        tmp_path: Path,
    ) -> None:
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
        assert service.resolve_first_fcs_path(uploaded_fcs_path_data) == expected_path
