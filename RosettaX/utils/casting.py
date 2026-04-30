from typing import Any, Optional
import numpy as np
import re


def as_float(value: Any) -> Optional[float]:
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


def as_int(value: Any, default: int, min_value: int, max_value: int) -> int:
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


def as_float_list(value: Any) -> np.ndarray:
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
        parsed_value = as_float(raw_value)
        if parsed_value is None:
            continue
        parsed_values.append(float(parsed_value))

    return np.asarray(parsed_values, dtype=float)


def as_required_float(value: Any, field_name: str) -> float:
    """
    Parse a value into a float, raising ``ValueError`` if parsing fails.

    Parameters
    ----------
    value : Any
        Candidate value to convert.
    field_name : str
        Human-readable name of the field, used in the error message.

    Returns
    -------
    float
        Parsed float value.

    Raises
    ------
    ValueError
        If the value is ``None``, an empty string, or cannot be converted.
    """
    if value in (None, ""):
        raise ValueError(f"Invalid value for {field_name}: {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc


def as_required_int(value: Any, field_name: str) -> int:
    """
    Parse a value into an int, raising ``ValueError`` if parsing fails.

    Parameters
    ----------
    value : Any
        Candidate value to convert.
    field_name : str
        Human-readable name of the field, used in the error message.

    Returns
    -------
    int
        Parsed integer value.

    Raises
    ------
    ValueError
        If the value is ``None``, an empty string, or cannot be converted.
    """
    if value in (None, ""):
        raise ValueError(f"Invalid value for {field_name}: {value!r}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc


def as_optional_float(value: Any) -> Optional[float]:
    """
    Parse a value into a float, returning ``None`` when parsing fails.

    Parameters
    ----------
    value : Any
        Candidate value to convert.

    Returns
    -------
    Optional[float]
        Parsed float, or ``None`` if the value is ``None``, empty, or invalid.
    """
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def as_optional_int(value: Any) -> Optional[int]:
    """
    Parse a value into an int, returning ``None`` when parsing fails.

    Parameters
    ----------
    value : Any
        Candidate value to convert.

    Returns
    -------
    Optional[int]
        Parsed integer, or ``None`` if the value is ``None``, empty, or invalid.
    """
    try:
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        return None


def parse_float_list(value: Any) -> list[float]:
    """
    Parse a value into a plain Python list of floats.

    Delegates to :func:`as_float_list` and converts the resulting NumPy array
    into a native Python list.

    Parameters
    ----------
    value : Any
        Candidate value accepted by :func:`as_float_list`.

    Returns
    -------
    list[float]
        List of finite floats parsed from *value*.
    """
    parsed_values = as_float_list(value)
    return [float(item) for item in parsed_values.tolist()]


def coerce_optional_number(value: Any) -> Optional[float]:
    """
    Coerce a value to ``float``, returning ``None`` for invalid input.

    Unlike :func:`as_optional_float`, this delegates to :func:`as_float` so
    that comma-separated strings and other normalisation rules are applied.

    Parameters
    ----------
    value : Any
        Candidate value to coerce.

    Returns
    -------
    Optional[float]
        Coerced float, or ``None`` if the value cannot be parsed.
    """
    parsed_value = as_float(value)
    if parsed_value is None:
        return None
    return float(parsed_value)

def coerce_optional_integer(value: Any) -> Optional[int]:
    """
    Coerce a value to ``int``, returning ``None`` for invalid input.

    The value is first parsed as a float via :func:`as_float` and then
    truncated to an integer so that floating point strings such as ``"3.0"``
    are accepted.

    Parameters
    ----------
    value : Any
        Candidate value to coerce.

    Returns
    -------
    Optional[int]
        Coerced integer, or ``None`` if the value cannot be parsed.
    """
    parsed_value = as_float(value)
    if parsed_value is None:
        return None
    return int(parsed_value)


def coerce_optional_string(value: Any) -> Optional[str]:
    """
    Coerce a value to a non-empty stripped string, returning ``None`` otherwise.

    Parameters
    ----------
    value : Any
        Candidate value to coerce.

    Returns
    -------
    Optional[str]
        Stripped string if non-empty, or ``None`` for ``None`` input or
        blank strings.
    """
    if value is None:
        return None
    resolved_value = str(value).strip()
    return resolved_value if resolved_value else None


def format_float_list_for_input(value: Any) -> str:
    """
    Format a list of floats as a comma-separated string for UI input fields.

    The output uses ``:.6g`` formatting so that each number is rendered with
    up to six significant figures without trailing zeros.

    Parameters
    ----------
    value : Any
        Candidate value accepted by :func:`as_float_list`.

    Returns
    -------
    str
        Comma-separated string, or an empty string when no valid values are
        found.

    Examples
    --------
    >>> format_float_list_for_input([100, 200, 300])
    '100, 200, 300'
    """
    parsed_values = as_float_list(value)

    if parsed_values.size == 0:
        return ""

    return ", ".join(f"{float(item):.6g}" for item in parsed_values)


