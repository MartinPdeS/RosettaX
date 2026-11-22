"""Verify configured-model Rosetta assignments against known peak identities."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import numpy as np
from RosettaX.workflow.page_session.scattering import ScatteringPageState
from RosettaX.workflow.parameters.table import MIE_MODEL_SOLID_SPHERE
from RosettaX.workflow.scattering.rosetta_assignment import (
    compute_model_with_rosetta_assignments,
    match_rosetta_coupling,
    resolve_rosetta_model_rows,
    rosetta_confirmation_pending,
)

# An irregular reference ladder with a turnover between 600 and 799 nm.
COUPLING = {
    70: 1.0, 100: 2.4, 125: 4.5, 140: 7.0, 147: 10.0, 203: 30.0,
    296: 81.0, 380: 115.0, 400: 135.0, 600: 310.0, 799: 240.0, 994: 810.0,
}


def test_model_recovers_sizes_with_missing_and_extra_peaks() -> None:
    """Recover identities with a gap, a spurious peak, and nonmonotonic coupling."""
    expected_diameters = (100, 147, None, 296, 799, 600)
    observations = np.array([2.4, 10.0, 49.0, 81.0, 240.0, 310.0]) * 23
    scatter = np.array([observations, observations * 0.995, observations * 1.008, observations * 1.003])
    markers = [{
        "marker_role": "Dim marker", "validated": True, "identity_uncertain": True,
        "selected_peak": {"mean": 7.0 * 23, "bootstrap_positions": [160.7, 161.3, 161.1]},
    }]
    assert match_rosetta_coupling(
        scatter_positions=scatter, coupled_sizes=COUPLING, marker_diagnostics=markers,
    ) == {index: diameter for index, diameter in enumerate(expected_diameters) if diameter}


def test_model_keeps_only_shared_identities_when_coupling_is_ambiguous() -> None:
    """Leave indistinguishable peaks unresolved even when both responses fit exactly."""
    coupled_sizes = dict(COUPLING)
    coupled_sizes[203] = coupled_sizes[147]
    scatter = np.tile([2.4, 10.0, 81.0, 240.0, 310.0], (4, 1))
    markers = [{
        "marker_role": "Dim marker", "validated": True,
        "selected_peak": {"mean": 7.0, "bootstrap_positions": [7.0, 7.0, 7.0]},
    }, {"marker_role": "Bright marker", "validated": False}]
    assert match_rosetta_coupling(
        scatter_positions=scatter, coupled_sizes=coupled_sizes, marker_diagnostics=markers,
    ) == {0: 100, 2: 296, 3: 799, 4: 600}


def test_coupling_replaces_provisional_sizes_and_respects_table_edits() -> None:
    """Use committed evidence, update provisional rows, and protect user-edited rows."""
    raw_peaks = [2.4, 10.0, 81.0, 240.0]
    rows = [{"measured_peak_position": position, "particle_diameter_nm": 70} for position in raw_peaks]
    evidence = {
        "rows": rows,
        "scatter": [{"position": position, "replicates": [position] * 3} for position in raw_peaks],
        "markers": [{
            "marker_role": "Dim marker", "validated": True,
            "selected_peak": {"mean": 7.0, "bootstrap_positions": [7.0, 7.0, 7.0]},
        }, {"marker_role": "Bright marker", "validated": False}],
    }

    def model_rows(*, current_rows):
        """Supply fixed theoretical coupling to exercise row reconciliation."""
        return [
            dict(row, expected_coupling=COUPLING.get(row["particle_diameter_nm"], 1.0))
            for row in current_rows
        ]

    assert rosetta_confirmation_pending(current_rows=rows, evidence=evidence)
    resolved, status, next_evidence = resolve_rosetta_model_rows(
        current_rows=rows, evidence=evidence, compute_model=model_rows,
    )
    assert [row["particle_diameter_nm"] for row in resolved] == [100, 147, 296, 799]
    assert status == ""
    assert not rosetta_confirmation_pending(current_rows=resolved, evidence=next_evidence)
    edited = [dict(rows[0], particle_diameter_nm=77), *rows[1:]]
    assert resolve_rosetta_model_rows(
        current_rows=edited, evidence=evidence, compute_model=model_rows,
    ) == (edited, "", None)


    page_state = ScatteringPageState(
        rosetta_assignment_evidence=evidence,
        scattering_peak_lines_payload={"scatter_guide_annotations": []},
        calibration_payload={"previous": True},
        calibration_saved=True,
    )
    computed_rows, updated_state, status = compute_model_with_rosetta_assignments(
        current_rows=rows,
        page_state=page_state,
        mie_model=MIE_MODEL_SOLID_SPHERE,
        compute_coupling=model_rows,
    )
    assert status == ""
    assert [row["expected_coupling"] for row in computed_rows] == raw_peaks
    assert updated_state.rosetta_assignment_evidence == next_evidence
    assert [
        entry["diameter_nm"] for entry in updated_state.scattering_peak_lines_payload["rosetta_size_assignments"]
    ] == [100, 147, 296, 799]
    assert updated_state.calibration_payload is None
    assert not updated_state.calibration_saved

    computed_rows, updated_state, status = compute_model_with_rosetta_assignments(
        current_rows=edited,
        page_state=page_state,
        mie_model=MIE_MODEL_SOLID_SPHERE,
        compute_coupling=model_rows,
    )
    assert status == ""
    assert computed_rows[0]["particle_diameter_nm"] == 77
    assert updated_state.rosetta_assignment_evidence is None
    assert updated_state.calibration_payload == page_state.calibration_payload
    assert updated_state.calibration_saved


def test_bootstrap_disagreement_does_not_confirm_a_shifted_identity() -> None:
    """Omit the bead whose identity changes in a perturbed scatter fit."""
    coupling = dict(COUPLING)
    coupling[203] = 13.0
    scatter = np.tile([2.4, 10.0, 81.0, 240.0, 310.0], (4, 1))
    scatter[-1, 1] = 13.0
    markers = [{
        "marker_role": "Dim marker", "validated": True,
        "selected_peak": {"mean": 7.0, "bootstrap_positions": [7.0] * 3},
    }, {"marker_role": "Bright marker", "validated": False}]
    assert match_rosetta_coupling(
        scatter_positions=scatter, coupled_sizes=coupling, marker_diagnostics=markers,
    ) == {0: 100, 2: 296, 3: 799, 4: 600}
