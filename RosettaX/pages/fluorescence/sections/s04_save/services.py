# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import dash


@dataclass(frozen=True)
class SaveResult:
    """
    Container for all Dash outputs of the Save callback.
    """

    save_out: Any = dash.no_update
    sidebar_refresh_signal: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.save_out,
            self.sidebar_refresh_signal,
        )


@dataclass(frozen=True)
class SaveInputs:
    """
    Parsed inputs required to save a fluorescence calibration file.
    """

    file_name: str
    calib_payload: dict


def normalize_file_name(file_name: Any) -> str:
    """
    Normalize the requested calibration file name.
    """
    return str(file_name or "").strip()


def validate_save_inputs(
    *,
    file_name: Any,
    calib_payload: Optional[dict],
) -> tuple[Optional[SaveInputs], Optional[str]]:
    """
    Validate save inputs before writing a fluorescence calibration file.
    """
    if not isinstance(calib_payload, dict) or not calib_payload:
        return None, "No calibration payload available. Run Calibrate first."

    file_name_clean = normalize_file_name(
        file_name,
    )

    if not file_name_clean:
        return None, "Please provide a calibration name."

    return (
        SaveInputs(
            file_name=file_name_clean,
            calib_payload=calib_payload,
        ),
        None,
    )


def compute_next_sidebar_refresh_signal(
    current_sidebar_refresh_signal: Any,
) -> int:
    """
    Increment the sidebar refresh signal.

    Non integer values are treated as no previous signal.
    """
    try:
        return int(current_sidebar_refresh_signal) + 1
    except (TypeError, ValueError):
        return 1