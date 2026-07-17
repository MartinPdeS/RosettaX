# -*- coding: utf-8 -*-

from io import BytesIO

import pytest

from RosettaX.utils.streamed_uploads import (
    build_streamed_upload_error_token,
    resolve_streamed_upload,
    stage_streamed_upload,
)


def test_streamed_upload_round_trip_uses_an_opaque_token(tmp_path) -> None:
    upload = stage_streamed_upload(
        stream=BytesIO(b"FCS payload"),
        filename="../sample file.fcs",
        content_length=11,
        staging_directory=tmp_path,
        max_upload_bytes=100,
    )

    assert upload.token.startswith("rosettax-upload://")
    assert "sample" not in upload.token
    assert upload.filename == "sample_file.fcs"
    assert upload.size_bytes == 11
    assert upload.file_path.read_bytes() == b"FCS payload"

    resolved = resolve_streamed_upload(
        upload.token,
        staging_directory=tmp_path,
        max_upload_bytes=100,
    )
    assert resolved == upload


def test_streamed_upload_rejects_oversized_content_and_removes_partial_file(
    tmp_path,
) -> None:
    with pytest.raises(ValueError, match="maximum supported size"):
        stage_streamed_upload(
            stream=BytesIO(b"too large"),
            filename="sample.fcs",
            staging_directory=tmp_path,
            max_upload_bytes=3,
        )

    assert list(tmp_path.iterdir()) == []


def test_streamed_upload_rejects_unsupported_extensions(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unsupported uploaded file type"):
        stage_streamed_upload(
            stream=BytesIO(b"payload"),
            filename="sample.txt",
            staging_directory=tmp_path,
        )


def test_streamed_upload_propagates_browser_bridge_errors(tmp_path) -> None:
    with pytest.raises(ValueError, match="connection failed"):
        resolve_streamed_upload(
            build_streamed_upload_error_token("connection failed"),
            staging_directory=tmp_path,
        )
