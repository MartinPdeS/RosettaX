from RosettaX.workflow.apply_calibration.report import (
    _build_chart_spec,
    apply_report_matches_request,
    build_apply_report_payload,
    build_apply_report_pdf_bytes,
)
from RosettaX.workflow.apply_calibration.report_helpers import build_fit_evidence_items
from RosettaX.workflow.apply_calibration.services import (
    ApplyCalibrationFilesResult,
    ApplyCalibrationRequest,
    CalibrationApplication,
)


def make_report():
    request = ApplyCalibrationRequest(
        uploaded_fcs_paths=["sample.fcs"],
        export_columns=[],
        calibrations=[CalibrationApplication(
            selected_calibration="ssc.json",
            calibration_payload={
                "calibration_type": "scattering",
                "source_channel": "SSC-A",
                "instrument_response": {"slope": 2.0, "intercept": 1.0, "r_squared": 0.99},
                "reference_table": [
                    {"measured_peak_position": 10, "expected_coupling": 20, "particle_diameter_nm": 100},
                    {"measured_peak_position": 20, "expected_coupling": 42, "particle_diameter_nm": 200},
                ],
            },
        )],
    )
    result = ApplyCalibrationFilesResult(
        payload_bytes=b"", download_filename="sample.zip", source_channel="SSC-A",
        output_channels=["diameter_nm"], file_count=1,
        warnings=["Values outside the target range were excluded."], status="Completed.",
    )
    return request, build_apply_report_payload(request=request, result=result)


def test_report_becomes_stale_when_calibration_coefficients_change():
    request, report = make_report()
    request.calibrations[0].calibration_payload["instrument_response"]["slope"] = 3.0
    assert not apply_report_matches_request(report_payload=report, request=request)


def test_scattering_chart_shows_fitted_coupling_instead_of_connected_diameters():
    _, report = make_report()
    chart = _build_chart_spec(report_payload=report)
    assert chart["y_values"] == [20.0, 42.0]
    assert chart["line_y_values"] == [21.0, 41.0]
    assert chart["y_label"] == "Expected coupling"


def test_scattering_chart_without_coupling_does_not_invent_a_fit():
    _, report = make_report()
    for row in report["calibration_details_list"][0]["reference_table"]:
        row.pop("expected_coupling")
    chart = _build_chart_spec(report_payload=report)
    assert chart["y_values"] == [100.0, 200.0]
    assert chart["line_y_values"] == []


def test_fit_evidence_ignores_nonfinite_and_missing_measurements():
    items = dict(build_fit_evidence_items(details={
        "calibration_type": "fluorescence",
        "reference_points": [{"measured_value": 10}, {"measured_value": float("nan")}, {}],
        "fit_metrics": {},
    }))
    assert items["Recorded reference peaks"] == "1"
    assert items["Measured reference range"] == "10 to 10 a.u."
    assert items["Saved R-squared"] == "n/a"


def test_report_places_warnings_before_run_details_and_shows_fit_evidence():
    _, report = make_report()
    pdf = build_apply_report_pdf_bytes(report_payload=report)
    assert pdf.index(b"Values outside the target") < pdf.index(b"Run summary")
    assert b"Calibration evidence" in pdf
    assert b"does not establish calibration" in pdf
