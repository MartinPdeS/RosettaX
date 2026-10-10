"""Fixed real-FCS regression cases for peak detection, calibration, and application."""

import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pytest

from RosettaX.pages.p03_scattering.sections.s05_calibration.services import (
    run_scattering_calibration,
)
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.peak.scripts.rosetta_mix import (
    FluorescenceGuidedScatterPeakProcess,
)
from RosettaX.workflow.scattering import ScatteringCalibration
from RosettaX.workflow.scattering.application import apply_scattering_calibration
from RosettaX.workflow.scattering.backend import BackEnd

REPOSITORY = Path(__file__).resolve().parents[1]
CASE_DIRECTORY = Path(__file__).with_name("fixtures") / "scattering"
CASE_PATHS = sorted(CASE_DIRECTORY.glob("*.json"))
if not CASE_PATHS:
    raise pytest.UsageError(f"No real-FCS scattering cases found in {CASE_DIRECTORY}")


@pytest.fixture(scope="module", params=CASE_PATHS, ids=lambda path: path.stem)
def scattering_case(request):
    case = json.loads(request.param.read_text())
    fcs_path = REPOSITORY / case["fcs_file"]
    assert hashlib.sha256(fcs_path.read_bytes()).hexdigest() == case["sha256"], (
        f"{fcs_path.name} changed; review the input and recorded baseline together."
    )
    with FCSFile(fcs_path) as fcs:
        assert fcs.text["Keywords"]["$TOT"] == case["expected_event_count"]
        assert set(case["detector_channels"].values()) <= set(fcs.get_column_names())
        # Keep real event values for verifying application after the file is closed.
        measured_values = fcs.column_copy(
            case["detector_channels"]["scattering"],
            dtype=float,
            n=case["peak_detection"]["max_events_for_analysis"],
        )
    backend = BackEnd()
    backend.fcs_file_path = str(fcs_path)
    detection = FluorescenceGuidedScatterPeakProcess().run_automatic_action(
        backend=backend,
        detector_channels=case["detector_channels"],
        **case["peak_detection"],
    )
    assert detection is not None
    return case, fcs_path, measured_values, detection


def test_real_fcs_scattering_peaks_match_recorded_positions(scattering_case):
    case, _, _, detection = scattering_case
    expected = case["expected"]
    actual_peaks = np.asarray(detection.new_peak_positions, dtype=float)
    assert actual_peaks.shape == np.asarray(expected["raw_peak_positions"]).shape, (
        f"Unexpected number of calibration peaks: {actual_peaks.tolist()}\n{detection.status}"
    )
    assert np.all(np.isfinite(actual_peaks))
    assert np.all(np.diff(actual_peaks) > 0)
    np.testing.assert_allclose(
        actual_peaks,
        expected["raw_peak_positions"],
        rtol=expected["raw_peak_relative_tolerance"],
        atol=0,
        err_msg=f"Raw scattering peaks changed. Detection diagnostic:\n{detection.status}",
    )


@pytest.fixture(scope="module")
def calibrated_case(scattering_case):
    case, fcs_path, measured_values, detection = scattering_case
    # These are explicit trial assignments, never the algorithm's placeholder sizes.
    reference_rows = [
        {"particle_diameter_nm": diameter, "measured_peak_position": peak}
        for diameter, peak in zip(
            case["trial_standard_diameters_nm"],
            detection.new_peak_positions,
            strict=True,
        )
    ]
    result = run_scattering_calibration(
        uploaded_fcs_path=str(fcs_path),
        detector_column=case["detector_channels"]["scattering"],
        bead_table_data=reference_rows,
        logger=logging.getLogger(__name__),
        **case["calibration"],
    )
    assert result.calibration_store is not None, result.apply_status
    # Exercise the saved calibration boundary, rather than retaining a live fit.
    calibration = ScatteringCalibration.from_dict(
        json.loads(json.dumps(result.calibration_store))
    )
    return case, measured_values, detection, calibration


def test_real_fcs_scattering_calibration_matches_recorded_response(calibrated_case):
    case, _, _, calibration = calibrated_case
    expected = case["expected"]
    assert calibration.source_channel == case["detector_channels"]["scattering"]
    response = calibration.instrument_response
    assert response.r_squared >= expected["minimum_fit_r_squared"]
    assert response.intercept == 0.0
    np.testing.assert_allclose(
        response.slope,
        expected["instrument_response_slope"],
        rtol=expected["instrument_response_relative_tolerance"],
        atol=0,
        err_msg="The trial configuration's scattering response changed.",
    )


def test_real_fcs_calibrated_peak_positions_match_recorded_baseline(calibrated_case):
    case, measured_values, detection, calibration = calibrated_case
    expected = case["expected"]
    relation = calibration.calibration_standard_mie_relation
    assert relation.is_monotonic, (
        "The trial diameter range no longer supports inversion."
    )
    applied_peaks = apply_scattering_calibration(
        calibration=calibration,
        measured_values=np.asarray(detection.new_peak_positions),
        target_mie_relation=relation,
    )
    assert not applied_peaks.warnings, applied_peaks.warnings
    np.testing.assert_allclose(
        applied_peaks.estimated_coupling,
        expected["coupling_peak_positions"],
        rtol=expected["coupling_peak_relative_tolerance"],
        atol=0,
        err_msg="Calibrated coupling peak positions changed.",
    )
    np.testing.assert_allclose(
        applied_peaks.mie_equivalent_diameter_nm,
        expected["equivalent_diameter_peak_positions_nm"],
        rtol=0,
        atol=expected["equivalent_diameter_absolute_tolerance_nm"],
        err_msg="Trial Mie-equivalent diameter peak positions changed.",
    )
    # Apply the saved response to the FCS events, not only its calibration anchors.
    event_coupling = calibration.measured_to_coupling(measured_values)
    assert event_coupling.shape == measured_values.shape
    assert np.all(np.isfinite(event_coupling))
    # Histogram modes provide a second estimator on actual calibrated events.
    for histogram in expected["calibrated_event_histograms"]:
        lower, upper = histogram["coupling_range"]
        counts, bin_edges = np.histogram(
            event_coupling, bins=histogram["bin_count"], range=(lower, upper)
        )
        assert int(np.sum(counts)) >= histogram["minimum_population"]
        peak_bin = int(np.argmax(counts))
        measured_peak = (bin_edges[peak_bin] + bin_edges[peak_bin + 1]) / 2
        np.testing.assert_allclose(
            measured_peak,
            histogram["peak_position"],
            rtol=0,
            atol=(upper - lower) / histogram["bin_count"],
            err_msg="The calibrated FCS event histogram mode changed by more than one bin.",
        )
