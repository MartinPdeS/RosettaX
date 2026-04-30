# -*- coding: utf-8 -*-
"""
Tests for RosettaX.utils.io I/O helpers.
"""

from pathlib import Path

import numpy as np
import pytest

from RosettaX.utils import directories
from RosettaX.utils.io import column_copy, get_column_names, load_signal


@pytest.fixture(scope="module")
def sample_fcs_path() -> str:
    fcs_directory = directories.fcs_data
    fcs_files = sorted(fcs_directory.glob("*.fcs"))
    assert fcs_files, f"No .fcs files found in {fcs_directory}"
    return str(fcs_files[0])


@pytest.fixture(scope="module")
def first_column(sample_fcs_path: str) -> str:
    names = get_column_names(sample_fcs_path)
    assert names, "FCS file has no column names"
    return names[0]


class Test_GetColumnNames:
    def test_returns_non_empty_list_of_strings(self, sample_fcs_path: str) -> None:
        names = get_column_names(sample_fcs_path)
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) and n.strip() for n in names)

    def test_raises_for_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            get_column_names("/nonexistent/path/file.fcs")


class Test_LoadSignal:
    def test_returns_finite_float_array(
        self, sample_fcs_path: str, first_column: str
    ) -> None:
        signal = load_signal(sample_fcs_path, first_column)
        assert isinstance(signal, np.ndarray)
        assert signal.ndim == 1
        assert np.all(np.isfinite(signal))

    def test_respects_max_events_limit(
        self, sample_fcs_path: str, first_column: str
    ) -> None:
        signal = load_signal(
            sample_fcs_path, first_column, max_events_for_analysis=50
        )
        assert len(signal) <= 50

    def test_require_positive_values_removes_non_positives(
        self, sample_fcs_path: str, first_column: str
    ) -> None:
        signal = load_signal(
            sample_fcs_path, first_column, require_positive_values=True
        )
        assert np.all(signal > 0)

    def test_raises_for_empty_column_name(self, sample_fcs_path: str) -> None:
        with pytest.raises(ValueError, match="non empty"):
            load_signal(sample_fcs_path, "")

    def test_raises_for_blank_column_name(self, sample_fcs_path: str) -> None:
        with pytest.raises(ValueError, match="non empty"):
            load_signal(sample_fcs_path, "   ")


class Test_ColumnCopy:
    def test_returns_owned_array(
        self, sample_fcs_path: str, first_column: str
    ) -> None:
        arr = column_copy(sample_fcs_path, first_column)
        assert isinstance(arr, np.ndarray)
        assert arr.ndim == 1
        assert arr.dtype == float

    def test_respects_n_limit(
        self, sample_fcs_path: str, first_column: str
    ) -> None:
        arr = column_copy(sample_fcs_path, first_column, n=20)
        assert len(arr) <= 20


if __name__ == "__main__":
    pytest.main(["-v", __file__])
