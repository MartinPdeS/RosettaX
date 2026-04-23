# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
from RosettaX.utils import service, directories
import logging

import dash

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SaveResult:
    """
    Container for all Dash outputs of the Save callback.
    """

    save_out: Any = dash.no_update
    sidebar_refresh_store: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (
            self.save_out,
            self.sidebar_refresh_store,
        )


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

def action_save_calibration(self, *, inputs: SaveInputs) -> SaveResult:
    """
    Save the current calibration payload to disk.
    """
    logger.debug(
        "_action_save_calibration called with file_name=%r payload_keys=%r",
        inputs.file_name,
        list(inputs.calib_payload.keys()) if isinstance(inputs.calib_payload, dict) else None,
    )

    try:
        saved = service.save_calibration_to_file(
            name=inputs.file_name,
            payload=dict(inputs.calib_payload or {}),
            calibration_kind="scattering",
            output_directory=directories.scattering_calibration,
        )
    except Exception:
        logger.exception(
            "_action_save_calibration failed for file_name=%r payload_keys=%r",
            inputs.file_name,
            list(inputs.calib_payload.keys()) if isinstance(inputs.calib_payload, dict) else None,
        )
        raise

    logger.debug(
        "Calibration saved successfully to folder=%r filename=%r",
        saved.folder,
        saved.filename,
    )

    sidebar_refresh_payload = build_sidebar_refresh_payload(
        saved_folder=saved.folder,
        saved_filename=saved.filename,
    )

    return SaveResult(
        save_out=f'Saved calibration "{inputs.file_name}" as {saved.folder}/{saved.filename}',
        sidebar_refresh_store=sidebar_refresh_payload,
    )