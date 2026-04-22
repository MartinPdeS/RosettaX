# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SaveInputs:
    file_name: str
    calib_payload: Optional[dict]


def normalize_file_name(file_name: Any) -> str:
    return str(file_name or "").strip()


def validate_save_inputs(
    *,
    file_name: Any,
    calib_payload: Optional[dict],
) -> tuple[Optional[SaveInputs], Optional[str]]:
    if not isinstance(calib_payload, dict) or not calib_payload:
        return None, "No calibration payload available. Run Calibrate first."

    file_name_clean = normalize_file_name(file_name)

    if not file_name_clean:
        return None, "Please provide a calibration name."

    return SaveInputs(
        file_name=file_name_clean,
        calib_payload=calib_payload,
    ), None


def compute_next_sidebar_refresh_signal(current_sidebar_refresh_signal: Any) -> int:
    if current_sidebar_refresh_signal is None:
        return 1

    return int(current_sidebar_refresh_signal) + 1