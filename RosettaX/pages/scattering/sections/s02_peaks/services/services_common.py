# -*- coding: utf-8 -*-

from typing import Any


def clean_optional_string(value: Any) -> str:
    """
    Convert an optional value into a stripped string.

    Parameters
    ----------
    value:
        Raw value.

    Returns
    -------
    str
        Empty string for None or blank values, otherwise stripped string.
    """
    if value is None:
        return ""

    cleaned_value = str(value).strip()

    if not cleaned_value:
        return ""

    if cleaned_value.lower() == "none":
        return ""

    return cleaned_value


def is_enabled(value: Any) -> bool:
    """
    Return whether a Dash checklist value contains enabled.

    Parameters
    ----------
    value:
        Dash checklist value.

    Returns
    -------
    bool
        True if the value is a list containing enabled.
    """
    return isinstance(value, list) and "enabled" in value


def resolve_mie_model(mie_model: Any) -> str:
    """
    Resolve the Mie model name used by the calibration reference table.

    Parameters
    ----------
    mie_model:
        Raw Mie model value.

    Returns
    -------
    str
        Canonical Mie model name.
    """
    mie_model_string = clean_optional_string(
        mie_model,
    )

    if mie_model_string == "Core/Shell Sphere":
        return "Core/Shell Sphere"

    return "Solid Sphere"