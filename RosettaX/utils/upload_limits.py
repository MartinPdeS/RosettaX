# -*- coding: utf-8 -*-

import argparse
import re
from typing import Any


DEFAULT_MAX_UPLOAD_BYTES = 2 * 1024**3

_configured_max_upload_bytes = DEFAULT_MAX_UPLOAD_BYTES

_DECIMAL_MULTIPLIERS = {
    "B": 1,
    "KB": 1024,
    "MB": 1024**2,
    "GB": 1024**3,
    "TB": 1024**4,
    "KIB": 1024,
    "MIB": 1024**2,
    "GIB": 1024**3,
    "TIB": 1024**4,
}


def parse_upload_size_bytes(
    value: Any,
) -> int:
    """
    Parse a human readable upload size into bytes.

    Examples
    --------
    1048576, "10MB", "10 MiB", "512KB"
    """
    if value is None:
        return DEFAULT_MAX_UPLOAD_BYTES

    if isinstance(value, bool):
        raise ValueError("Upload size must be a positive byte value.")

    if isinstance(value, int):
        resolved_bytes = int(value)

    else:
        text = str(value).strip()

        if not text:
            raise ValueError("Upload size cannot be empty.")

        normalized = text.upper().replace(" ", "")
        match = re.fullmatch(r"(\d+(?:\.\d+)?)([A-Z]+)?", normalized)

        if match is None:
            raise ValueError(
                "Upload size must look like 1048576, 10MB, 10 MiB, or 1GB."
            )

        number_text, unit_text = match.groups()
        unit = unit_text or "B"

        if unit not in _DECIMAL_MULTIPLIERS:
            raise ValueError(
                f"Unsupported upload size unit {unit!r}. Use B, KB, MB, or GB."
            )

        resolved_bytes = int(float(number_text) * _DECIMAL_MULTIPLIERS[unit])

    if resolved_bytes <= 0:
        raise ValueError("Upload size must be greater than zero bytes.")

    return resolved_bytes


def parse_upload_size_argument(
    value: str,
) -> int:
    """
    argparse compatible parser for the max upload size CLI option.
    """
    try:
        return parse_upload_size_bytes(value)

    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def configure_max_upload_bytes(
    max_upload_bytes: Any,
) -> int:
    """
    Configure the process wide upload size cap.
    """
    global _configured_max_upload_bytes

    _configured_max_upload_bytes = parse_upload_size_bytes(max_upload_bytes)

    return _configured_max_upload_bytes


def get_max_upload_bytes() -> int:
    """
    Return the configured process wide upload size cap.
    """
    return int(_configured_max_upload_bytes)


def format_upload_size(
    max_upload_bytes: Any = None,
) -> str:
    """
    Format a byte count into a compact human readable string.
    """
    resolved_bytes = (
        get_max_upload_bytes()
        if max_upload_bytes is None
        else parse_upload_size_bytes(max_upload_bytes)
    )

    for unit_name, unit_bytes in (
        ("TiB", 1024**4),
        ("GiB", 1024**3),
        ("MiB", 1024**2),
        ("KiB", 1024),
    ):
        if resolved_bytes >= unit_bytes:
            value = resolved_bytes / unit_bytes

            if float(value).is_integer():
                return f"{int(value)} {unit_name}"

            return f"{value:.1f} {unit_name}"

    return f"{resolved_bytes} B"
