"""Exports remain downloadable when report generation or ZIP bundling fails."""

import io
import zipfile
from dataclasses import fields, replace

import pytest

from RosettaX.pages.p04_calibrate.sections.s04_apply import services
from RosettaX.pages.p04_calibrate.sections.s04_apply.models import (
    ApplyCalibrationControls,
)
from RosettaX.workflow.apply_calibration import ApplyCalibrationFilesResult


@pytest.fixture
def controls():
    return ApplyCalibrationControls(
        **{field.name: None for field in fields(ApplyCalibrationControls)}
    )


@pytest.fixture
def calibrated_result():
    return ApplyCalibrationFilesResult(
        payload_bytes=b"calibrated events",
        download_filename="calibrated.fcs",
        source_channel="SSC",
        output_channels=["Diameter"],
        file_count=1,
        warnings=[],
        status="Applied calibration.",
    )


@pytest.fixture
def report(monkeypatch):
    payload = {"report": "evidence"}
    monkeypatch.setattr(
        services.apply_report, "build_apply_report_payload", lambda **_: payload
    )
    monkeypatch.setattr(
        services.apply_report,
        "build_apply_report_download_filename",
        lambda **_: "report.pdf",
    )
    monkeypatch.setattr(
        services.apply_report, "build_apply_report_pdf_bytes", lambda **_: b"PDF"
    )
    return payload


def test_single_file_export_keeps_fcs_bytes_and_separate_report(
    controls, calibrated_result, report
):
    prepared = services.prepare_calibration_export(
        controls=controls, request=None, result=calibrated_result
    )
    assert prepared.payload_bytes == b"calibrated events"
    assert prepared.download_filename == "calibrated.fcs"
    assert prepared.status == "Applied calibration."
    assert prepared.report_payload == report


def test_multiple_file_export_bundles_report_pdf(controls, calibrated_result, report):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("calibrated.fcs", b"calibrated events")
    result = replace(
        calibrated_result,
        payload_bytes=buffer.getvalue(),
        download_filename="calibrated.zip",
        file_count=2,
    )
    prepared = services.prepare_calibration_export(
        controls=controls, request=None, result=result
    )
    with zipfile.ZipFile(io.BytesIO(prepared.payload_bytes)) as archive:
        assert archive.read("calibrated.fcs") == b"calibrated events"
        assert archive.read("report.pdf") == b"PDF"
    assert "Bundled report PDF" in prepared.status
    assert prepared.report_payload == report


@pytest.mark.parametrize(
    "failure_stage", ["build_apply_report_payload", "build_apply_report_pdf_bytes"]
)
def test_report_failure_preserves_calibrated_download(
    controls, calibrated_result, report, monkeypatch, failure_stage
):
    def fail(**_):
        raise ValueError("report unavailable")

    monkeypatch.setattr(services.apply_report, failure_stage, fail)
    prepared = services.prepare_calibration_export(
        controls=controls, request=None, result=calibrated_result
    )
    assert prepared.payload_bytes == calibrated_result.payload_bytes
    assert (
        prepared.status
        == "Applied calibration. Report generation failed: ValueError: report unavailable"
    )
    assert prepared.report_payload == (
        None if failure_stage == "build_apply_report_payload" else report
    )


def test_zip_failure_preserves_original_download_and_report(
    controls, calibrated_result, report
):
    result = replace(calibrated_result, download_filename="invalid.zip")
    prepared = services.prepare_calibration_export(
        controls=controls, request=None, result=result
    )
    assert prepared.payload_bytes == result.payload_bytes
    assert prepared.report_payload == report
    assert "ZIP bundling failed" in prepared.status


def test_invalid_request_clears_report_without_creating_download(controls, monkeypatch):
    monkeypatch.setattr(
        services.usage_metrics, "record_apply_button_click", lambda: None
    )
    result = services.apply_and_prepare_calibration_export(controls)
    assert (
        result.status
        == "Failed to apply and export calibration: ValueError: Upload at least one input FCS file first."
    )
    assert result.payload_bytes is None
    assert result.report_payload is None


def test_apply_orchestrator_passes_controls_and_prepares_result(
    controls, calibrated_result, report, monkeypatch
):
    recorded = []
    request = object()

    def build_request(**values):
        assert values["uploaded_fcs_path"] == "input.fcs"
        return request

    def apply_request(*, request):
        recorded.append(request)
        return calibrated_result

    monkeypatch.setattr(services, "build_apply_calibration_request", build_request)
    monkeypatch.setattr(
        services.apply_calibration, "apply_calibration_to_fcs_files", apply_request
    )
    monkeypatch.setattr(
        services.usage_metrics, "record_apply_button_click", lambda: None
    )
    monkeypatch.setattr(
        services.usage_metrics,
        "record_calibrated_files",
        lambda **values: recorded.append(values["file_count"]),
    )
    result = services.apply_and_prepare_calibration_export(
        replace(controls, uploaded_fcs_path="input.fcs")
    )
    assert recorded == [request, 1]
    assert result.payload_bytes == calibrated_result.payload_bytes
    assert result.report_payload == report
