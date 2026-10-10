"""Regression tests for workflow page session."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import pytest

from RosettaX.workflow.page_session import FeedbackState, WorkflowProgressState


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
