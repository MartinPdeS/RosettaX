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
        return None, "No calibration payload available. Run the calibration first."

    file_name_clean = normalize_file_name(file_name)

    if not file_name_clean:
        return None, "Please provide a calibration name."

    return SaveInputs(
        file_name=file_name_clean,
        calib_payload=calib_payload,
    ), None


def build_sidebar_refresh_payload(
    *,
    saved_folder: Any,
    saved_filename: Any,
) -> dict[str, Any]:
    return {
        "refresh": True,
        "folder": str(saved_folder),
        "filename": str(saved_filename),
        "kind": "scattering",
    }