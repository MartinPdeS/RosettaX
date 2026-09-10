from pathlib import Path

import pytest

from RosettaX.workflow.upload import services
from RosettaX.workflow.upload.models import FCSBatchOperationResult


def test_load_fcs_batch_persists_validates_and_preserves_upload_order(
    monkeypatch,
) -> None:
    saved_paths = [Path("saved-second.fcs"), Path("saved-first.fcs")]
    saved_filenames = ["second.fcs", "first.fcs"]
    consistency_report = {
        "are_all_files_consistent": True,
        "reference_column_names": ["FSC-A", "SSC-A"],
        "reference_fcs_version": "FCS3.1",
    }
    save_calls = []

    def save_batch(**kwargs):
        save_calls.append(kwargs)
        return saved_paths, saved_filenames

    monkeypatch.setattr(services, "save_uploaded_batch", save_batch)
    monkeypatch.setattr(
        services,
        "inspect_compatible_fcs_batch",
        lambda paths: consistency_report,
    )

    result = services.load_fcs_batch(
        contents=["second-content", "first-content"],
        filenames=["second.fcs", "first.fcs"],
        upload_directory=Path("uploads"),
        max_upload_bytes=1024,
    )

    assert isinstance(result, FCSBatchOperationResult)
    assert result.is_compatible is True
    assert result.feedback.to_display_tuple() == (
        ("Loaded 2 compatible FCS files with 2 channels (FCS3.1). "
        "Files: second.fcs, first.fcs."),
        "success",
    )
    assert result.batch is not None
    assert [file.path for file in result.batch.files] == [
        "saved-second.fcs",
        "saved-first.fcs",
    ]
    assert [file.filename for file in result.batch.files] == saved_filenames
    assert all(
        file.column_names == ("FSC-A", "SSC-A") for file in result.batch.files
    )
    assert result.batch.reference_column_names == ("FSC-A", "SSC-A")
    assert save_calls == [
        {
            "contents": ["second-content", "first-content"],
            "filenames": ["second.fcs", "first.fcs"],
            "upload_directory": Path("uploads"),
            "max_upload_bytes": 1024,
        }
    ]


def test_load_fcs_batch_returns_standard_feedback_for_incompatible_files(
    monkeypatch,
) -> None:
    consistency_report = {
        "are_all_files_consistent": False,
        "column_name_consistency": {
            "are_all_files_consistent": False,
            "mismatch_details": ["second.fcs does not contain SSC-A."],
        },
    }
    monkeypatch.setattr(
        services,
        "save_uploaded_batch",
        lambda **_kwargs: ([Path("first.fcs"), Path("second.fcs")], ["first.fcs", "second.fcs"]),
    )
    monkeypatch.setattr(
        services,
        "inspect_compatible_fcs_batch",
        lambda _paths: consistency_report,
    )

    result = services.load_fcs_batch(
        contents=["first-content", "second-content"],
        filenames=["first.fcs", "second.fcs"],
    )

    assert result.is_compatible is False
    assert result.batch is None
    assert result.feedback.color == "danger"
    assert "Invalid channels or missing channel metadata" in result.feedback.message
    with pytest.raises(ValueError, match="cannot be used together"):
        services.load_compatible_fcs_batch(
            contents=["first-content", "second-content"],
            filenames=["first.fcs", "second.fcs"],
        )


def test_load_fcs_batch_enforces_the_requested_minimum_without_inspection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        services,
        "save_uploaded_batch",
        lambda **_kwargs: ([Path("only.fcs")], ["only.fcs"]),
    )
    monkeypatch.setattr(
        services,
        "inspect_compatible_fcs_batch",
        lambda _paths: pytest.fail("A too-small batch must not be inspected."),
    )

    result = services.load_fcs_batch(
        contents=["only-content"],
        filenames=["only.fcs"],
        minimum_file_count=2,
    )

    assert result.is_compatible is False
    assert result.feedback == services.FeedbackState.danger(
        "Select at least 2 FCS files."
    )
    assert result.consistency_report == {}
