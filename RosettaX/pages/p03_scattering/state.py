# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ScatteringPageState:
    """
    Single source of truth for the scattering calibration page.

    This state object is serialized into one Dash dcc.Store and progressively
    replaces scattered section specific stores.
    """

    uploaded_fcs_path: Optional[str] = None
    uploaded_filename: Optional[str] = None

    peak_lines_payload: Optional[dict[str, Any]] = None
    scattering_peak_lines_payload: Optional[dict[str, Any]] = None

    scattering_parameters_payload: Optional[dict[str, Any]] = None

    calibration_graph_payload: Optional[dict[str, Any]] = None
    calibration_model_graph_payload: Optional[dict[str, Any]] = None
    calibration_payload: Optional[dict[str, Any]] = None

    status_message: str = ""

    @classmethod
    def empty(cls) -> "ScatteringPageState":
        """
        Build an empty scattering page state.

        Returns
        -------
        ScatteringPageState
            Empty page state.
        """
        return cls(
            peak_lines_payload={
                "positions": [],
                "labels": [],
            },
            scattering_peak_lines_payload={
                "positions": [],
                "labels": [],
            },
        )

    @classmethod
    def from_dict(cls, payload: Optional[dict[str, Any]]) -> "ScatteringPageState":
        """
        Build a scattering page state from a serialized dictionary.

        Unknown keys are ignored so older browser sessions do not crash after
        the state schema evolves.

        Parameters
        ----------
        payload:
            Serialized page state from Dash dcc.Store.

        Returns
        -------
        ScatteringPageState
            Parsed scattering page state.
        """
        if not payload:
            return cls.empty()

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in payload.items()
            if key in valid_keys
        }

        peak_lines_payload = clean_payload.get("peak_lines_payload")
        scattering_peak_lines_payload = clean_payload.get("scattering_peak_lines_payload")

        if peak_lines_payload is None and scattering_peak_lines_payload is None:
            empty_peak_lines_payload = {
                "positions": [],
                "labels": [],
            }
            clean_payload["peak_lines_payload"] = empty_peak_lines_payload
            clean_payload["scattering_peak_lines_payload"] = dict(empty_peak_lines_payload)

        elif peak_lines_payload is None:
            clean_payload["peak_lines_payload"] = scattering_peak_lines_payload

        elif scattering_peak_lines_payload is None:
            clean_payload["scattering_peak_lines_payload"] = peak_lines_payload

        return cls(**clean_payload)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the scattering page state.

        Returns
        -------
        dict[str, Any]
            Dictionary suitable for Dash dcc.Store.
        """
        return asdict(self)

    def update(self, **changes: Any) -> "ScatteringPageState":
        """
        Return a new state with selected fields changed.

        Parameters
        ----------
        **changes:
            Field values to update.

        Returns
        -------
        ScatteringPageState
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
            raise KeyError(f"Unknown scattering page state field(s): {unknown_keys_text}")

        current_payload = self.to_dict()
        current_payload.update(changes)

        return self.from_dict(current_payload)