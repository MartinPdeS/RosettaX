# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FluorescencePageState:
    """
    Single source of truth for the fluorescence calibration page.

    This state object replaces scattered Dash stores that previously held
    upload state, scattering threshold state, fluorescence histogram state,
    peak state, and calibration state independently.

    The object is intentionally serializable so it can be stored directly in
    a Dash dcc.Store component.
    """

    uploaded_fcs_path: Optional[str] = None
    uploaded_filename: Optional[str] = None

    calibration_payload: Optional[dict[str, Any]] = None

    scattering_threshold: Optional[float] = None

    fluorescence_histogram_payload: Optional[dict[str, Any]] = None
    fluorescence_source_channel: Optional[str] = None
    fluorescence_peak_lines_payload: Optional[dict[str, Any]] = None

    status_message: str = ""

    @classmethod
    def empty(cls) -> "FluorescencePageState":
        """
        Build an empty fluorescence page state.

        Returns
        -------
        FluorescencePageState
            Empty page state.
        """
        return cls(
            fluorescence_peak_lines_payload={
                "positions": [],
                "labels": [],
            },
        )

    @classmethod
    def from_dict(cls, payload: Optional[dict[str, Any]]) -> "FluorescencePageState":
        """
        Build a fluorescence page state from a serialized dictionary.

        Unknown keys are ignored so older browser sessions do not crash after
        the state schema evolves.

        Parameters
        ----------
        payload:
            Serialized page state from Dash dcc.Store.

        Returns
        -------
        FluorescencePageState
            Parsed fluorescence page state.
        """
        if not payload:
            return cls.empty()

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in payload.items()
            if key in valid_keys
        }

        state = cls(**clean_payload)

        if state.fluorescence_peak_lines_payload is None:
            state = state.update(
                fluorescence_peak_lines_payload={
                    "positions": [],
                    "labels": [],
                }
            )

        return state

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the fluorescence page state.

        Returns
        -------
        dict[str, Any]
            Dictionary suitable for Dash dcc.Store.
        """
        return asdict(self)

    def update(self, **changes: Any) -> "FluorescencePageState":
        """
        Return a new state with selected fields changed.

        Parameters
        ----------
        **changes:
            Field values to update.

        Returns
        -------
        FluorescencePageState
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
            raise KeyError(f"Unknown fluorescence page state field(s): {unknown_keys_text}")

        current_payload = self.to_dict()
        current_payload.update(changes)

        return self.from_dict(current_payload)