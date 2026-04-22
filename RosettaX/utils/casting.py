from typing import Any, Optional
import numpy as np
import re


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


def _as_float_list(value: Any) -> np.ndarray:
    """
    Parse a value into a 1D NumPy array of finite floats.

    Accepted inputs
    ---------------
    - list, tuple, or ndarray of numeric like values
    - string with values separated by commas, semicolons, or whitespace

    Examples
    --------
    "100, 200, 300" -> array([100., 200., 300.])
    "100;200;300"   -> array([100., 200., 300.])
    "100 200 300"   -> array([100., 200., 300.])

    Parameters
    ----------
    value : Any
        Candidate value from UI components.

    Returns
    -------
    np.ndarray
        1D array of finite floats. Invalid entries are ignored.
    """
    if value is None:
        return np.asarray([], dtype=float)

    if isinstance(value, np.ndarray):
        raw_values = value.reshape(-1).tolist()
    elif isinstance(value, (list, tuple)):
        raw_values = list(value)
    elif isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return np.asarray([], dtype=float)

        normalized_value = stripped_value.replace(";", ",")
        raw_values = [
            part.strip()
            for part in re.split(r"[,\s]+", normalized_value)
            if part.strip()
        ]
    else:
        raw_values = [value]

    parsed_values: list[float] = []

    for raw_value in raw_values:
        parsed_value = _as_float(raw_value)
        if parsed_value is None:
            continue
        parsed_values.append(float(parsed_value))

    return np.asarray(parsed_values, dtype=float)

def as_required_float(value: Any, field_name: str) -> float:
    try:
        if value in (None, ""):
            raise ValueError
        return float(value)
    except Exception as exc:
        raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc

def as_required_int(value: Any, field_name: str) -> int:
    try:
        if value in (None, ""):
            raise ValueError
        return int(value)
    except Exception as exc:
        raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc

def as_optional_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None