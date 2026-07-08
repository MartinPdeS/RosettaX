# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ApplyCalibrationPageState:
    """
    Single source of truth for the apply calibration page.

    This state object is serialized into one Dash dcc.Store and progressively
    replaces scattered section-specific stores.
    """

    selected_calibration_path: Optional[str] = None
    uploaded_fcs_path: Optional[str] = None

    apply_result_payload: Optional[dict[str, Any]] = None

    status_message: str = ""

    @classmethod
    def empty(cls) -> "ApplyCalibrationPageState":
        """
        Build an empty apply calibration page state.

        Returns
        -------
        ApplyCalibrationPageState
            Empty page state.
        """
        return cls()

    @classmethod
    def from_dict(cls, payload: Optional[dict[str, Any]]) -> "ApplyCalibrationPageState":
        """
        Build an apply calibration page state from a serialized dictionary.

        Unknown keys are ignored so older browser sessions do not crash after
        the state schema evolves.

        Parameters
        ----------
        payload:
            Serialized page state from Dash dcc.Store.

        Returns
        -------
        ApplyCalibrationPageState
            Parsed apply calibration page state.
        """
        if not payload:
            return cls.empty()

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in payload.items()
            if key in valid_keys
        }

        return cls(**clean_payload)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the apply calibration page state.

        Returns
        -------
        dict[str, Any]
            Dictionary suitable for Dash dcc.Store.
        """
        return asdict(self)

    def update(self, **changes: Any) -> "ApplyCalibrationPageState":
        """
        Return a new state with selected fields changed.

        Parameters
        ----------
        **changes:
            Field values to update.

        Returns
        -------
        ApplyCalibrationPageState
            Updated immutable state.

        Raises
        ------
        KeyError
            If an unknown state field is provided.
        """
        valid_keys = set(self.__dataclass_fields__.keys())
        unknown_keys = set(changes.keys()) - valid_keys

        if unknown_keys:
            unknown_keys_text = ", ".join(sorted(unknown_keys))
            raise KeyError(f"Unknown apply calibration page state field(s): {unknown_keys_text}")

        current_payload = self.to_dict()
        current_payload.update(changes)

        return self.from_dict(current_payload)