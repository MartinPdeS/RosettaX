# -*- coding: utf-8 -*-
"""
Tests for RosettaX.utils.service utility functions.
"""

import json
from pathlib import Path

import pytest

from RosettaX.utils.service import (
    is_invalid_detector_channel,
    is_scatter_channel,
    list_saved_calibrations_from_directory,
    resolve_default_dropdown_value,
    resolve_first_fcs_path,
    sanitize_filename,
    save_calibration_to_file,
)


class Test_SanitizeFilename:
    @pytest.mark.parametrize(
        ("raw_name", "expected_stem"),
        [
            ("My Calibration", "My_Calibration"),
            ("  leading and trailing  ", "leading_and_trailing"),
            ("special!@#chars", "specialchars"),
            ("with (parens) and.dots", "with_(parens)_and.dots"),
            ("", "calibration"),
            (None, "calibration"),
            ("   ", "calibration"),
            ("multiple   spaces", "multiple_spaces"),
        ],
    )
    def test_sanitize_filename(self, raw_name: object, expected_stem: str) -> None:
        assert sanitize_filename(raw_name) == expected_stem


class Test_IsScatterChannel:
    @pytest.mark.parametrize(
        "column_name",
        ["FSC-A", "SSC-H", "SCATTER_1", "fsc-a", "488LS", "SALS"],
    )
    def test_scatter_channel_is_recognized(self, column_name: str) -> None:
        assert is_scatter_channel(column_name) is True

    @pytest.mark.parametrize(
        "column_name",
        ["FITC-A", "PE-H", "APC-A", "BV421", ""],
    )
    def test_non_scatter_channel_is_not_recognized(self, column_name: str) -> None:
        assert is_scatter_channel(column_name) is False


class Test_IsInvalidDetectorChannel:
    @pytest.mark.parametrize(
        "column_name",
        ["Time", "Width", "Diameter", "cross section"],
    )
    def test_invalid_channel_is_recognized(self, column_name: str) -> None:
        assert is_invalid_detector_channel(column_name) is True

    @pytest.mark.parametrize(
        "column_name",
        ["FSC-A", "FITC-A", "PE-H", ""],
    )
    def test_valid_channel_is_not_excluded(self, column_name: str) -> None:
        assert is_invalid_detector_channel(column_name) is False


class Test_ResolveDefaultDropdownValue:
    def test_returns_preferred_value_when_present_in_options(self) -> None:
        options = [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}]
        result = resolve_default_dropdown_value(options=options, preferred_value="B")
        assert result == "B"

    def test_falls_back_to_first_option_when_preferred_absent(self) -> None:
        options = [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}]
        result = resolve_default_dropdown_value(options=options, preferred_value="C")
        assert result == "A"

    def test_returns_none_when_options_empty(self) -> None:
        result = resolve_default_dropdown_value(options=[], preferred_value="A")
        assert result is None

    def test_returns_none_when_preferred_is_none_and_options_empty(self) -> None:
        result = resolve_default_dropdown_value(options=[], preferred_value=None)
        assert result is None

    def test_returns_first_option_when_preferred_is_none(self) -> None:
        options = [{"label": "X", "value": "X"}]
        result = resolve_default_dropdown_value(options=options, preferred_value=None)
        assert result == "X"


class Test_ResolveFirstFcsPath:
    def test_returns_plain_string(self) -> None:
        assert resolve_first_fcs_path("/data/sample.fcs") == "/data/sample.fcs"

    def test_unwraps_single_element_list(self) -> None:
        assert resolve_first_fcs_path(["/data/sample.fcs"]) == "/data/sample.fcs"

    def test_unwraps_nested_list(self) -> None:
        assert resolve_first_fcs_path([["/data/sample.fcs"]]) == "/data/sample.fcs"

    def test_returns_none_for_none_input(self) -> None:
        assert resolve_first_fcs_path(None) is None

    def test_returns_none_for_empty_list(self) -> None:
        assert resolve_first_fcs_path([]) is None

    def test_returns_none_for_blank_string(self) -> None:
        assert resolve_first_fcs_path("   ") is None

    def test_returns_none_for_nested_empty_list(self) -> None:
        assert resolve_first_fcs_path([[]]) is None


class Test_ListSavedCalibrationsFromDirectory:
    def test_returns_sorted_json_filenames(self, tmp_path: Path) -> None:
        (tmp_path / "zebra.json").write_text("{}")
        (tmp_path / "apple.json").write_text("{}")
        (tmp_path / "not_a_json.txt").write_text("text")

        result = list_saved_calibrations_from_directory(directory=tmp_path)

        assert result == ["apple.json", "zebra.json"]

    def test_returns_empty_list_for_empty_directory(self, tmp_path: Path) -> None:
        result = list_saved_calibrations_from_directory(directory=tmp_path)
        assert result == []

    def test_ignores_subdirectories(self, tmp_path: Path) -> None:
        (tmp_path / "subdir.json").mkdir()
        (tmp_path / "real.json").write_text("{}")

        result = list_saved_calibrations_from_directory(directory=tmp_path)

        assert result == ["real.json"]


class Test_SaveCalibrationToFile:
    def test_saves_json_file_with_correct_schema(self, tmp_path: Path) -> None:
        info = save_calibration_to_file(
            name="My Calibration",
            payload={"slope": 1.0, "intercept": 0.0},
            calibration_kind="fluorescence",
            output_directory=tmp_path,
        )

        assert info.path.exists()
        assert info.filename == "My_Calibration.json"
        assert info.folder == "fluorescence"

        record = json.loads(info.path.read_text(encoding="utf-8"))

        assert record["schema"] == "rosettax_calibration_v1"
        assert record["kind"] == "fluorescence"
        assert record["name"] == "My Calibration"
        assert record["payload"] == {"slope": 1.0, "intercept": 0.0}
        assert "created_at" in record

    def test_falls_back_to_calibration_for_empty_name(self, tmp_path: Path) -> None:
        info = save_calibration_to_file(
            name="",
            payload={"k": "v"},
            calibration_kind="scattering",
            output_directory=tmp_path,
        )

        assert info.filename == "calibration.json"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
