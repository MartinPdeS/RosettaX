# -*- coding: utf-8 -*-

import sys
import types


class _DashBootstrapComponentsSentinel:
    def __call__(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    def __getattr__(self, name):
        return _DashBootstrapComponentsSentinel()


class _PyMieSimStub(types.ModuleType):
    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    ureg = types.SimpleNamespace()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)
sys.modules.setdefault(
    "PyMieSim",
    _PyMieSimStub("PyMieSim"),
)
sys.modules.setdefault(
    "PyMieSim.units",
    _PyMieSimUnitsStub("PyMieSim.units"),
)

from RosettaX.workflow.apply_calibration.report import (
    apply_report_matches_request,
    build_apply_report_download_filename,
    build_apply_report_payload,
    build_apply_report_pdf_bytes,
)
from RosettaX.workflow.apply_calibration.services import (
    ApplyCalibrationFilesResult,
    ApplyCalibrationRequest,
)
from RosettaX.workflow.apply_calibration.scattering.models import (
    ScatteringTargetModelParameters,
)


class Test_ApplyCalibrationReport:
    def test_build_apply_report_payload_serializes_request_result_and_summary(self) -> None:
        request = ApplyCalibrationRequest(
            uploaded_fcs_paths=[
                "/tmp/input-a.fcs",
                "/tmp/input-b.fcs",
            ],
            selected_calibration="scatter-calibration.json",
            calibration_payload={
                "calibration_type": "scattering",
                "source_channel": "SSC-A",
                "output_quantity": "particle_diameter_nm",
                "instrument_response": {
                    "measured_channel": "SSC-A",
                    "slope": 1.23,
                    "intercept": 4.56,
                    "r_squared": 0.998,
                    "force_zero_intercept": False,
                    "input_quantity": "measured_peak_position",
                    "output_quantity": "particle_diameter_nm",
                    "model_name": "Linear",
                },
                "reference_table": [
                    {
                        "measured_peak_position": 1200.0,
                        "particle_diameter_nm": 180.0,
                    },
                    {
                        "measured_peak_position": 2100.0,
                        "particle_diameter_nm": 240.0,
                    },
                ],
                "metadata": {
                    "detector_configuration_preset_name": "Side scatter preset",
                    "wavelength_nm": 488,
                    "notes": "Silica standards",
                },
            },
            export_columns=[
                "FSC-A",
                "Time",
            ],
            scattering_target_model_parameters=ScatteringTargetModelParameters.from_raw_values(
                target_mie_model="Solid Sphere",
                target_medium_refractive_index=1.335,
                target_particle_refractive_index=1.59,
                target_diameter_min_nm=100,
                target_diameter_max_nm=500,
                target_diameter_count=41,
            ),
        )

        result = ApplyCalibrationFilesResult(
            payload_bytes=b"zip-bytes",
            download_filename="scattering_calibrated_2_files.zip",
            source_channel="SSC-A",
            output_channels=[
                "SSC-A",
                "particle_diameter_nm",
            ],
            file_count=2,
            warnings=[
                "Monotonic branch fallback used.",
            ],
            status="Applied scattering calibration to 2 files.",
        )

        calibration_summary = {
            "file_name": "scatter-calibration.json",
            "file_path": "/tmp/scatter-calibration.json",
            "calibration_type": "scattering",
            "source_channel": "SSC-A",
            "output_quantity": "particle_diameter_nm",
            "version": 2,
            "requires_target_model": True,
        }

        payload = build_apply_report_payload(
            request=request,
            result=result,
            calibration_summary=calibration_summary,
        )

        assert payload["selected_calibration"] == "scatter-calibration.json"
        assert payload["uploaded_fcs_paths"] == [
            "/tmp/input-a.fcs",
            "/tmp/input-b.fcs",
        ]
        assert payload["export_columns"] == [
            "FSC-A",
            "Time",
        ]
        assert payload["calibration_summary"]["calibration_type"] == "scattering"
        assert payload["scattering_target_model_parameters"]["mie_model"] == "Solid Sphere"
        assert payload["result"]["download_filename"] == "scattering_calibrated_2_files.zip"
        assert payload["result"]["warnings"] == [
            "Monotonic branch fallback used.",
        ]
        assert payload["result"]["includes_embedded_report"] is True
        assert payload["request_signature"]["uploaded_fcs_paths"] == [
            "/tmp/input-a.fcs",
            "/tmp/input-b.fcs",
        ]
        assert payload["calibration_details"]["calibration_type"] == "scattering"
        assert payload["calibration_details"]["instrument_response"]["slope"] == 1.23
        assert payload["calibration_details"]["reference_table"][0]["particle_diameter_nm"] == 180.0
        assert payload["saved_calibration_payload"]["metadata"]["detector_configuration_preset_name"] == "Side scatter preset"
        assert payload["saved_calibration_payload"]["instrument_response"]["model_name"] == "Linear"

    def test_apply_report_matches_request_detects_request_changes(self) -> None:
        request = ApplyCalibrationRequest(
            uploaded_fcs_paths=["/tmp/input-a.fcs"],
            selected_calibration="fluorescence-calibration.json",
            calibration_payload={
                "source_channel": "FITC-A",
            },
            export_columns=["Time"],
        )

        result = ApplyCalibrationFilesResult(
            payload_bytes=b"fcs-bytes",
            download_filename="input-a_calibrated.fcs",
            source_channel="FITC-A",
            output_channels=["FITC-A"],
            file_count=1,
            warnings=[],
            status="Applied fluorescence calibration to 1 file.",
        )

        payload = build_apply_report_payload(
            request=request,
            result=result,
            calibration_summary={
                "file_name": "fluorescence-calibration.json",
                "calibration_type": "fluorescence",
            },
        )

        changed_request = ApplyCalibrationRequest(
            uploaded_fcs_paths=["/tmp/input-a.fcs"],
            selected_calibration="fluorescence-calibration.json",
            calibration_payload={
                "source_channel": "FITC-A",
            },
            export_columns=["Time", "FSC-A"],
        )

        assert apply_report_matches_request(
            report_payload=payload,
            request=request,
        ) is True
        assert apply_report_matches_request(
            report_payload=payload,
            request=changed_request,
        ) is False

    def test_build_apply_report_pdf_bytes_returns_pdf_with_expected_text(self) -> None:
        request = ApplyCalibrationRequest(
            uploaded_fcs_paths=["/tmp/input-a.fcs"],
            selected_calibration="fluorescence-calibration.json",
            calibration_payload={
                "schema_version": "1.0",
                "calibration_type": "fluorescence",
                "name": "FITC MESF calibration",
                "created_at": "2026-06-09T15:30:00Z",
                "source_file": "beads.fcs",
                "source_channel": "FITC-A",
                "gating_channel": "SSC-A",
                "gating_threshold": 1200.0,
                "fit_model": "power-law",
                "fit_metrics": {
                    "r_squared": 0.999,
                    "point_count": 3,
                },
                "parameters": {
                    "slope": 0.98,
                    "intercept": 0.12,
                    "prefactor": 1.32,
                },
                "export_notes": "Generated from MESF bead batch 24A.",
                "payload": {
                    "slope": 0.98,
                    "intercept": 0.12,
                    "prefactor": 1.32,
                    "R_squared": 0.999,
                    "model": "power-law",
                    "x_definition": "Intensity [a.u.]",
                    "y_definition": "Intensity [MESF]",
                },
                "reference_points": [
                    {
                        "reference_value": 1.0e3,
                        "measured_value": 9.0e2,
                    },
                    {
                        "reference_value": 1.0e4,
                        "measured_value": 8.4e3,
                    },
                    {
                        "reference_value": 1.0e5,
                        "measured_value": 7.6e4,
                    },
                ],
            },
            export_columns=[],
        )

        result = ApplyCalibrationFilesResult(
            payload_bytes=b"fcs-bytes",
            download_filename="input-a_calibrated.fcs",
            source_channel="FITC-A",
            output_channels=["FITC-A"],
            file_count=1,
            warnings=[],
            status="Applied fluorescence calibration to 1 file.",
        )

        payload = build_apply_report_payload(
            request=request,
            result=result,
            calibration_summary={
                "file_name": "fluorescence-calibration.json",
                "calibration_type": "fluorescence",
                "source_channel": "FITC-A",
            },
        )

        pdf_bytes = build_apply_report_pdf_bytes(
            report_payload=payload,
        )
        pdf_filename = build_apply_report_download_filename(
            report_payload=payload,
        )

        assert pdf_bytes.startswith(b"%PDF-1.4")
        assert b"RosettaX Apply Calibration Report" in pdf_bytes
        assert b"fluorescence-calibration.json" in pdf_bytes
        assert b"Applied fluorescence calibration to 1 file." in pdf_bytes
        assert b"MESF and peak positions" in pdf_bytes
        assert b"Measured peak position" in pdf_bytes
        assert b"Saved calibration JSON" in pdf_bytes
        assert b"Generated from MESF bead batch 24A." in pdf_bytes
        assert b"Intensity [MESF]" in pdf_bytes
        assert pdf_filename.startswith("rosettax_apply_report_fluorescence-calibration_")
        assert pdf_filename.endswith(".pdf")

    def test_build_apply_report_pdf_bytes_includes_saved_scattering_metadata(self) -> None:
        request = ApplyCalibrationRequest(
            uploaded_fcs_paths=["/tmp/input-a.fcs"],
            selected_calibration="scatter-calibration.json",
            calibration_payload={
                "calibration_type": "scattering",
                "version": 2,
                "source_channel": "SSC-A",
                "output_quantity": "particle_diameter_nm",
                "instrument_response": {
                    "measured_channel": "SSC-A",
                    "slope": 1.23,
                    "intercept": 4.56,
                    "r_squared": 0.998,
                    "force_zero_intercept": False,
                    "input_quantity": "measured_peak_position",
                    "output_quantity": "particle_diameter_nm",
                    "model_name": "Linear",
                },
                "metadata": {
                    "detector_configuration_preset_name": "Small particle SSC",
                    "wavelength_nm": 488,
                    "notes": "Lot 42",
                },
                "reference_table": [
                    {
                        "measured_peak_position": 1200.0,
                        "particle_diameter_nm": 180.0,
                    },
                    {
                        "measured_peak_position": 2100.0,
                        "particle_diameter_nm": 240.0,
                    },
                ],
            },
            export_columns=["Time"],
        )

        result = ApplyCalibrationFilesResult(
            payload_bytes=b"zip-bytes",
            download_filename="scattering_calibrated_1_file.zip",
            source_channel="SSC-A",
            output_channels=["SSC-A", "particle_diameter_nm"],
            file_count=1,
            warnings=[],
            status="Applied scattering calibration to 1 file.",
        )

        payload = build_apply_report_payload(
            request=request,
            result=result,
            calibration_summary={
                "file_name": "scatter-calibration.json",
                "calibration_type": "scattering",
                "source_channel": "SSC-A",
                "output_quantity": "particle_diameter_nm",
            },
        )

        pdf_bytes = build_apply_report_pdf_bytes(report_payload=payload)

        assert b"Saved calibration JSON: Metadata" in pdf_bytes
        assert b"Small particle SSC" in pdf_bytes
        assert b"Lot 42" in pdf_bytes