"""Scattering numerical arrays."""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def _as_flat_float_array(
    *,
    name: str,
    values: Any,
) -> np.ndarray:
    """
    Convert values to a one dimensional float array and log its content summary.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)
    except Exception:
        logger.exception(
            "_as_flat_float_array failed for %s with values=%r",
            name,
            values,
        )
        raise

    _log_array_summary(
        name=name,
        values=array,
    )

    return array


def _validate_same_size(
    *,
    first_values: np.ndarray,
    second_values: np.ndarray,
    first_name: str,
    second_name: str,
) -> None:
    """
    Validate that two arrays have the same size.
    """
    first_values = np.asarray(
        first_values,
    ).reshape(-1)

    second_values = np.asarray(
        second_values,
    ).reshape(-1)

    if first_values.size == second_values.size:
        logger.debug(
            "_validate_same_size passed for %s and %s with size=%r",
            first_name,
            second_name,
            first_values.size,
        )
        return

    logger.error(
        "_validate_same_size failed: %s size=%r, %s size=%r",
        first_name,
        first_values.size,
        second_name,
        second_values.size,
    )

    raise ValueError(
        f"{first_name} and {second_name} must have the same length. "
        f"Got {first_values.size} and {second_values.size}."
    )


def _log_array_summary(
    *,
    name: str,
    values: Any,
) -> None:
    """
    Log a compact numerical summary of an array.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)
    except Exception:
        logger.debug(
            "%s summary unavailable because conversion to float array failed. raw_type=%s",
            name,
            type(values).__name__,
        )
        return

    finite_mask = np.isfinite(
        array,
    )

    finite_values = array[finite_mask]

    if finite_values.size == 0:
        logger.debug(
            "%s summary: size=%r finite_count=0 nan_count=%r inf_count=%r values=%r",
            name,
            array.size,
            int(np.sum(np.isnan(array))),
            int(np.sum(np.isinf(array))),
            array.tolist(),
        )
        return

    logger.debug(
        "%s summary: size=%r finite_count=%r nan_count=%r inf_count=%r "
        "min=%r max=%r first_values=%r",
        name,
        array.size,
        finite_values.size,
        int(np.sum(np.isnan(array))),
        int(np.sum(np.isinf(array))),
        float(np.min(finite_values)),
        float(np.max(finite_values)),
        array[:10].tolist(),
    )
