"""Normalize saved calibration records at the apply workflow boundary."""

import json
from dataclasses import dataclass
from functools import cached_property
from RosettaX.workflow.scattering.calibration_models import ScatteringCalibration
from typing import Any

APPLIED_OUTPUT_CHANNEL_NAME_KEY = "applied_output_channel_name"


@dataclass(frozen=True)
class CalibrationPayload:
    """Shared calibration fields and the saved data used by model-specific readers.

    Attributes
    ----------
    saved_payload : dict
        Original calibration fields, including metadata used in reports.
    calibration_type : str
        Saved model family.
    source_channel : str
        Detector column, with the legacy measured channel as a fallback.
    output_quantity : str
        Saved quantity produced by the calibration.
    output_channel_name : str
        Preferred name of the derived detector column, if saved.
    version : int or None
        Numeric schema version, if available.
    """

    saved_payload: dict[str, Any]
    calibration_type: str
    source_channel: str
    output_quantity: str
    output_channel_name: str
    version: int | None

    @classmethod
    def from_value(cls, *, value: Any) -> "CalibrationPayload":
        """Read current and legacy header fields from a saved payload."""
        if isinstance(value, cls):
            return value

        payload = value if isinstance(value, dict) else {}
        instrument_response = payload.get("instrument_response")
        measured_channel = (
            instrument_response.get("measured_channel")
            if isinstance(instrument_response, dict)
            else None
        )
        source_channel = str(payload.get("source_channel") or "").strip()
        try:
            version = int(payload.get("version"))
        except (TypeError, ValueError, OverflowError):
            version = None

        return cls(
            saved_payload=payload,
            calibration_type=str(payload.get("calibration_type") or "").strip(),
            source_channel=source_channel or str(measured_channel or "").strip(),
            output_quantity=str(payload.get("output_quantity") or "").strip(),
            output_channel_name=str(payload.get(APPLIED_OUTPUT_CHANNEL_NAME_KEY) or "").strip(),
            version=version,
        )

    @property
    def is_scattering_v2(self) -> bool:
        """Return whether the saved payload uses the scattering apply model."""
        return self.calibration_type == "scattering" and self.version is not None and self.version >= 2

    @cached_property
    def scattering_calibration(self) -> ScatteringCalibration:
        """Validate and construct the scattering model once for this apply run."""
        return ScatteringCalibration.from_dict(self.saved_payload)


def decode_calibration_record(*, content: str | bytes, require_schema: bool = False) -> dict[str, Any]:
    """Read the calibration envelope used by saved files and Dash uploads."""
    record = json.loads(content)
    if not isinstance(record, dict):
        raise ValueError("Calibration file root record is invalid.")

    if require_schema:
        schema = str(record.get("schema", "")).strip()
        if schema != "rosettax_calibration_v1":
            raise ValueError(f"Calibration file schema is unsupported: {schema or '<missing>'}.")

    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise ValueError('Calibration file is missing top level "payload".')

    return payload
