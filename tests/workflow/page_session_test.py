"""Regression tests for workflow page session."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import pytest
from RosettaX.workflow.page_session import FeedbackState, WorkflowProgressState
from RosettaX.workflow.peak.adapters.fluorescence import FluorescencePeakWorkflowAdapter
from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter
from RosettaX.workflow.peak.core.mutation import (
    resolve_detector_change,
    touch_peak_graph_revision,
)
from RosettaX.workflow.table.fluorescence import FluorescenceReferenceTable
from RosettaX.workflow.upload.adapters import FluorescenceUploadAdapter


def test_feedback_state_round_trips_and_maps_to_dash_outputs() -> None:
    """Check feedback state round trips and maps to Dash outputs."""
    feedback = FeedbackState.success("Files loaded.")

    assert feedback.to_display_tuple() == ("Files loaded.", "success")
    assert FeedbackState.from_dict(feedback.to_dict()) == feedback
    assert FeedbackState.from_dict({"text": "Legacy feedback", "color": "warning"}) == (
        FeedbackState.warning("Legacy feedback")
    )


def test_empty_feedback_is_hidden() -> None:
    """Check empty feedback is hidden."""
    assert FeedbackState.from_dict(None) == FeedbackState.empty()


def test_workflow_progress_bounds_completion_and_resolves_step_states() -> None:
    """Check workflow progress bounds completion and resolves step states."""
    progress = WorkflowProgressState(total_steps=3, completed_count=10)

    assert progress.completed_count == 3
    assert progress.is_complete is True
    assert progress.current_step_number is None
    assert progress.completion_percent == 100
    assert [progress.step_status(number) for number in range(1, 4)] == [
        "complete",
        "complete",
        "complete",
    ]
    assert WorkflowProgressState.from_dict(progress.to_dict()) == progress


def test_workflow_progress_identifies_current_and_blocked_steps() -> None:
    """Check workflow progress identifies current and blocked steps."""
    progress = WorkflowProgressState(total_steps=3, completed_count=1)

    assert progress.current_step_number == 2
    assert [progress.step_status(number) for number in range(1, 4)] == [
        "complete",
        "current",
        "blocked",
    ]
    with pytest.raises(ValueError, match="step_number"):
        progress.step_status(0)


@pytest.mark.parametrize("adapter", [FluorescencePeakWorkflowAdapter(), ScatteringPeakWorkflowAdapter()])
def test_peak_graph_revision_survives_real_page_state_round_trip(adapter):
    """Retain revision changes when graph data are otherwise identical."""
    page_state = adapter.get_page_state_from_payload(None)
    first = touch_peak_graph_revision(adapter=adapter, page_state=page_state, reason="run_action", process_name="Automatic 1D")
    second = touch_peak_graph_revision(adapter=adapter, page_state=first, reason="run_action", process_name="Automatic 1D")

    first_payload = first.to_dict()
    second_payload = second.to_dict()
    revision = second_payload.pop("peak_graph_revision")
    assert revision["reason"] == "run_action"
    assert revision["id"] != first_payload.pop("peak_graph_revision")["id"]
    assert second_payload == first_payload


@pytest.mark.parametrize("new_detectors, expected", [
    ({"scattering": "SSC-A", "green_fluorescence": "FITC-A"}, None),
    ({"scattering": "FSC-A", "green_fluorescence": "FITC-A"}, True),
    ({"scattering": "SSC-A", "green_fluorescence": None}, True),
])
def test_detector_changes_invalidate_only_measurements_from_another_selection(new_detectors, expected):
    """Invalidate any changed channel after a run and retain measurements on hydration."""
    process_name = "Rosetta Script Mixture"
    context = {
        "process_name": process_name,
        "detector_channels": {"scattering": "SSC-A", "green_fluorescence": "FITC-A"},
    }
    adapter = ScatteringPeakWorkflowAdapter()
    page_state = adapter.build_page_state(payload={"peak_table_context": context})

    assert resolve_detector_change(
        page_state_payload=page_state.to_dict(), process_name=process_name, detector_channels=new_detectors,
    ) is expected


def test_replacing_fluorescence_upload_preserves_reference_values() -> None:
    """Clear measured intensities and graph results when a different file is loaded."""
    adapter = FluorescenceUploadAdapter()
    calibrated_column = FluorescenceReferenceTable.column_calibrated_intensity
    measured_column = FluorescenceReferenceTable.column_measured_intensity
    old_state = adapter.page_state_from_payload({
        "uploaded_fcs_path": "old.fcs",
        "peak_graph_revision": {"id": "previous-run"},
        "reference_table_rows": [{calibrated_column: "1200", measured_column: "500"}],
    })

    new_state = adapter.update_page_state_after_upload(
        current_page_state=old_state, uploaded_fcs_path="new.fcs", uploaded_filename="new.fcs",
    )

    assert new_state.uploaded_fcs_path == "new.fcs"
    assert new_state.peak_graph_revision is None
    assert new_state.reference_table_rows == [{calibrated_column: "1200", measured_column: ""}]
    assert old_state.reference_table_rows == [{calibrated_column: "1200", measured_column: "500"}]
