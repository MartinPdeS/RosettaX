"""Apply saved fluorescence calibration models to detector measurements."""

import numpy as np
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FluorescenceCalibration:
    """A linear calibration or a power law when a prefactor is present."""

    slope: float
    intercept: float
    prefactor: float | None = None

    @classmethod
    def from_payload(cls, *, payload: dict[str, Any]) -> "FluorescenceCalibration":
        """Resolve the coefficients of a saved log, slope, or scale model."""
        if not isinstance(payload, dict):
            raise ValueError("Calibration payload must be a dictionary.")

        parameters = payload.get("parameters")
        nested_payload = payload.get("payload")
        parameters = parameters if isinstance(parameters, dict) else {}
        nested_payload = nested_payload if isinstance(nested_payload, dict) else {}
        model = str(payload.get("fit_model", "")).strip() or str(nested_payload.get("model", "")).strip()

        if "log10(y)=slope*log10(x)+intercept" in model:
            return cls.from_log_parameters(parameters=parameters, payload=nested_payload)
        if payload.get("slope") is not None and payload.get("intercept") is not None:
            return cls(slope=float(payload["slope"]), intercept=float(payload["intercept"]))
        if payload.get("scale") is not None:
            return cls(slope=float(payload["scale"]), intercept=float(payload.get("offset", 0.0)))

        raise ValueError(
            "Unsupported calibration payload format. Expected a log model, "
            '"slope"/"intercept", or "scale"/"offset".'
        )

    @classmethod
    def from_log_parameters(
        cls, *, parameters: dict[str, Any], payload: dict[str, Any],
    ) -> "FluorescenceCalibration":
        """Resolve log coefficients using the nested payload as a legacy fallback."""
        slope = parameters.get("slope", payload.get("slope"))
        intercept = parameters.get("intercept", payload.get("intercept"))
        if slope is None or intercept is None:
            raise ValueError("Log calibration payload is missing slope or intercept.")

        prefactor = parameters.get("prefactor", payload.get("prefactor"))
        intercept = float(intercept)
        return cls(
            slope=float(slope),
            intercept=intercept,
            prefactor=float(prefactor) if prefactor is not None else 10.0 ** intercept,
        )


def apply_legacy_calibration_to_series(
    *,
    values: np.ndarray,
    calibration_payload: dict[str, Any] | FluorescenceCalibration,
    warning_messages: list[str] | None = None,
    source_channel: str | None = None,
) -> np.ndarray:
    """Apply a saved log or linear fluorescence model to an array of detector values."""
    calibration = (
        calibration_payload
        if isinstance(calibration_payload, FluorescenceCalibration)
        else FluorescenceCalibration.from_payload(payload=calibration_payload)
    )
    values_array = np.asarray(values, dtype=float)
    prefactor = calibration.prefactor
    slope = calibration.slope
    if prefactor is None:
        return slope * values_array + calibration.intercept

    negative_mask = values_array < 0

    if np.any(negative_mask):
        values_array = values_array.copy()
        values_array[negative_mask] = 0.0

        if warning_messages is not None:
            negative_count = int(np.count_nonzero(negative_mask))
            channel_text = str(source_channel or "the source channel").strip()
            warning_message = (
                f'Clamped {negative_count} negative event(s) to 0 before applying '
                f'log calibration to "{channel_text}".'
            )

            if warning_message not in warning_messages:
                warning_messages.append(warning_message)

    calibrated_values = np.zeros_like(
        values_array,
        dtype=float,
    )

    positive_mask = values_array > 0

    calibrated_values[positive_mask] = prefactor * np.power(
        values_array[positive_mask],
        slope,
    )

    calibrated_values[~positive_mask] = 0.0

    return calibrated_values



def apply_log_calibration_to_series(
    *,
    values: np.ndarray,
    nested_parameters: dict[str, Any],
    nested_payload: dict[str, Any],
    warning_messages: list[str] | None = None,
    source_channel: str | None = None,
) -> np.ndarray:
    """Apply a log power law from saved coefficients to an array of detector values."""
    return apply_legacy_calibration_to_series(
        values=values,
        calibration_payload=FluorescenceCalibration.from_log_parameters(
            parameters=nested_parameters, payload=nested_payload,
        ),
        warning_messages=warning_messages,
        source_channel=source_channel,
    )
