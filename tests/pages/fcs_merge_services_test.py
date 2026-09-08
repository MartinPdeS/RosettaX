# -*- coding: utf-8 -*-

from pathlib import Path

import pandas as pd
import pytest

from RosettaX.pages.p24_fcs_merge import services
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


def test_build_merged_fcs_bytes_concatenates_events_in_input_order(
    sample_fcs_file_path: Path,
    tmp_path: Path,
) -> None:
    with FCSFile(sample_fcs_file_path, writable=False) as source_file:
        columns = source_file.get_column_names()
        first_dataframe = source_file.dataframe_copy(columns=columns, dtype=None)
        second_dataframe = first_dataframe.copy()
        second_dataframe.iloc[:, 0] += 1
        second_path = tmp_path / "second.fcs"
        second_path.write_bytes(
            FCSFile.builder_from_dataframe(
                second_dataframe,
                template=source_file,
                force_float32=False,
            ).build_bytes()
        )
        expected_dataframe = pd.concat(
            [first_dataframe, second_dataframe],
            ignore_index=True,
        )
        expected_version = source_file.get_metadata().fcs_version

    payload = services.build_merged_fcs_bytes(
        file_paths=[sample_fcs_file_path, second_path],
    )

    merged_path = tmp_path / "merged.fcs"
    merged_path.write_bytes(payload)
    with FCSFile(merged_path, writable=False) as merged_file:
        assert merged_file.get_column_names() == columns
        assert merged_file.get_metadata().fcs_version == expected_version
        merged_dataframe = merged_file.dataframe_copy(columns=columns, dtype=None)
    assert merged_dataframe.equals(expected_dataframe)


def test_validate_merge_input_paths_reports_incompatible_files(monkeypatch) -> None:
    monkeypatch.setattr(
        services.upload_services,
        "inspect_compatible_fcs_batch",
        lambda _paths: {
            "are_all_files_consistent": False,
            "column_name_consistency": {
                "are_all_files_consistent": False,
                "mismatch_details": ["second.fcs: columns do not match first.fcs"],
            },
        },
    )

    with pytest.raises(ValueError, match="Invalid channels"):
        services.validate_merge_input_paths(["first.fcs", "second.fcs"])


def test_build_merged_export_filename_uses_first_file_stem() -> None:
    assert services.build_merged_export_filename("acquisition.fcs") == "acquisition_merged.fcs"
