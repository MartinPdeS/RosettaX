# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash

from RosettaX.utils import service
from .models import SaveConfig, SaveInputs, SaveResult

def validate_save_inputs(
    *,
    file_name: str | None,
    calibration_payload: dict | None,
) -> tuple[SaveInputs | None, str | None]:
    """
    Validate the save workflow inputs.

    Parameters
    ----------
    file_name:
        Requested calibration file name.

    calibration_payload:
        Calibration payload to save.

    Returns
    -------
    tuple[SaveInputs | None, str | None]
        Validated inputs and optional validation error.
    """
    clean_file_name = "" if file_name is None else str(file_name).strip()

    if not clean_file_name:
        return (
            None,
            "Enter a calibration name before saving.",
        )

    if not isinstance(calibration_payload, dict) or not calibration_payload:
        return (
            None,
            "Create a calibration before saving.",
        )

    return (
        SaveInputs(
            file_name=clean_file_name,
            calibration_payload=dict(calibration_payload),
        ),
        None,
    )


def compute_next_sidebar_refresh_signal(
    *,
    current_sidebar_refresh_signal: Any,
) -> int:
    """
    Compute the next sidebar refresh signal.
    """
    try:
        current_value = int(
            current_sidebar_refresh_signal or 0
        )
    except (TypeError, ValueError):
        current_value = 0

    return current_value + 1


def save_calibration_payload(
    *,
    inputs: SaveInputs,
    config: SaveConfig,
    current_sidebar_refresh_signal: Any,
    logger: logging.Logger,
) -> SaveResult:
    """
    Save a calibration payload to disk.
    """
    logger.debug(
        "save_calibration_payload called with calibration_kind=%r "
        "file_name=%r payload_keys=%r output_directory=%r",
        config.calibration_kind,
        inputs.file_name,
        list(inputs.calibration_payload.keys()),
        config.output_directory,
    )

    saved = service.save_calibration_to_file(
        name=inputs.file_name,
        payload=dict(inputs.calibration_payload),
        calibration_kind=config.calibration_kind,
        output_directory=config.output_directory,
    )

    logger.debug(
        "save_calibration_payload saved successfully to folder=%r filename=%r",
        saved.folder,
        saved.filename,
    )

    next_sidebar_refresh_signal = compute_next_sidebar_refresh_signal(
        current_sidebar_refresh_signal=current_sidebar_refresh_signal,
    )

    return SaveResult(
        save_out=(
            f'{config.saved_message_prefix} "{inputs.file_name}" '
            f"as {saved.folder}/{saved.filename}"
        ),
        sidebar_refresh_signal=next_sidebar_refresh_signal,
    )


def run_save_workflow(
    *,
    file_name: str | None,
    calibration_payload: dict | None,
    current_sidebar_refresh_signal: Any,
    config: SaveConfig,
    logger: logging.Logger,
) -> SaveResult:
    """
    Run the reusable calibration save workflow.
    """
    parsed_inputs, validation_error = validate_save_inputs(
        file_name=file_name,
        calibration_payload=calibration_payload,
    )

    if validation_error is not None:
        logger.debug(
            "run_save_workflow validation failed with message=%r",
            validation_error,
        )

        return SaveResult(
            save_out=validation_error,
            sidebar_refresh_signal=dash.no_update,
        )

    if parsed_inputs is None:
        logger.debug(
            "run_save_workflow failed because parsed_inputs is None."
        )

        return SaveResult(
            save_out="Could not parse save inputs.",
            sidebar_refresh_signal=dash.no_update,
        )

    try:
        return save_calibration_payload(
            inputs=parsed_inputs,
            config=config,
            current_sidebar_refresh_signal=current_sidebar_refresh_signal,
            logger=logger,
        )
    except Exception:
        logger.exception(
            "Failed to save calibration with calibration_kind=%r file_name=%r "
            "payload_keys=%r",
            config.calibration_kind,
            parsed_inputs.file_name,
            list(parsed_inputs.calibration_payload.keys()),
        )

        return SaveResult(
            save_out=config.failure_message,
            sidebar_refresh_signal=dash.no_update,
        )