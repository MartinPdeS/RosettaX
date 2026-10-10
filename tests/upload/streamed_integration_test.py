"""Regression tests for upload streamed integration."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import json
from io import BytesIO

from RosettaX.pages.p04_calibrate.sections.s02_calibration_picker import (
    services as calibration_picker_services,
)
from RosettaX.pages.p04_calibrate.sections.s03_file_picker import (
    services as file_picker_services,
)
from RosettaX.utils.streamed_uploads import (
    resolve_streamed_upload,
    stage_streamed_upload,
)
from RosettaX.workflow.upload import services as upload_services


def _resolve_from_directory(staging_directory):
    """Resolve a streamed-upload token within the test directory."""
    def resolve(token, *, max_upload_bytes=None):
        """Resolve for this test."""
        return resolve_streamed_upload(
            token,
            staging_directory=staging_directory,
            max_upload_bytes=max_upload_bytes,
        )

    return resolve


def test_shared_fcs_service_uses_staged_path_without_decoding_or_copying(
    tmp_path,
    monkeypatch,
) -> None:
    """Check shared FCS service uses staged path without decoding or copying."""
    staged = stage_streamed_upload(
        stream=BytesIO(b"FCS3.0 payload"),
        filename="sample.fcs",
        staging_directory=tmp_path / "staged",
    )
    monkeypatch.setattr(
        upload_services,
        "resolve_streamed_upload",
        _resolve_from_directory(tmp_path / "staged"),
    )

    result = upload_services.save_uploaded_file(
        contents=staged.token,
        filename="sample.fcs",
        upload_directory=tmp_path / "legacy-destination",
    )

    assert result == staged.file_path
    assert result.read_bytes() == b"FCS3.0 payload"
    assert not (tmp_path / "legacy-destination").exists()


def test_calibration_json_parser_reads_streamed_token(
    tmp_path,
    monkeypatch,
) -> None:
    """Check calibration JSON parser reads streamed token."""
    record = {
        "schema": "rosettax_calibration_v1",
        "payload": {
            "calibration_type": "fluorescence",
            "source_channel": "FITC-A",
        },
    }
    staged = stage_streamed_upload(
        stream=BytesIO(json.dumps(record).encode("utf-8")),
        filename="calibration.json",
        staging_directory=tmp_path / "staged",
    )
    monkeypatch.setattr(
        upload_services,
        "resolve_streamed_upload",
        _resolve_from_directory(tmp_path / "staged"),
    )

    filename, payload = calibration_picker_services.parse_uploaded_calibration(
        contents=staged.token,
        filename="calibration.json",
    )

    assert filename == "calibration.json"
    assert payload["source_channel"] == "FITC-A"


def test_apply_file_picker_accepts_streamed_fcs_token(
    tmp_path,
    monkeypatch,
) -> None:
    """Check apply file picker accepts streamed FCS token."""
    staged = stage_streamed_upload(
        stream=BytesIO(b"FCS3.0 payload"),
        filename="sample.fcs",
        staging_directory=tmp_path / "staged",
    )
    monkeypatch.setattr(
        file_picker_services,
        "resolve_streamed_upload",
        _resolve_from_directory(tmp_path / "staged"),
    )

    result = file_picker_services.save_single_uploaded_file(
        upload_directory=tmp_path / "legacy-destination",
        contents=staged.token,
        filename="sample.fcs",
    )

    assert result == staged.file_path
    assert not (tmp_path / "legacy-destination").exists()
