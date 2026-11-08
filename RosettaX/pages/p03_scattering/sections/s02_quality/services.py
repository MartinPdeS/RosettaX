"""Inspect selected FCS channels and summarize calibration readiness."""

import numpy as np
from RosettaX.utils.reader import FCSFile


def inspect_channels(*, file_path: str, channels: list[str], max_events: int = 100_000) -> dict:
    """Inspect the first events in selected channels and their detector ranges.

    Parameters
    ----------
    file_path : str
        Path to the FCS file.
    channels : list[str]
        Detector column names to inspect.
    max_events : int
        Maximum number of events read per channel.

    Returns
    -------
    dict
        Total event count and per-channel counts for the inspected sample.
    """
    with FCSFile(file_path) as fcs:
        detectors = fcs.get_metadata().detectors.values()
        ranges = {str(detector.get("N", "")): detector.get("R") for detector in detectors}
        results = []
        for channel in dict.fromkeys(channels):
            values = fcs.column_copy(channel, dtype=float, n=max_events)
            finite = np.isfinite(values)
            try:
                detector_range = float(ranges.get(channel))
                if not np.isfinite(detector_range) or detector_range <= 0:
                    detector_range = None
            except (TypeError, ValueError):
                detector_range = None
            results.append({
                "channel": channel,
                "count": int(values.size),
                "nonfinite": int(np.count_nonzero(~finite)),
                "zero": int(np.count_nonzero(finite & (values == 0))),
                "negative": int(np.count_nonzero(finite & (values < 0))),
                "range": detector_range,
                "at_range": int(np.count_nonzero(finite & (values >= detector_range - 1))) if detector_range is not None else None,
            })
        return {"total_events": fcs.text.get("Keywords", {}).get("$TOT"), "channels": results}


def count_measured_peaks(*, table_data: list | None) -> int:
    """Count finite positive measured peak positions in the calibration table."""
    count = 0
    for row in table_data or []:
        if not isinstance(row, dict):
            continue
        try:
            value = float(row.get("measured_peak_position"))
        except (TypeError, ValueError):
            continue
        count += int(np.isfinite(value) and value > 0)
    return count


def status_text(*, value: object) -> str:
    """Extract the text from a serialized Dash status component."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return status_text(value=value.get("props", {}).get("children"))
    if isinstance(value, list):
        return "\n".join(text for item in value if (text := status_text(value=item)))
    return ""
