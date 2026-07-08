# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash

from RosettaX.utils import service
from RosettaX.workflow.save.models import SaveConfig
from RosettaX.workflow.save.models import SaveInputs
from RosettaX.workflow.save.models import SaveResult


def validate_save_inputs(
    *,
    file_name: str | None,
    output_channel_name: str | None,
    calibration_payload: dict | None,
    require_output_channel_name: bool = False,
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
    clean_output_channel_name = (
        ""
        if output_channel_name is None
        else str(output_channel_name).strip()
    )

    if not clean_file_name:
        return (
            None,
            "Enter a calibration name before saving.",
        )

    if require_output_channel_name and not clean_output_channel_name:
        return (
            None,
            "Enter an applied output channel name before saving.",
        )

    if not isinstance(calibration_payload, dict) or not calibration_payload:
        return (
            None,
            "Create a calibration before saving.",
        )

    return (
        SaveInputs(
            file_name=clean_file_name,
            output_channel_name=clean_output_channel_name,
            calibration_payload=dict(calibration_payload),
        ),
        None,
    )


def save_calibration_payload(
    *,
    inputs: SaveInputs,
    config: SaveConfig,
    logger: logging.Logger,
) -> SaveResult:
    """
    Build a calibration download payload.
    """
    file_name = service.build_calibration_download_filename(
        name=inputs.file_name,
    )
    calibration_payload = dict(inputs.calibration_payload)

    if inputs.output_channel_name:
        calibration_payload["applied_output_channel_name"] = inputs.output_channel_name

    json_text = service.serialize_calibration_record(
        name=inputs.file_name,
        payload=calibration_payload,
        calibration_kind=config.calibration_kind,
    )

    logger.debug(
        "save_calibration_payload called with calibration_kind=%r "
        "file_name=%r payload_keys=%r download_filename=%r",
        config.calibration_kind,
        inputs.file_name,
        list(calibration_payload.keys()),
        file_name,
    )

    logger.debug(
        "save_calibration_payload prepared download successfully filename=%r",
        file_name,
    )

    return SaveResult(
        save_out=f'{config.saved_message_prefix} "{file_name}".',
        download_data=dash.dcc.send_string(
            json_text,
            file_name,
        ),
    )


def run_save_workflow(
    *,
    file_name: str | None,
    output_channel_name: str | None,
    calibration_payload: dict | None,
    config: SaveConfig,
    logger: logging.Logger,
) -> SaveResult:
    """
    Run the reusable calibration save workflow.
    """
    parsed_inputs, validation_error = validate_save_inputs(
        file_name=file_name,
        output_channel_name=output_channel_name,
        calibration_payload=calibration_payload,
        require_output_channel_name=config.require_output_channel_name,
    )

    if validation_error is not None:
        logger.debug(
            "run_save_workflow validation failed with message=%r",
            validation_error,
        )

        return SaveResult(
            save_out=validation_error,
            download_data=dash.no_update,
        )

    if parsed_inputs is None:
        logger.debug(
            "run_save_workflow failed because parsed_inputs is None."
        )

        return SaveResult(
            save_out="Could not parse save inputs.",
            download_data=dash.no_update,
        )

    try:
        return save_calibration_payload(
            inputs=parsed_inputs,
            config=config,
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
            download_data=dash.no_update,
        )
