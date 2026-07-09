# -*- coding: utf-8 -*-

import io
import zipfile

from RosettaX.workflow.apply_calibration.io import append_files_to_zip_bytes
from RosettaX.workflow.apply_calibration.io import build_export_filename


class Test_ApplyCalibrationIO:
    def test_build_export_filename_uses_uploaded_stem_only(self) -> None:
        filename = build_export_filename(
            uploaded_fcs_path="/tmp/apogee_mystery_beads.fcs",
            output_channels=["Diameter [nm]"],
        )

        assert filename == "apogee_mystery_beads_RosettaX.fcs"

    def test_build_export_filename_ignores_output_channels(self) -> None:
        filename = build_export_filename(
            uploaded_fcs_path="/tmp/input-a.fcs",
            output_channels=["Diameter [nm]", "Estimated Coupling"],
        )

        assert filename == "input-a_RosettaX.fcs"

    def test_append_files_to_zip_bytes_preserves_existing_members_and_adds_report(self) -> None:
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
