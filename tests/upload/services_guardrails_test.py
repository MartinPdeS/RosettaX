# -*- coding: utf-8 -*-

import base64

import pytest

from RosettaX.workflow.upload.services import (
    decode_dash_upload_contents,
    parse_allowed_upload_extensions,
    save_uploaded_file,
)


class Test_UploadServiceGuardrails:
    def test_parse_allowed_upload_extensions_parses_csv_values(self) -> None:
        assert parse_allowed_upload_extensions(".fcs, .csv") == frozenset(
            {".fcs", ".csv"}
        )

    def test_save_uploaded_file_rejects_unsupported_extension(
        self,
        tmp_path,
    ) -> None:
        encoded_payload = base64.b64encode(b"hello").decode("ascii")

        with pytest.raises(ValueError, match="Unsupported uploaded file type"):
            save_uploaded_file(
                contents=f"data:text/plain;base64,{encoded_payload}",
                filename="sample.txt",
                upload_directory=tmp_path,
            )

    def test_decode_dash_upload_contents_rejects_oversized_payload(self) -> None:
        encoded_payload = base64.b64encode(b"123456").decode("ascii")

        with pytest.raises(ValueError, match="maximum supported size"):
            decode_dash_upload_contents(
                f"data:application/octet-stream;base64,{encoded_payload}",
                max_upload_bytes=3,
            )
