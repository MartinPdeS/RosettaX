# -*- coding: utf-8 -*-

from typing import Any

import numpy as np


def apply_legacy_calibration_to_series(
    *,
    values: np.ndarray,
    calibration_payload: dict[str, Any],
) -> np.ndarray:
    """
    Apply a legacy fluorescence or simple linear calibration payload.

    Supported schemas
    -----------------
    - log10(y)=slope*log10(x)+intercept
    - top level slope/intercept
    - top level scale/offset
    """
    values_array = np.asarray(
        values,
        dtype=float,
    )

    if not isinstance(calibration_payload, dict):
        raise ValueError("Calibration payload must be a dictionary.")

    nested_parameters = calibration_payload.get(
        "parameters",
    )

    if not isinstance(nested_parameters, dict):
        nested_parameters = {}

    nested_payload = calibration_payload.get(
        "payload",
    )

    if not isinstance(nested_payload, dict):
        nested_payload = {}

    fit_model = str(
        calibration_payload.get(
            "fit_model",
            "",
        )
    ).strip()

    nested_model = str(
        nested_payload.get(
            "model",
            "",
        )
    ).strip()

    resolved_model = fit_model or nested_model

    if "log10(y)=slope*log10(x)+intercept" in resolved_model:
        return apply_log_calibration_to_series(
            values=values_array,
            nested_parameters=nested_parameters,
            nested_payload=nested_payload,
        )

    top_level_slope = calibration_payload.get(
        "slope",
    )

    top_level_intercept = calibration_payload.get(
        "intercept",
    )

    if top_level_slope is not None and top_level_intercept is not None:
        slope = float(
            top_level_slope,
        )

        intercept = float(
            top_level_intercept,
        )

        return slope * values_array + intercept

    top_level_scale = calibration_payload.get(
        "scale",
    )

    if top_level_scale is not None:
        scale = float(
            top_level_scale,
        )

        offset = float(
            calibration_payload.get(
                "offset",
                0.0,
            )
        )

        return scale * values_array + offset

    raise ValueError(
        (
            "Unsupported calibration payload format. Expected a log model, "
            '"slope"/"intercept", or "scale"/"offset".'
        )
    )


def apply_log_calibration_to_series(
    *,
    values: np.ndarray,
    nested_parameters: dict[str, Any],
    nested_payload: dict[str, Any],
) -> np.ndarray:
    """
    Apply a log power law calibration.
    """
    values_array = np.asarray(
        values,
        dtype=float,
    )

    slope_value = nested_parameters.get(
        "slope",
        nested_payload.get(
            "slope",
        ),
    )

    intercept_value = nested_parameters.get(
        "intercept",
        nested_payload.get(
            "intercept",
        ),
    )

    prefactor_value = nested_parameters.get(
        "prefactor",
        nested_payload.get(
            "prefactor",
        ),
    )

    if slope_value is None or intercept_value is None:
        raise ValueError(
            "Log calibration payload is missing slope or intercept."
        )

    slope = float(
        slope_value,
    )

    intercept = float(
        intercept_value,
    )

    prefactor = (
        float(
            prefactor_value,
        )
        if prefactor_value is not None
        else float(
            10 ** intercept,
        )
    )

    if np.any(values_array < 0):
        raise ValueError("Log calibration cannot be applied to negative values.")

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