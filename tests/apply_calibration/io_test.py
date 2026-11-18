"""Regression tests for apply calibration io."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import io
import zipfile
from RosettaX.workflow.apply_calibration import io as calibration_io
from RosettaX.workflow.apply_calibration.io import (
    append_files_to_zip_bytes,
    build_export_filename,
)


class Test_ApplyCalibrationIO:
    """Regression checks for apply calibration io."""

    def test_build_export_filename_uses_uploaded_stem_only(self) -> None:
        """Check build export filename uses uploaded stem only."""
        filename = build_export_filename(
            uploaded_fcs_path="/tmp/apogee_mystery_beads.fcs",
            output_channels=["Diameter [nm]"],
        )

        assert filename == "apogee_mystery_beads_RosettaX.fcs"

    def test_build_export_filename_ignores_output_channels(self) -> None:
        """Check build export filename ignores output channels."""
        filename = build_export_filename(
            uploaded_fcs_path="/tmp/input-a.fcs",
            output_channels=["Diameter [nm]", "Estimated Coupling"],
        )

        assert filename == "input-a_RosettaX.fcs"

    def test_export_zip_preserves_files_with_the_same_basename(self, monkeypatch) -> None:
        """Give same-named inputs distinct archive entries with their own bytes."""
        first = "first/sample.fcs"
        second = "second/sample.fcs"
        monkeypatch.setattr(
            calibration_io,
            "build_exported_fcs_bytes",
            lambda **kwargs: kwargs["uploaded_fcs_path"].encode(),
        )

        zip_bytes = calibration_io.build_zip_of_exported_fcs_files(
            uploaded_fcs_paths=[first, second],
            input_export_columns=[],
            output_channels=[],
            dataframe_transformer_factory=lambda _path: lambda dataframe: dataframe,
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            assert archive.namelist() == ["sample_RosettaX.fcs", "sample_RosettaX_2.fcs"]
            assert [archive.read(name) for name in archive.namelist()] == [
                first.encode(), second.encode(),
            ]

    def test_append_files_to_zip_bytes_preserves_existing_members_and_adds_report(self) -> None:
        """Check append files to ZIP bytes preserves existing members and adds report."""
        source_buffer = io.BytesIO()

        with zipfile.ZipFile(source_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("input-a_calibrated.fcs", b"fcs-a")
            zip_file.writestr("input-b_calibrated.fcs", b"fcs-b")

        bundled_zip = append_files_to_zip_bytes(
            zip_bytes=source_buffer.getvalue(),
            extra_files={
                "rosettax_apply_report.pdf": b"pdf-bytes",
            },
        )

        with zipfile.ZipFile(io.BytesIO(bundled_zip), mode="r") as zip_file:
            assert sorted(zip_file.namelist()) == [
                "input-a_calibrated.fcs",
                "input-b_calibrated.fcs",
                "rosettax_apply_report.pdf",
            ]
            assert zip_file.read("input-a_calibrated.fcs") == b"fcs-a"
            assert zip_file.read("input-b_calibrated.fcs") == b"fcs-b"
            assert zip_file.read("rosettax_apply_report.pdf") == b"pdf-bytes"
