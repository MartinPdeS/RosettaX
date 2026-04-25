# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class PeakWorkflowState:
    """
    Generic peak workflow state.

    This is page independent. A page can either store this object directly, or
    embed equivalent fields inside its own page state.
    """

    peak_lines_payload: Optional[dict[str, Any]] = None
    status_message: str = ""

    @classmethod
    def empty(cls) -> "PeakWorkflowState":
        """
        Build an empty peak workflow state.

        Returns
        -------
        PeakWorkflowState
            Empty state.
        """
        return cls(
            peak_lines_payload=build_empty_peak_lines_payload(),
            status_message="",
        )

    @classmethod
    def from_dict(cls, payload: Optional[dict[str, Any]]) -> "PeakWorkflowState":
        """
        Build a peak workflow state from a serialized payload.

        Parameters
        ----------
        payload:
            Serialized state.

        Returns
        -------
        PeakWorkflowState
            Parsed state.
        """
        if not payload:
            return cls.empty()

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in payload.items()
            if key in valid_keys
        }

        if "peak_lines_payload" not in clean_payload:
            clean_payload["peak_lines_payload"] = build_empty_peak_lines_payload()

        return cls(**clean_payload)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the state.

        Returns
        -------
        dict[str, Any]
            JSON compatible payload.
        """
        return asdict(self)

    def update(self, **changes: Any) -> "PeakWorkflowState":
        """
        Return a new state with selected fields updated.

        Parameters
        ----------
        **changes:
            Field updates.

        Returns
        -------
        PeakWorkflowState
            Updated immutable state.
        """
        valid_keys = set(self.__dataclass_fields__.keys())
        unknown_keys = set(changes.keys()) - valid_keys

        if unknown_keys:
            unknown_keys_text = ", ".join(sorted(unknown_keys))
            raise KeyError(f"Unknown peak workflow state field(s): {unknown_keys_text}")

        payload = self.to_dict()
        payload.update(changes)

        return self.from_dict(payload)


def build_empty_peak_lines_payload() -> dict[str, list[Any]]:
    """
    Build an empty peak marker payload.

    Returns
    -------
    dict[str, list[Any]]
        Empty peak marker payload.
    """
    return {
        "positions": [],
        "labels": [],
        "x_positions": [],
        "y_positions": [],
        "points": [],
    }