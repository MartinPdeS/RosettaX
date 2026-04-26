from typing import Optional, Any

import numpy as np
from RosettaX.utils.reader import FCSFile
import logging


logger = logging.getLogger(__name__)


def load_signal(
    fcs_file_path: str,
    detector_column: str,
    max_events_for_analysis: Optional[int] = None,
    require_positive_values: bool = False,
) -> np.ndarray:
    """
    Load a detector signal from the FCS file.
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

    with FCSFile(fcs_file_path, writable=False) as fcs_file:
        signal = fcs_file.column_copy(resolved_detector_column, dtype=float)

    signal = np.asarray(signal, dtype=float).reshape(-1)
    signal = signal[np.isfinite(signal)]

    if require_positive_values:
        signal = signal[signal > 0.0]

    if max_events_for_analysis is not None:
        signal = signal[: int(max_events_for_analysis)]

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
    n: Optional[int] = None,
) -> np.ndarray:
    """
    Return an owned copy of a detector column.

    This method matches the minimal file reader interface expected by the shared
    peak workflow graph code. It delegates to ``load_signal`` so all FCS reading
    remains centralized in this backend.
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
    Return detector column names from the FCS file.
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