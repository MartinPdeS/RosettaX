"""Pure models for serializable page feedback and workflow progress."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeedbackState:
    """A serializable user-facing message with its Bootstrap color."""

    message: str
    color: str = "secondary"
    is_visible: bool = True

    @classmethod
    def empty(cls) -> "FeedbackState":
        """Build hidden feedback for an unstarted workflow."""
        return cls(
            message="",
            color="secondary",
            is_visible=False,
        )

    @classmethod
    def success(cls, message: str) -> "FeedbackState":
        """Build success feedback."""
        return cls(message=message, color="success")

    @classmethod
    def warning(cls, message: str) -> "FeedbackState":
        """Build warning feedback."""
        return cls(message=message, color="warning")

    @classmethod
    def danger(cls, message: str) -> "FeedbackState":
        """Build failure feedback."""
        return cls(message=message, color="danger")

    @classmethod
    def from_dict(cls, payload: Any) -> "FeedbackState":
        """Restore serialized feedback while accepting common legacy field names."""
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, dict):
            return cls.empty()

        message = str(
            payload.get("message")
            or payload.get("text")
            or payload.get("children")
            or ""
        )
        color = str(payload.get("color") or "secondary")
        is_visible = bool(payload.get("is_visible", bool(message)))
        return cls(
            message=message,
            color=color,
            is_visible=is_visible,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize this state for a Dash store."""
        return {
            "message": self.message,
            "color": self.color,
            "is_visible": self.is_visible,
        }

    def to_display_tuple(self) -> tuple[str, str]:
        """Return the message and color in Dash output order."""
        return self.message, self.color


@dataclass(frozen=True)
class WorkflowProgressState:
    """Contiguous completion state for an ordered workflow."""

    total_steps: int
    completed_count: int = 0

    def __post_init__(self) -> None:
        if self.total_steps < 0:
            raise ValueError("total_steps must be non-negative.")
        object.__setattr__(
            self,
            "completed_count",
            max(0, min(int(self.completed_count), self.total_steps)),
        )

    @classmethod
    def from_dict(cls, payload: Any) -> "WorkflowProgressState":
        """Restore serialized workflow progress."""
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, dict):
            return cls(total_steps=0)
        return cls(
            total_steps=int(payload.get("total_steps") or 0),
            completed_count=int(payload.get("completed_count") or 0),
        )

    @property
    def is_complete(self) -> bool:
        """Return whether every workflow step is complete."""
        return self.total_steps > 0 and self.completed_count == self.total_steps

    @property
    def current_step_number(self) -> int | None:
        """Return the one-based active step number, when one remains."""
        if self.completed_count >= self.total_steps:
            return None
        return self.completed_count + 1

    @property
    def completion_percent(self) -> float:
        """Return the completed percentage without division by zero."""
        if not self.total_steps:
            return 0.0
        return 100 * self.completed_count / self.total_steps

    def step_status(self, step_number: int) -> str:
        """Return ``complete``, ``current``, or ``blocked`` for one-based step."""
        if step_number < 1 or step_number > self.total_steps:
            raise ValueError(
                f"step_number must be between 1 and {self.total_steps}."
            )
        if step_number <= self.completed_count:
            return "complete"
        if step_number == self.current_step_number:
            return "current"
        return "blocked"

    def to_dict(self) -> dict[str, int]:
        """Serialize this state for a Dash store."""
        return {
            "total_steps": self.total_steps,
            "completed_count": self.completed_count,
        }
