from typing import Any, Optional
import numpy as np

def _as_float(value: Any) -> Optional[float]:
    """
    Parse a value into a finite float.

    Parameters
    ----------
    value : Any
        Candidate value from UI components.

    Returns
    -------
    Optional[float]
        Parsed float if valid and finite, otherwise None.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        v = float(value)
        return v if np.isfinite(v) else None

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        s = s.replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return None
        return v if np.isfinite(v) else None

    return None


def _as_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    """
    Parse a value into an int, falling back to a default and clamping within bounds.

    Parameters
    ----------
    value : Any
        Candidate numeric input.
    default : int
        Default value used when parsing fails.
    min_value : int
        Minimum allowed value.
    max_value : int
        Maximum allowed value.

    Returns
    -------
    int
        Parsed and clamped integer.
    """
    try:
        v = int(value)
    except Exception:
        v = default

    if v < min_value:
        v = min_value
    if v > max_value:
        v = max_value

    return v