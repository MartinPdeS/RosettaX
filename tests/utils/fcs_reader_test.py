#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from RosettaX.utils import directories
from RosettaX.utils.reader import FCSFile


@pytest.fixture(scope="module")
def sample_fcs_file_path() -> Path:
    """
    Return one bundled FCS file from the RosettaX FCS data directory.
    """
    fcs_directory = directories.fcs_data

    assert fcs_directory.exists(), f"Missing FCS data directory: {fcs_directory}"
    assert fcs_directory.is_dir(), f"FCS data path is not a directory: {fcs_directory}"

    fcs_file_paths = sorted(fcs_directory.glob("*.fcs"))

    assert len(fcs_file_paths) > 0, f"No .fcs files found in: {fcs_directory}"

    return fcs_file_paths[0]


def test_fcs_reader_loads_sample_file(sample_fcs_file_path: Path) -> None:
    """
    Test that the bundled FCS file can be opened and exposes channel names.
    """
    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()

    assert isinstance(column_names, list)
    assert len(column_names) > 0
    assert all(isinstance(column_name, str) for column_name in column_names)
    assert all(column_name.strip() != "" for column_name in column_names)


def test_fcs_reader_returns_numeric_dataframe(sample_fcs_file_path: Path) -> None:
    """
    Test that the FCS reader returns a non empty numeric dataframe.
    """
    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()
        dataframe = fcs_file.dataframe_copy(
            columns=column_names,
            dtype=float,
            n=500,
        )

    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty
    assert list(dataframe.columns) == column_names
    assert len(dataframe) <= 500

    for column_name in dataframe.columns:
        assert np.issubdtype(dataframe[column_name].dtype, np.number)

    numeric_values = dataframe.to_numpy(dtype=float)

    assert numeric_values.size > 0
    assert np.isfinite(numeric_values).any()


def test_fcs_reader_can_select_column_subset(sample_fcs_file_path: Path) -> None:
    """
    Test that dataframe_copy respects explicit column selection.
    """
    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()
        selected_column_names = column_names[: min(3, len(column_names))]

        dataframe = fcs_file.dataframe_copy(
            columns=selected_column_names,
            dtype=float,
            n=100,
        )

    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty
    assert list(dataframe.columns) == selected_column_names
    assert len(dataframe) <= 100


def test_fcs_reader_dataframe_copy_is_owned_after_context_closes(sample_fcs_file_path: Path) -> None:
    """
    Test that dataframe_copy returns an owned dataframe that remains usable after
    the FCS file context is closed.
    """
    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()
        selected_column_names = column_names[: min(2, len(column_names))]

        dataframe = fcs_file.dataframe_copy(
            columns=selected_column_names,
            dtype=float,
            n=50,
        )

    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty

    copied_dataframe = dataframe.copy(deep=True)
    first_column_name = copied_dataframe.columns[0]
    first_value = copied_dataframe[first_column_name].iloc[0]

    assert np.isfinite(first_value)


def test_fcs_reader_dataframe_contains_fcs_metadata_attrs(sample_fcs_file_path: Path) -> None:
    """
    Test that dataframe_copy attaches the expected FCS metadata attributes.
    """
    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()

        dataframe = fcs_file.dataframe_copy(
            columns=column_names[: min(3, len(column_names))],
            dtype=float,
            n=100,
        )

    expected_attribute_names = {
        "fcs_header",
        "fcs_keywords",
        "fcs_detectors",
        "fcs_delimiter",
    }

    assert expected_attribute_names.issubset(dataframe.attrs.keys())

    assert dataframe.attrs["fcs_header"] is not None
    assert dataframe.attrs["fcs_keywords"] is not None
    assert dataframe.attrs["fcs_detectors"] is not None
    assert dataframe.attrs["fcs_delimiter"] is not None


def test_fcs_reader_respects_requested_number_of_events(sample_fcs_file_path: Path) -> None:
    """
    Test that the requested number of events limits the returned dataframe size.
    """
    requested_number_of_events = 10

    with FCSFile(sample_fcs_file_path) as fcs_file:
        column_names = fcs_file.get_column_names()

        dataframe = fcs_file.dataframe_copy(
            columns=column_names[: min(2, len(column_names))],
            dtype=float,
            n=requested_number_of_events,
        )

    assert isinstance(dataframe, pd.DataFrame)
    assert 0 < len(dataframe) <= requested_number_of_events


def test_fcs_reader_raises_for_missing_file() -> None:
    """
    Test that opening a missing FCS file fails explicitly.
    """
    missing_file_path = directories.fcs_data / "this_file_does_not_exist.fcs"

    with pytest.raises(FileNotFoundError):
        with FCSFile(missing_file_path):
            pass


if __name__ == "__main__":
    pytest.main(["-W", "error", __file__])