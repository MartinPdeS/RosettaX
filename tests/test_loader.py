"""
Tests for RosettaX.reader.FCSFile.

These tests assume that RosettaX.directories.fcs_data / "sample.fcs"
is a valid FCS file that can be parsed successfully.
"""

from pathlib import Path

import pandas as pd
import pytest

from RosettaX.reader import FCSFile
from RosettaX.directories import fcs_data


def test_fcsfile_parses_header_and_text() -> None:
    """FCSFile loads header and text metadata from a valid sample file."""
    sample_path = fcs_data / "sample.fcs"
    reader = FCSFile(sample_path)

    # Header basic checks
    assert isinstance(reader.header, dict)
    assert reader.header["FCS version"] in {"FCS2.0", "FCS3.0", "FCS3.1"}
    assert "Text start" in reader.header
    assert "Text end" in reader.header
    assert "Data start" in reader.header
    assert "Data end" in reader.header

    # Text structure checks
    assert isinstance(reader.text, dict)
    assert "Keywords" in reader.text
    assert "Detectors" in reader.text

    keywords = reader.text["Keywords"]
    detectors = reader.text["Detectors"]

    assert "$PAR" in keywords
    assert "$TOT" in keywords

    # Detector metadata must match number of parameters
    num_parameters = keywords["$PAR"]
    assert len(detectors) == num_parameters

    # Each detector should have at least a name "N"
    for detector_index, detector_info in detectors.items():
        assert isinstance(detector_index, int)
        assert "N" in detector_info
        assert isinstance(detector_info["N"], str)


def test_read_all_data_shape_and_columns() -> None:
    """read_all_data returns a DataFrame that matches metadata and detector names."""
    sample_path = fcs_data / "sample.fcs"
    reader = FCSFile(sample_path)
    data_frame = reader.read_all_data()

    assert isinstance(data_frame, pd.DataFrame)

    keywords = reader.text["Keywords"]
    detectors = reader.text["Detectors"]

    num_events = keywords["$TOT"]
    num_parameters = keywords["$PAR"]

    # Shape must match header metadata
    assert data_frame.shape == (num_events, num_parameters)

    # Column names must match detector names $PnN
    expected_columns = [
        detectors[index]["N"] for index in range(1, num_parameters + 1)
    ]
    assert list(data_frame.columns) == expected_columns


def test_FCSFile_alias() -> None:
    """The legacy FCSFile alias should behave like FCSFile."""
    sample_path = fcs_data / "sample.fcs"
    reader = FCSFile(sample_path)  # alias

    assert isinstance(reader, FCSFile)
    data_frame = reader.read_all_data()
    assert isinstance(data_frame, pd.DataFrame)


def test_missing_file_raises(tmp_path: Path) -> None:
    """Construction with a missing file should raise FileNotFoundError."""
    missing_path = tmp_path / "does_not_exist.fcs"
    with pytest.raises(FileNotFoundError):
        FCSFile(missing_path)


def test_too_small_file_raises(tmp_path: Path) -> None:
    """Files that are smaller than the minimal header size are rejected."""
    tiny_file = tmp_path / "tiny.fcs"
    tiny_file.write_bytes(b"123")  # clearly shorter than 257 bytes

    with pytest.raises(FileNotFoundError):
        FCSFile(tiny_file)



if __name__ == "__main__":
    pytest.main(["-W error", __file__])