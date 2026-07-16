# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from pathlib import Path

import pytest

from RosettaX.pages.p21_fcs_slicer import services
from RosettaX.utils import directories
from RosettaX.utils.reader import FCSFile


@pytest.fixture(scope="module")
def sample_fcs_file_path() -> Path:
    for candidate_directory in (
        directories.fcs_data,
        directories.asset_directory / "sample-files",
    ):
        fcs_paths = sorted(candidate_directory.glob("*.fcs"))
        if fcs_paths:
            return fcs_paths[0]
    raise AssertionError("No bundled FCS sample file was found.")


def test_validate_selected_channels_preserves_original_fcs_order() -> None:
    assert services.validate_selected_channels(
        selected_channels=["SSC-A", "FSC-A"],
        available_channels=["Time", "FSC-A", "SSC-A"],
    ) == ["FSC-A", "SSC-A"]


def test_validate_selected_channels_requires_at_least_one_channel() -> None:
    with pytest.raises(ValueError, match="at least one"):
        services.validate_selected_channels(
            selected_channels=[],
            available_channels=["FSC-A"],
        )


def test_save_uploaded_batch_keeps_duplicate_original_names_without_overwriting(
    tmp_path: Path,
) -> None:
    contents = "data:application/octet-stream;base64," + base64.b64encode(b"FCS").decode()

    saved_paths, filenames = services.save_uploaded_batch(
        contents=[contents, contents],
        filenames=["same.fcs", "same.fcs"],
        upload_directory=tmp_path,
    )

    assert filenames == ["same.fcs", "same.fcs"]
    assert saved_paths[0] != saved_paths[1]
    assert all(path.read_bytes() == b"FCS" for path in saved_paths)


def test_build_sliced_fcs_bytes_preserves_events_and_selected_metadata(
    sample_fcs_file_path: Path,
    tmp_path: Path,
) -> None:
    with FCSFile(sample_fcs_file_path, writable=False) as source_file:
        source_columns = source_file.get_column_names()
        selected_columns = source_columns[:2]
        expected_dataframe = source_file.dataframe_copy(
            columns=selected_columns,
            dtype=None,
        )
        expected_version = source_file.get_metadata().fcs_version

    payload = services.build_sliced_fcs_bytes(
        input_path=sample_fcs_file_path,
        selected_channels=selected_columns,
    )

    output_path = tmp_path / "test_sliced_output.fcs"
    try:
        output_path.write_bytes(payload)
        with FCSFile(output_path, writable=False) as sliced_file:
            assert sliced_file.get_column_names() == selected_columns
            assert sliced_file.get_metadata().fcs_version == expected_version
            sliced_dataframe = sliced_file.dataframe_copy(
                columns=selected_columns,
                dtype=None,
            )
        assert sliced_dataframe.equals(expected_dataframe)
    finally:
        output_path.unlink(missing_ok=True)


def test_build_sliced_fcs_zip_exports_each_input(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "build_sliced_fcs_bytes",
        lambda *, input_path, selected_channels: (
            f"{Path(input_path).name}:{','.join(selected_channels)}".encode()
        ),
    )

    payload = services.build_sliced_fcs_zip(
        file_paths=["/tmp/a.fcs", "/tmp/b.fcs"],
        filenames=["a.fcs", "b.fcs"],
        selected_channels=["SSC-A"],
        available_channels=["FSC-A", "SSC-A"],
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.namelist() == ["a_sliced.fcs", "b_sliced.fcs"]
        assert archive.read("a_sliced.fcs") == b"a.fcs:SSC-A"
