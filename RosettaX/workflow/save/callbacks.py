# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash

from . import services
from .adapters import SaveAdapter
from .models import SaveConfig


def save_button_should_be_disabled(
    file_name: Any,
) -> bool:
    """
    Return whether the save button should be disabled.
    """
    return not bool(str(file_name or "").strip())


def register_save_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: SaveAdapter,
    config: SaveConfig,
    logger: logging.Logger,
    calibration_store_id: Any = None,
    page_state_store_id: Any = None,
) -> None:
    """
    Register reusable save callbacks.
    """
    logger.debug(
        "Registering reusable save callbacks for calibration_kind=%r",
        config.calibration_kind,
    )

    _register_save_callback(
        page=page,
        ids=ids,
        adapter=adapter,
        config=config,
        logger=logger,
        calibration_store_id=calibration_store_id,
        page_state_store_id=page_state_store_id,
    )

    _register_save_button_enabled_state_callback(
        ids=ids,
    )


def _register_save_button_enabled_state_callback(
    *,
    ids: Any,
) -> None:
    """
    Disable the save/download button until a calibration name is provided.
    """

    @dash.callback(
        dash.Output(ids.save_calibration_btn, "disabled"),
        dash.Input(ids.file_name, "value"),
        prevent_initial_call=False,
    )
    def set_save_button_enabled_state(
        file_name: Any,
    ) -> bool:
        return save_button_should_be_disabled(
            file_name=file_name,
        )


def _register_save_callback(
    *,
    page: Any,
    ids: Any,
    adapter: SaveAdapter,
    config: SaveConfig,
    logger: logging.Logger,
    calibration_store_id: Any,
    page_state_store_id: Any,
) -> None:
    """
    Register the save callback.
    """
    callback_states = [
        dash.State(ids.file_name, "value"),
    ]

    if calibration_store_id is not None:
        callback_states.append(
            dash.State(
                calibration_store_id,
                "data",
            )
        )

    if page_state_store_id is not None:
        callback_states.append(
            dash.State(
                page_state_store_id,
                "data",
            )
        )

    @dash.callback(
        dash.Output(ids.save_out, "children"),
        dash.Output(ids.download, "data"),
        dash.Input(ids.save_calibration_btn, "n_clicks"),
        *callback_states,
        prevent_initial_call=True,
    )
    def save_callback(
        n_clicks: int,
        file_name: str,
        *optional_state_payloads: Any,
    ) -> tuple[Any, Any]:
        del n_clicks

        calibration_store_payload = None
        page_state_payload = None
        optional_state_index = 0

        if calibration_store_id is not None:
            calibration_store_payload = optional_state_payloads[optional_state_index]
            optional_state_index += 1

        if page_state_store_id is not None:
            page_state_payload = optional_state_payloads[optional_state_index]

        calibration_payload = adapter.get_calibration_payload(
            page=page,
            calibration_store_payload=calibration_store_payload,
            page_state_payload=page_state_payload,
        )

        logger.debug(
            "save_callback called with calibration_kind=%r file_name=%r "
            "calibration_payload_type=%s calibration_payload_keys=%r "
            "page_state_payload_type=%s",
            config.calibration_kind,
            file_name,
            type(calibration_payload).__name__,
            list(calibration_payload.keys()) if isinstance(calibration_payload, dict) else None,
            type(page_state_payload).__name__,
        )

        result = services.run_save_workflow(
            file_name=file_name,
            calibration_payload=calibration_payload,
            config=config,
            logger=logger,
        )

        logger.debug(
            "save_callback returning save_out=%r download_data_type=%s",
            result.save_out,
            type(result.download_data).__name__,
        )

        return result.to_tuple()