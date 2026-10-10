import logging
from collections import OrderedDict
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np

from RosettaX.utils.reader import FCSFile

logger = logging.getLogger(__name__)

# Store owned arrays only; readers and their memory mappings always close.
_SIGNAL_CACHE_MAX_BYTES = 32 * 1024 * 1024
_SIGNAL_CACHE_MAX_ENTRIES = 16
_signal_cache: OrderedDict[tuple[Any, ...], np.ndarray] = OrderedDict()
_signal_cache_lock = RLock()


def _signal_cache_key(
    file_path: Path,
    detector_column: str,
    max_events_for_analysis: int | None,
    require_positive_values: bool,
) -> tuple[Any, ...]:
    file_stat = file_path.stat()
    return (
        str(file_path),
        file_stat.st_dev,
        file_stat.st_ino,
        file_stat.st_size,
        file_stat.st_mtime_ns,
        file_stat.st_ctime_ns,
        detector_column,
        max_events_for_analysis,
        require_positive_values,
    )


def load_signal(
    fcs_file_path: str,
    detector_column: str,
    max_events_for_analysis: int | None = None,
    require_positive_values: bool = False,
) -> np.ndarray:
    """
    Load a detector signal from an FCS file.

    Reads all events for the requested detector column, strips non-finite
    values, and optionally filters out non-positive values and truncates to a
    maximum event count.

    Parameters
    ----------
    fcs_file_path : str
        Absolute or relative path to the FCS file.
    detector_column : str
        Name of the detector column to read.
    max_events_for_analysis : Optional[int]
        If provided, only the first *max_events_for_analysis* events are
        returned after filtering.
    require_positive_values : bool
        If ``True``, events with a value of zero or below are removed.

    Returns
    -------
    np.ndarray
        1D array of finite (and optionally positive) float values.

    Raises
    ------
    ValueError
        If *detector_column* is empty.
    """
    resolved_detector_column = str(detector_column).strip()

    if not resolved_detector_column:
        raise ValueError("detector_column must be a non empty string.")

    logger.debug(
        "load_signal called with detector_column=%r max_events_for_analysis=%r require_positive_values=%r",
        resolved_detector_column,
        max_events_for_analysis,
        require_positive_values,
    )

    file_path = Path(fcs_file_path).resolve()
    cache_key = _signal_cache_key(
        file_path,
        resolved_detector_column,
        None if max_events_for_analysis is None else int(max_events_for_analysis),
        require_positive_values,
    )
    with _signal_cache_lock:
        cached_signal = _signal_cache.get(cache_key)
        if cached_signal is not None:
            _signal_cache.move_to_end(cache_key)
            return cached_signal.copy()

    with FCSFile(file_path, writable=False) as fcs_file:
        signal = fcs_file.column_copy(resolved_detector_column, dtype=float)

    signal = np.asarray(signal, dtype=float).reshape(-1)
    signal = signal[np.isfinite(signal)]

    if require_positive_values:
        signal = signal[signal > 0.0]

    if max_events_for_analysis is not None:
        signal = signal[: int(max_events_for_analysis)]

    # A replacement during reading must never be cached under the old identity.
    try:
        unchanged = cache_key == _signal_cache_key(
            file_path,
            resolved_detector_column,
            None if max_events_for_analysis is None else int(max_events_for_analysis),
            require_positive_values,
        )
    except OSError:
        unchanged = False
    if unchanged and signal.nbytes <= _SIGNAL_CACHE_MAX_BYTES:
        cached_signal = signal.copy()
        cached_signal.setflags(write=False)
        with _signal_cache_lock:
            _signal_cache[cache_key] = cached_signal
            _signal_cache.move_to_end(cache_key)
            while (
                len(_signal_cache) > _SIGNAL_CACHE_MAX_ENTRIES
                or sum(value.nbytes for value in _signal_cache.values())
                > _SIGNAL_CACHE_MAX_BYTES
            ):
                _signal_cache.popitem(last=False)

    logger.debug(
        "load_signal returning detector_column=%r n_values=%r min=%r max=%r",
        resolved_detector_column,
        signal.size,
        None if signal.size == 0 else float(np.min(signal)),
        None if signal.size == 0 else float(np.max(signal)),
    )

    return signal

def column_copy(
    fcs_file_path: str,
    detector_column: str,
    *,
    dtype: Any = float,
    n: int | None = None,
) -> np.ndarray:
    """
    Return an owned copy of a detector column from an FCS file.

    This function matches the minimal file-reader interface expected by the
    shared peak-workflow graph code.  It delegates to :func:`load_signal` so
    that all FCS reading remains centralised in one place.

    Parameters
    ----------
    fcs_file_path : str
        Absolute or relative path to the FCS file.
    detector_column : str
        Name of the detector column to read.
    dtype : type
        NumPy dtype to cast the values to.  Defaults to ``float``.
    n : Optional[int]
        If provided, only the first *n* events are returned.

    Returns
    -------
    np.ndarray
        1D array of values cast to *dtype*.
    """
    values = load_signal(
        fcs_file_path=fcs_file_path,
        detector_column=detector_column,
        max_events_for_analysis=n,
        require_positive_values=False,
    )

    return np.asarray(
        values,
        dtype=dtype,
    ).copy()


def get_column_names(fcs_file_path: str) -> list[str]:
    """
    Return detector column names from an FCS file.

    The names are read from the ``$PnN`` keywords in the TEXT segment and
    returned in parameter order.  If a parameter has no name keyword, a
    fallback of the form ``P{index}`` is used.

    Parameters
    ----------
    fcs_file_path : str
        Absolute or relative path to the FCS file.

    Returns
    -------
    list[str]
        Ordered list of detector column names.
    """
    logger.debug("get_column_names called for fcs_file_path=%r", fcs_file_path)

    with FCSFile(fcs_file_path, writable=False) as fcs_file:
        detectors = fcs_file.text["Detectors"]
        parameter_count = int(fcs_file.text["Keywords"]["$PAR"])

        column_names = [
            str(detectors[index].get("N", f"P{index}"))
            for index in range(1, parameter_count + 1)
        ]

    logger.debug("get_column_names returning n_columns=%r", len(column_names))

    return column_names
