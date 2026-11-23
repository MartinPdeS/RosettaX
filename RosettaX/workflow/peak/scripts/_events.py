"""Read and filter detector columns while preserving FCS event alignment."""

import numpy as np
from RosettaX.utils.io import load_signal
from RosettaX.utils.reader import FCSFile


def read_peak_event_columns(
    *, fcs_file_path: str, detector_columns: tuple[str, ...], max_events: int | None,
) -> tuple[np.ndarray, ...]:
    """Read aligned raw events for paired channels or a finite single-channel signal.

    Returns
    -------
    tuple of ndarray
        One 1D float array per detector, in the supplied order.
    """
    if not detector_columns:
        return ()
    if len(detector_columns) == 1:
        return (load_signal(fcs_file_path, detector_columns[0], max_events),)

    # Keep invalid values in place until the joint event mask is available.
    with FCSFile(fcs_file_path) as reader:
        return tuple(reader.column_copy(name, n=max_events) for name in detector_columns)


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
