from RosettaX.workflow.file_selection import UploadedFile, UploadedFileBatch
from RosettaX.workflow.file_selection.services import (
    build_channel_options,
    build_file_options,
    resolve_selected_channel,
    resolve_selected_file,
)


def test_uploaded_file_batch_round_trips_serialized_state() -> None:
    batch = UploadedFileBatch(
        files=(
            UploadedFile(
                path="/tmp/first.fcs",
                filename="first.fcs",
                column_names=("FSC-A", "SSC-A"),
                number_of_events=12,
            ),
        ),
        reference_column_names=("FSC-A", "SSC-A"),
    )

    restored = UploadedFileBatch.from_dict(batch.to_dict())

    assert restored == batch


def test_file_selection_builds_options_and_preserves_valid_selection() -> None:
    batch = UploadedFileBatch(
        files=(
            UploadedFile(path="/tmp/first.fcs", filename="first.fcs"),
            UploadedFile(path="/tmp/second.fcs", filename="second.fcs"),
        )
    )

    assert build_file_options(batch.to_dict()) == [
        {"label": "first.fcs", "value": "/tmp/first.fcs"},
        {"label": "second.fcs", "value": "/tmp/second.fcs"},
    ]
    assert resolve_selected_file(batch.to_dict(), current_path="/tmp/second.fcs") == batch.files[1]
    assert resolve_selected_file(batch.to_dict(), current_path="/tmp/missing.fcs") == batch.files[0]


def test_uploaded_file_batch_accepts_legacy_visualization_keys() -> None:
    batch = UploadedFileBatch.from_dict(
        {
            "files": [
                {
                    "uploaded_fcs_path": "/tmp/legacy.fcs",
                    "uploaded_filename": "legacy.fcs",
                }
            ],
            "available_channels": ["FL1-A"],
        }
    )

    assert batch.files[0].path == "/tmp/legacy.fcs"
    assert batch.files[0].filename == "legacy.fcs"
    assert batch.reference_column_names == ("FL1-A",)


def test_file_selection_accepts_legacy_path_lists_and_channel_defaults() -> None:
    assert build_file_options(["/tmp/one.fcs", "/tmp/two.fcs"]) == [
        {"label": "one.fcs", "value": "/tmp/one.fcs"},
        {"label": "two.fcs", "value": "/tmp/two.fcs"},
    ]
    assert build_channel_options(["FSC-A", "", "SSC-A"]) == [
        {"label": "FSC-A", "value": "FSC-A"},
        {"label": "SSC-A", "value": "SSC-A"},
    ]
    assert resolve_selected_channel(["FSC-A", "SSC-A"], fallback_index=1) == "SSC-A"
