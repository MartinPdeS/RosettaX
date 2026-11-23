"""Check Rosetta's detector output and the historical global fit on real FCS files."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import hashlib
import json
import numpy as np
import pytest
from pathlib import Path
from RosettaX.utils.reader import FCSFile
from RosettaX.workflow.peak import registry
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture import (
    MixtureRosettaScatterPeakProcess,
)
from RosettaX.workflow.scattering.backend import BackEnd

REPOSITORY = Path(__file__).resolve().parents[1]
CASE_DIRECTORY = Path(__file__).with_name("fixtures") / "rosetta"
CASE_PATHS = sorted(CASE_DIRECTORY.glob("*.json"))
if not CASE_PATHS:
    raise pytest.UsageError(f"No Rosetta script cases found in {CASE_DIRECTORY}")
CASES = [(path.stem, json.loads(path.read_text())) for path in CASE_PATHS]
RUNS = [
    pytest.param((case, run), id=f"{name}-{run['process_name']}")
    for name, case in CASES for run in case["runs"]
]


def run_on_fixture(*, case, run, process):
    """Use the checksum-pinned FCS data and saved detector settings."""
    path = REPOSITORY / case["fcs_file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"], (
        "FCS input changed; review the fixture and its baseline together."
    )
    with FCSFile(path) as fcs:
        assert fcs.text["Keywords"]["$TOT"] == case["expected_event_count"]
        assert set(case["detector_channels"].values()) <= set(fcs.get_column_names())
    backend = BackEnd()
    backend.fcs_file_path = str(path)
    result = process.run_automatic_action(
        backend=backend,
        detector_channels=case["detector_channels"],
        peak_count=case["peak_count"],
        max_events_for_analysis=case["max_events_for_analysis"],
        process_settings=run["process_settings"],
    )
    assert result is not None
    return result


@pytest.fixture(scope="module", params=RUNS)
def script_run(request):
    """Run a registered mode with real readers, fitting, and recorded settings."""
    case, run = request.param
    process = registry.get_process_instance(process_name=run["process_name"])
    assert process is not None, f"Registered script missing: {run['process_name']}"
    return case, run, run_on_fixture(case=case, run=run, process=process)


def format_stage_trace(*, result):
    """Show Rosetta's fit and sizing decisions alongside a baseline failure."""
    payload = result.peak_lines_payload
    diagnostics = payload.get("rosetta_debug_diagnostics", {})
    trace = {
        "event_counts": payload.get("rosetta_event_counts"),
        "baseline_gate": payload.get("baseline_cutoff"),
        "fluorescence": diagnostics.get("fluorescence_peaks"),
        "marker_scatter": diagnostics.get("marker_scatter_fits"),
        "scatter_fit_method": diagnostics.get("scatter_fit_method"),
        "scatter_candidates": diagnostics.get("scatter_peaks"),
        "sizing": payload.get("rosetta_sizing"),
        "lowest_peak_exclusion": payload.get("rosetta_lowest_peak_exclusion"),
        "status": result.status,
    }
    return json.dumps(trace, indent=2)


def test_script_outcome_and_table_match_baseline(script_run):
    """Keep successful sizes and peak counts, and meaningful failures, unchanged."""
    case, expected, result = script_run
    assert result.warning == expected["warning"], format_stage_trace(result=result)
    if expected["status_contains"]:
        assert expected["status_contains"] in result.status
    else:
        assert not result.status
    rows = result.table_prefill_rows or []
    assert len(rows) == len(expected["rows"]), format_stage_trace(result=result)
    if not rows:
        assert not result.new_peak_positions
        assert not result.peak_positions
        return
    np.testing.assert_allclose(
        [row["measured_peak_position"] for row in rows],
        [row["measured_peak_position"] for row in expected["rows"]],
        rtol=case["position_relative_tolerance"], atol=0, err_msg=format_stage_trace(result=result),
    )
    assert [row["particle_diameter_nm"] for row in rows] == [
        row["particle_diameter_nm"] for row in expected["rows"]
    ]
    positions = np.asarray(result.new_peak_positions, dtype=float)
    assert np.all(np.isfinite(positions)) and np.all(positions > 0)
    assert np.all(np.diff(positions) > 0)
    np.testing.assert_allclose(positions, [row["measured_peak_position"] for row in rows])
    if "expected_sizing" in expected:
        payload = result.peak_lines_payload
        sizing = payload["rosetta_sizing"]
        assert sizing["state"] == expected["expected_sizing"]["state"]
        assert sizing["needs_confirmation"] == expected["expected_sizing"]["needs_confirmation"]
        assert sizing["assigned_row_count"] == sum(bool(row["particle_diameter_nm"]) for row in rows)
        assert "rosetta_lowest_peak_exclusion" not in payload


def test_script_graph_markers_and_labels_match_baseline(script_run):
    """Keep fluorescence anchors, plot labels, and failure cleanup consistent."""
    case, expected, result = script_run
    payload = result.peak_lines_payload or {}
    baseline = expected["payload"]
    if expected["warning"] and not expected["rows"]:
        assert not payload.get("scatter_guide_annotations")
        if not baseline.get("points"):
            assert not payload.get("points")
            return
    assert payload["labels"] == baseline["labels"], format_stage_trace(result=result)
    assert [point["kind"] for point in payload["points"]] == [
        point["kind"] for point in baseline["points"]
    ]
    np.testing.assert_allclose(
        [[point["x"], point["y"]] for point in payload["points"]],
        [[point["x"], point["y"]] for point in baseline["points"]],
        rtol=case["position_relative_tolerance"], atol=0, err_msg=format_stage_trace(result=result),
    )
    np.testing.assert_allclose(payload["baseline_cutoff"], baseline["baseline_cutoff"], rtol=0.01)
    assert [item["label"] for item in payload.get("scatter_guide_annotations", [])] == [
        item["label"] for item in baseline.get("scatter_guide_annotations", [])
    ]


class GlobalMixtureControl(MixtureRosettaScatterPeakProcess):
    """Fit the baseline-gated scatter globally for the historical comparison."""

    def fit_marker_bounded_scatter(self, *, values, peak_count, marker_diagnostics, fluorescence_saturation, **fit_options):
        """Use the same scatter solver over the full gated population."""
        return self.scatter_fit_function(values=values, peak_count=peak_count, **fit_options)


@pytest.mark.parametrize("case,run", [
    pytest.param(case, run, id=name)
    for name, case in CASES for run in case["runs"]
    if "historical_global_scatter_positions" in run
])
def test_global_mixture_control_matches_historical_scatter_centers(case, run):
    """Recover the archived full-range fit with the same gates and FCS events."""
    result = run_on_fixture(case=case, run=run, process=GlobalMixtureControl())
    payload = result.peak_lines_payload
    assert payload["rosetta_debug_diagnostics"]["scatter_fit_method"] == "log_gaussian_mixture"
    np.testing.assert_allclose(
        [point["x"] for point in payload["points"] if point["kind"] == "non_fluorescent"],
        run["historical_global_scatter_positions"],
        rtol=case["position_relative_tolerance"],
        atol=0,
        err_msg=format_stage_trace(result=result),
    )
