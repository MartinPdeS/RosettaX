"""Regression tests for upload services guardrails."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import base64
import pytest
from pathlib import Path
from RosettaX.workflow.upload.services import (
    decode_dash_upload_contents,
    parse_allowed_upload_extensions,
    save_uploaded_file,
)


class Test_UploadServiceGuardrails:
    """Regression checks for upload service guardrails."""

    def test_parse_allowed_upload_extensions_parses_csv_values(self) -> None:
        """Check parse allowed upload extensions parses csv values."""
        assert parse_allowed_upload_extensions(".fcs, .csv") == frozenset(
            {".fcs", ".csv"}
        )

    def test_save_uploaded_file_rejects_unsupported_extension(
        self,
        tmp_path,
    ) -> None:
        """Check save uploaded file rejects unsupported extension."""
        encoded_payload = base64.b64encode(b"hello").decode("ascii")

        with pytest.raises(ValueError, match="Unsupported uploaded file type"):
            save_uploaded_file(
                contents=f"data:text/plain;base64,{encoded_payload}",
                filename="sample.txt",
                upload_directory=tmp_path,
            )

    def test_decode_dash_upload_contents_rejects_oversized_payload(self) -> None:
        """Check decode Dash upload contents rejects oversized payload."""
        encoded_payload = base64.b64encode(b"123456").decode("ascii")

        with pytest.raises(ValueError, match="maximum supported size"):
            decode_dash_upload_contents(
                f"data:application/octet-stream;base64,{encoded_payload}",
                max_upload_bytes=3,
            )

    def test_decode_dash_upload_contents_checks_padding_at_size_limit(self) -> None:
        """Check the decoded size when payloads have the same encoded length."""
        assert decode_dash_upload_contents("data:;base64,YQ==", max_upload_bytes=1) == b"a"
        with pytest.raises(ValueError, match="maximum supported size"):
            decode_dash_upload_contents("data:;base64,YWI=", max_upload_bytes=1)

    def test_legacy_uploads_with_same_name_keep_independent_contents(self, tmp_path: Path) -> None:
        """Keep a previously returned path valid when its filename is reused."""
        first = save_uploaded_file(
            contents="data:;base64,YQ==", filename="sample.fcs", upload_directory=tmp_path
        )
        second = save_uploaded_file(
            contents="data:;base64,Yg==", filename="sample.fcs", upload_directory=tmp_path
        )

        assert first != second
        assert first.name == second.name == "sample.fcs"
        assert first.read_bytes() == b"a"
        assert second.read_bytes() == b"b"
