"""Read and filter detector columns while preserving FCS event alignment."""

import numpy as np
from collections.abc import Callable
from RosettaX.utils.io import column_copy


def read_peak_event_columns(
    *, fcs_file_path: str, detector_columns: tuple[str, ...], max_events: int | None,
    read_column: Callable = column_copy,
) -> tuple[np.ndarray, ...]:
    """Read the same prefix of events from each requested detector column.

    Returns
    -------
    tuple of ndarray
        One 1D float array per detector, in the supplied order.
    """
    return tuple(
        np.asarray(
            read_column(fcs_file_path=fcs_file_path, detector_column=str(detector_column), dtype=float, n=max_events),
            dtype=float,
        ).reshape(-1)
        for detector_column in detector_columns
    )


def filter_finite_peak_events(*, columns: tuple[np.ndarray, ...]) -> tuple[tuple[np.ndarray, ...], int]:
    """Filter out rows with non-finite values in any requested detector.

    Returns
    -------
    tuple of ndarray, int
        Aligned detector columns and the number of removed events.
    """
    if not columns:
        return (), 0
    event_count = columns[0].size
    if any(column.shape != (event_count,) for column in columns):
        raise ValueError("Detector columns must contain the same number of paired FCS events.")

    finite_mask = np.isfinite(columns[0])
    for column in columns[1:]:
        finite_mask &= np.isfinite(column)
    removed_count = event_count - int(np.count_nonzero(finite_mask))
    if removed_count == 0:
        return columns, 0

    return tuple(column[finite_mask] for column in columns), removed_count
