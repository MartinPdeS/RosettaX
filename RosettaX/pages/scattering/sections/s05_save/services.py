# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

from RosettaX.utils import directories, service


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaveResult:
    """
    Result returned by the scattering save service.

    This object is intentionally independent from Dash. The callback decides
    whether None should become dash.no_update.
    """

    save_out: str
    sidebar_refresh_store: Optional[dict[str, Any]] = None

    def to_tuple(self) -> tuple[str, Optional[dict[str, Any]]]:
        """
        Convert the save result to the callback output shape.

        Returns
        -------
        tuple[str, Optional[dict[str, Any]]]
            Save status message and optional sidebar refresh payload.
        """
        return (
            self.save_out,
            self.sidebar_refresh_store,
        )


@dataclass(frozen=True)
class SaveInputs:
    """
    Parsed inputs required to save a calibration file.
    """

    file_name: str
    calib_payload: dict[str, Any]


def normalize_file_name(file_name: Any) -> str:
    """
    Normalize the requested calibration file name.

    Parameters
    ----------
    file_name:
        Raw file name value.

    Returns
    -------
    str
        Cleaned file name.
    """
    return str(file_name or "").strip()


def validate_save_inputs(
    *,
    file_name: Any,
    calib_payload: Optional[dict[str, Any]],
) -> tuple[Optional[SaveInputs], Optional[str]]:
    """
    Validate save inputs before writing a calibration file.

    Parameters
    ----------
    file_name:
        Raw calibration file name.

    calib_payload:
        Calibration payload to save.

    Returns
    -------
    tuple[Optional[SaveInputs], Optional[str]]
        Parsed inputs and validation error. Exactly one should be non None.
    """
    if not isinstance(calib_payload, dict) or not calib_payload:
        return None, "No calibration payload available. Run the calibration first."

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


def build_sidebar_refresh_payload(
    *,
    saved_folder: Any,
    saved_filename: Any,
) -> dict[str, Any]:
    """
    Build the sidebar refresh payload after saving a calibration.

    Parameters
    ----------
    saved_folder:
        Folder where the calibration was saved.

    saved_filename:
        Saved calibration filename.

    Returns
    -------
    dict[str, Any]
        Sidebar refresh payload.
    """
    return {
        "refresh": True,
        "folder": str(saved_folder),
        "filename": str(saved_filename),
        "kind": "scattering",
    }


def action_save_calibration(
    *,
    inputs: SaveInputs,
) -> SaveResult:
    """
    Save the current scattering calibration payload to disk.

    Parameters
    ----------
    inputs:
        Validated save inputs.

    Returns
    -------
    SaveResult
        Save result and sidebar refresh payload.
    """
    logger.debug(
        "action_save_calibration called with file_name=%r payload_keys=%r",
        inputs.file_name,
        list(inputs.calib_payload.keys()),
    )

    try:
        saved = service.save_calibration_to_file(
            name=inputs.file_name,
            payload=dict(inputs.calib_payload),
            calibration_kind="scattering",
            output_directory=directories.scattering_calibration,
        )

    except Exception:
        logger.exception(
            "action_save_calibration failed for file_name=%r payload_keys=%r",
            inputs.file_name,
            list(inputs.calib_payload.keys()),
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
        save_out=(
            f'Saved calibration "{inputs.file_name}" '
            f"as {saved.folder}/{saved.filename}"
        ),
        sidebar_refresh_store=sidebar_refresh_payload,
    )