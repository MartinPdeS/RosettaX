"""Pure, serializable state contracts shared by workflow pages."""

from .models import FeedbackState, WorkflowProgressState

__all__ = [
    "FeedbackState",
    "WorkflowProgressState",
]
