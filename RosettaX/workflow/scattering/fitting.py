"""Scattering fitting."""

import logging

import numpy as np

from .calibration_models import ScatteringInstrumentResponse
from .numerical_arrays import _as_flat_float_array, _validate_same_size

logger = logging.getLogger(__name__)


def fit_linear_instrument_response(
    *,
    measured_peak_values: np.ndarray,
    theoretical_coupling_values: np.ndarray,
    measured_channel: str,
    force_zero_intercept: bool = True,
) -> ScatteringInstrumentResponse:
    """
    Fit the linear instrument response from measured peaks to modeled coupling.

    The fitted model is:

        theoretical_coupling = slope * measured_peak + intercept

    If force_zero_intercept is True, the intercept is fixed to zero.
    """
    logger.debug(
        "fit_linear_instrument_response called with measured_channel=%r "
        "force_zero_intercept=%r",
        measured_channel,
        force_zero_intercept,
    )

    measured_array = _as_flat_float_array(
        name="fit_measured_peak_values_before_mask",
        values=measured_peak_values,
    )

    coupling_array = _as_flat_float_array(
        name="fit_theoretical_coupling_values_before_mask",
        values=theoretical_coupling_values,
    )

    _validate_same_size(
        first_values=measured_array,
        second_values=coupling_array,
        first_name="measured_peak_values",
        second_name="theoretical_coupling_values",
    )

    valid_mask = (
        np.isfinite(
            measured_array,
        )
        & np.isfinite(
            coupling_array,
        )
    )

    logger.debug(
        "fit_linear_instrument_response finite valid_count=%r total_count=%r",
        int(np.sum(valid_mask)),
        measured_array.size,
    )

    measured_array = measured_array[valid_mask]
    coupling_array = coupling_array[valid_mask]

    if np.any(measured_array <= 0.0):
        raise ValueError(
            "measured_peak_values must contain only positive finite values."
        )

    if np.any(coupling_array <= 0.0):
        raise ValueError(
            "theoretical_coupling_values must contain only positive finite values."
        )

    if measured_array.size < 2:
        logger.error(
            "fit_linear_instrument_response failed because finite calibration point count=%r.",
            measured_array.size,
        )
        raise ValueError("At least two valid calibration points are required.")

    if force_zero_intercept:
        nonzero_mask = measured_array != 0.0

        logger.debug(
            "fit_linear_instrument_response zero intercept nonzero_count=%r total_count=%r",
            int(np.sum(nonzero_mask)),
            measured_array.size,
        )

        measured_array = measured_array[nonzero_mask]
        coupling_array = coupling_array[nonzero_mask]

    if measured_array.size < 2:
        logger.error(
            "fit_linear_instrument_response failed because nonzero calibration point count=%r.",
            measured_array.size,
        )
        raise ValueError("At least two nonzero measured values are required.")

    if force_zero_intercept:
        denominator = float(
            np.sum(
                measured_array * measured_array,
            )
        )

        logger.debug(
            "fit_linear_instrument_response zero intercept denominator=%r",
            denominator,
        )

        if denominator == 0.0:
            logger.error(
                "fit_linear_instrument_response failed because denominator is zero."
            )
            raise ValueError("Cannot fit zero intercept response with zero denominator.")

        slope = float(
            np.sum(
                measured_array * coupling_array,
            )
            / denominator
        )

        intercept = 0.0

    else:
        slope, intercept = np.polyfit(
            measured_array,
            coupling_array,
            deg=1,
        )

        slope = float(
            slope,
        )

        intercept = float(
            intercept,
        )

    predicted_coupling = slope * measured_array + intercept

    r_squared = compute_r_squared(
        observed_values=coupling_array,
        predicted_values=predicted_coupling,
    )

    if not np.isfinite(slope) or not np.isfinite(intercept) or not np.isfinite(r_squared):
        raise ValueError(
            "Instrument-response fit produced non-finite parameters or "
            "undefined fit quality."
        )

    logger.debug(
        "fit_linear_instrument_response fitted slope=%r intercept=%r r_squared=%r "
        "used_point_count=%r",
        slope,
        intercept,
        r_squared,
        measured_array.size,
    )

    return ScatteringInstrumentResponse(
        measured_channel=measured_channel,
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        force_zero_intercept=force_zero_intercept,
    )


def compute_r_squared(
    *,
    observed_values: np.ndarray,
    predicted_values: np.ndarray,
) -> float:
    """
    Compute coefficient of determination.
    """
    observed_array = _as_flat_float_array(
        name="r_squared_observed_values",
        values=observed_values,
    )

    predicted_array = _as_flat_float_array(
        name="r_squared_predicted_values",
        values=predicted_values,
    )

    _validate_same_size(
        first_values=observed_array,
        second_values=predicted_array,
        first_name="observed_values",
        second_name="predicted_values",
    )

    residual_sum_of_squares = float(
        np.sum(
            np.square(
                observed_array - predicted_array,
            )
        )
    )

    total_sum_of_squares = float(
        np.sum(
            np.square(
                observed_array - np.mean(
                    observed_array,
                )
            )
        )
    )

    logger.debug(
        "compute_r_squared residual_sum_of_squares=%r total_sum_of_squares=%r",
        residual_sum_of_squares,
        total_sum_of_squares,
    )

    if total_sum_of_squares == 0.0:
        logger.debug(
            "compute_r_squared returning nan because total_sum_of_squares is zero."
        )
        return np.nan

    return 1.0 - residual_sum_of_squares / total_sum_of_squares
