# -*- coding: utf-8 -*-

from dataclasses import asdict, dataclass
from typing import Any, Optional


def build_empty_peak_lines_payload() -> dict[str, list[Any]]:
    """
    Build an empty peak annotation payload.

    Returns
    -------
    dict[str, list[Any]]
        Empty peak annotation payload.
    """
    return {
        "positions": [],
        "labels": [],
        "x_positions": [],
        "y_positions": [],
        "points": [],
    }


@dataclass(frozen=True)
class FluorescencePageState:
    """
    Single source of truth for the fluorescence calibration page.

    This state stores upload state, threshold state, peak workflow state,
    histogram state, and calibration state in one serializable object.

    Compatibility
    -------------
    Older callbacks may still refer to:
    - uploaded_fcs_filename
    - fluorescence_peak_lines_payload

    Those names are accepted as aliases in from_dict() and update(), but the
    canonical state fields are:
    - uploaded_filename
    - peak_lines_payload
    """

    uploaded_fcs_path: Optional[str] = None
    uploaded_filename: str = ""

    calibration_payload: Optional[dict[str, Any]] = None

    scattering_threshold: Optional[float] = None

    fluorescence_histogram_payload: Optional[dict[str, Any]] = None
    fluorescence_source_channel: Optional[str] = None

    peak_lines_payload: Optional[dict[str, Any]] = None
    fluorescence_peak_lines: Optional[list[float]] = None

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
            uploaded_fcs_path=None,
            uploaded_filename="",
            calibration_payload=None,
            scattering_threshold=None,
            fluorescence_histogram_payload=None,
            fluorescence_source_channel=None,
            peak_lines_payload=build_empty_peak_lines_payload(),
            fluorescence_peak_lines=[],
            status_message="",
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

        normalized_payload = normalize_legacy_payload_keys(
            payload,
        )

        valid_keys = set(cls.__dataclass_fields__.keys())

        clean_payload = {
            key: value
            for key, value in normalized_payload.items()
            if key in valid_keys
        }

        if "uploaded_filename" not in clean_payload:
            clean_payload["uploaded_filename"] = infer_uploaded_filename(
                clean_payload.get("uploaded_fcs_path"),
            )

        if "peak_lines_payload" not in clean_payload:
            clean_payload["peak_lines_payload"] = build_peak_lines_payload_from_legacy_lines(
                clean_payload.get("fluorescence_peak_lines"),
            )

        if clean_payload.get("peak_lines_payload") is None:
            clean_payload["peak_lines_payload"] = build_empty_peak_lines_payload()

        if "fluorescence_peak_lines" not in clean_payload:
            clean_payload["fluorescence_peak_lines"] = extract_1d_positions_from_peak_payload(
                clean_payload.get("peak_lines_payload"),
            )

        if clean_payload.get("fluorescence_peak_lines") is None:
            clean_payload["fluorescence_peak_lines"] = []

        if "status_message" not in clean_payload:
            clean_payload["status_message"] = ""

        return cls(**clean_payload)

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
        normalized_changes = normalize_legacy_payload_keys(
            changes,
        )

        valid_keys = set(self.__dataclass_fields__.keys())
        unknown_keys = set(normalized_changes.keys()) - valid_keys

        if unknown_keys:
            unknown_keys_text = ", ".join(
                sorted(unknown_keys),
            )

            raise KeyError(
                f"Unknown fluorescence page state field(s): {unknown_keys_text}"
            )

        current_payload = self.to_dict()
        current_payload.update(
            normalized_changes,
        )

        return self.from_dict(
            current_payload,
        )


def normalize_legacy_payload_keys(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize legacy page state field names to canonical field names.

    Parameters
    ----------
    payload:
        Raw page state payload or update dictionary.

    Returns
    -------
    dict[str, Any]
        Payload with canonical keys.
    """
    normalized_payload = dict(
        payload or {},
    )

    if "uploaded_fcs_filename" in normalized_payload:
        normalized_payload["uploaded_filename"] = normalized_payload.pop(
            "uploaded_fcs_filename",
        )

    if "fluorescence_peak_lines_payload" in normalized_payload:
        normalized_payload["peak_lines_payload"] = normalized_payload.pop(
            "fluorescence_peak_lines_payload",
        )

    return normalized_payload


def infer_uploaded_filename(
    uploaded_fcs_path: Any,
) -> str:
    """
    Infer the uploaded filename from the uploaded FCS path.

    Parameters
    ----------
    uploaded_fcs_path:
        Uploaded FCS path.

    Returns
    -------
    str
        Filename or empty string.
    """
    uploaded_fcs_path_string = str(
        uploaded_fcs_path or "",
    ).strip()

    if not uploaded_fcs_path_string:
        return ""

    return uploaded_fcs_path_string.replace("\\", "/").split("/")[-1]


def build_peak_lines_payload_from_legacy_lines(
    fluorescence_peak_lines: Any,
) -> dict[str, list[Any]]:
    """
    Build a peak payload from the previous fluorescence_peak_lines list.

    Parameters
    ----------
    fluorescence_peak_lines:
        Legacy list of 1D peak positions.

    Returns
    -------
    dict[str, list[Any]]
        Peak annotation payload.
    """
    peak_positions: list[float] = []

    if isinstance(fluorescence_peak_lines, list):
        for value in fluorescence_peak_lines:
            try:
                peak_positions.append(
                    float(value),
                )

            except Exception:
                continue

    return {
        "positions": peak_positions,
        "labels": [
            f"Peak {index + 1}"
            for index in range(len(peak_positions))
        ],
        "x_positions": [],
        "y_positions": [],
        "points": [],
    }


def extract_1d_positions_from_peak_payload(
    peak_lines_payload: Any,
) -> list[float]:
    """
    Extract 1D positions from a peak annotation payload.

    Parameters
    ----------
    peak_lines_payload:
        Peak annotation payload.

    Returns
    -------
    list[float]
        Extracted positions.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    positions: list[float] = []

    candidate_values = (
        peak_lines_payload.get("positions")
        or peak_lines_payload.get("x_positions")
        or []
    )

    for value in candidate_values:
        try:
            positions.append(
                float(value),
            )

        except Exception:
            continue

    return positions