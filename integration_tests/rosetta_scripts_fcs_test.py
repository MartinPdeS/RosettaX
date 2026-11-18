"""Preserve every Rosetta mode's current behavior on two fixed real FCS files."""

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


@pytest.fixture(scope="module", params=RUNS)
def script_run(request):
    """Run a registered mode with real readers, fitting, and recorded settings."""
    case, run = request.param
    path = REPOSITORY / case["fcs_file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"], (
        "FCS input changed; review the fixture and its baseline together."
    )
    with FCSFile(path) as fcs:
        assert fcs.text["Keywords"]["$TOT"] == case["expected_event_count"]
        assert set(case["detector_channels"].values()) <= set(fcs.get_column_names())
    process = registry.get_process_instance(process_name=run["process_name"])
    assert process is not None, f"Registered script missing: {run['process_name']}"
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
    return case, run, result


def test_script_outcome_and_table_match_baseline(script_run):
    """Keep successful sizes and peak counts, and meaningful failures, unchanged."""
    case, expected, result = script_run
    assert result.warning == expected["warning"], result.status
    if expected["warning"]:
        assert expected["status_contains"] in result.status
        assert not result.table_prefill_rows
        assert not result.new_peak_positions
        assert not result.peak_positions
        return
    if expected["status_contains"]:
        assert expected["status_contains"] in result.status
    else:
        assert not result.status
    rows = result.table_prefill_rows
    assert len(rows) == len(expected["rows"])
    np.testing.assert_allclose(
        [row["measured_peak_position"] for row in rows],
        [row["measured_peak_position"] for row in expected["rows"]],
        rtol=case["position_relative_tolerance"], atol=0,
    )
    assert [row["particle_diameter_nm"] for row in rows] == [
        row["particle_diameter_nm"] for row in expected["rows"]
    ]
    positions = np.asarray(result.new_peak_positions, dtype=float)
    assert np.all(np.isfinite(positions)) and np.all(positions > 0)
    assert np.all(np.diff(positions) > 0)
    np.testing.assert_allclose(positions, [row["measured_peak_position"] for row in rows])


def test_script_graph_markers_and_labels_match_baseline(script_run):
    """Keep fluorescence anchors, plot labels, and failure cleanup consistent."""
    case, expected, result = script_run
    payload = result.peak_lines_payload or {}
    baseline = expected["payload"]
    if expected["warning"]:
        assert not payload.get("scatter_guide_annotations")
        if not baseline.get("points"):
            assert not payload.get("points")
            return
    assert payload["labels"] == baseline["labels"]
    assert [point["kind"] for point in payload["points"]] == [
        point["kind"] for point in baseline["points"]
    ]
    np.testing.assert_allclose(
        [[point["x"], point["y"]] for point in payload["points"]],
        [[point["x"], point["y"]] for point in baseline["points"]],
        rtol=case["position_relative_tolerance"], atol=0,
    )
    np.testing.assert_allclose(payload["baseline_cutoff"], baseline["baseline_cutoff"], rtol=0.01)
    assert [item["label"] for item in payload.get("scatter_guide_annotations", [])] == [
        item["label"] for item in baseline.get("scatter_guide_annotations", [])
    ]
