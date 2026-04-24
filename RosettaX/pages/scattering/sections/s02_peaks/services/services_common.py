# -*- coding: utf-8 -*-

from typing import Any


def clean_optional_string(value: Any) -> str:
    """
    Convert an optional value into a stripped string.
    """
    if value is None:
        return ""

    return str(value).strip()


def is_enabled(value: Any) -> bool:
    """
    Return True when a Dash checklist value contains enabled.
    """
    return isinstance(value, list) and "enabled" in value


def resolve_mie_model(mie_model: Any) -> str:
    """
    Resolve the Mie model name used by the calibration reference table.
    """
    mie_model_string = clean_optional_string(mie_model)

    if mie_model_string == "Core/Shell Sphere":
        return "Core/Shell Sphere"

    return "Solid Sphere"