
import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import html

from . import services
from .adapters import SaveAdapter
from .models import SaveConfig


def save_button_should_be_disabled(
    file_name: Any,
    output_channel_name: Any = None,
    require_output_channel_name: bool = False,
    calibration_payload: Any = None,
    review_acknowledgment: Any = None,
) -> bool:
    """
    Return whether the save button should be disabled.
    """
    if not bool(str(file_name or "").strip()):
        return True

    if require_output_channel_name and not bool(str(output_channel_name or "").strip()):
        return True

    return (
        not isinstance(calibration_payload, dict)
        or not calibration_payload
        or "reviewed" not in (review_acknowledgment or [])
    )


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
        page=page,
        ids=ids,
        adapter=adapter,
        config=config,
        calibration_store_id=calibration_store_id,
        page_state_store_id=page_state_store_id,
    )
    _register_save_review_summary_callback(
        page=page,
        ids=ids,
        adapter=adapter,
        config=config,
        calibration_store_id=calibration_store_id,
        page_state_store_id=page_state_store_id,
    )


def _register_save_button_enabled_state_callback(
    *,
    page: Any,
    ids: Any,
    adapter: SaveAdapter,
    config: SaveConfig,
    calibration_store_id: Any,
    page_state_store_id: Any,
) -> None:
    """
    Disable the save/download button until a calibration name is provided.
    """

    store_inputs = _build_store_inputs(
        calibration_store_id=calibration_store_id,
        page_state_store_id=page_state_store_id,
    )

    @dash.callback(
        dash.Output(ids.save_calibration_btn, "disabled"),
        dash.Input(ids.file_name, "value"),
        dash.Input(ids.output_channel_name, "value"),
        dash.Input(ids.review_acknowledgment, "value"),
        *store_inputs,
        prevent_initial_call=False,
    )
    def set_save_button_enabled_state(
        file_name: Any,
        output_channel_name: Any,
        review_acknowledgment: Any,
        *store_payloads: Any,
    ) -> bool:
        calibration_payload = _get_calibration_payload(
            page=page,
            adapter=adapter,
            calibration_store_id=calibration_store_id,
            page_state_store_id=page_state_store_id,
            store_payloads=store_payloads,
        )
        return save_button_should_be_disabled(
            file_name=file_name,
            output_channel_name=output_channel_name,
            require_output_channel_name=config.require_output_channel_name,
            calibration_payload=calibration_payload,
            review_acknowledgment=review_acknowledgment,
        )


def _register_save_review_summary_callback(
    *,
    page: Any,
    ids: Any,
    adapter: SaveAdapter,
    config: SaveConfig,
    calibration_store_id: Any,
    page_state_store_id: Any,
) -> None:
    """Render live readiness checks and concise calibration context before saving."""
    store_inputs = _build_store_inputs(
        calibration_store_id=calibration_store_id,
        page_state_store_id=page_state_store_id,
    )

    @dash.callback(
        dash.Output(ids.review_summary, "children"),
        dash.Input(ids.file_name, "value"),
        dash.Input(ids.output_channel_name, "value"),
        *store_inputs,
        prevent_initial_call=False,
    )
    def render_save_review(
        file_name: Any,
        output_channel_name: Any,
        *store_payloads: Any,
    ) -> dbc.Alert:
        calibration_payload = _get_calibration_payload(
            page=page,
            adapter=adapter,
            calibration_store_id=calibration_store_id,
            page_state_store_id=page_state_store_id,
            store_payloads=store_payloads,
        )
        return _build_save_review_summary(
            file_name=file_name,
            output_channel_name=output_channel_name,
            calibration_payload=calibration_payload,
            config=config,
        )


def _build_store_inputs(
    *,
    calibration_store_id: Any,
    page_state_store_id: Any,
) -> list[dash.Input]:
    """Build shared store inputs in the order expected by the save adapter."""
    inputs: list[dash.Input] = []
    if calibration_store_id is not None:
        inputs.append(dash.Input(calibration_store_id, "data"))
    if page_state_store_id is not None:
        inputs.append(dash.Input(page_state_store_id, "data"))
    return inputs


def _get_calibration_payload(
    *,
    page: Any,
    adapter: SaveAdapter,
    calibration_store_id: Any,
    page_state_store_id: Any,
    store_payloads: tuple[Any, ...],
) -> dict | None:
    """Resolve the calibration payload from the optional shared stores."""
    payload_index = 0
    calibration_store_payload = None
    page_state_payload = None
    if calibration_store_id is not None:
        calibration_store_payload = store_payloads[payload_index]
        payload_index += 1
    if page_state_store_id is not None:
        page_state_payload = store_payloads[payload_index]
    return adapter.get_calibration_payload(
        page=page,
        calibration_store_payload=calibration_store_payload,
        page_state_payload=page_state_payload,
    )


def _build_save_review_summary(
    *,
    file_name: Any,
    output_channel_name: Any,
    calibration_payload: dict | None,
    config: SaveConfig,
) -> dbc.Alert:
    """Build the pre-download readiness and calibration-context summary."""
    checks = [
        (
            "Calibration fit is available",
            isinstance(calibration_payload, dict) and bool(calibration_payload),
        ),
        ("Calibration name is entered", bool(str(file_name or "").strip())),
    ]
    if config.require_output_channel_name:
        checks.append(
            (
                "Applied output channel is entered",
                bool(str(output_channel_name or "").strip()),
            )
        )
    ready = all(is_complete for _, is_complete in checks)
    context = (
        f"{len(calibration_payload)} calibration fields are ready for review."
        if calibration_payload
        else "Create a calibration to review its context and fit."
    )
    return dbc.Alert(
        [
            html.Strong("Ready to save" if ready else "Needs attention"),
            html.Div(context, style={"fontSize": "0.9rem", "marginTop": "4px"}),
            html.Ul(
                [
                    html.Li(
                        f"{'Complete' if is_complete else 'Required'}: {label}"
                    )
                    for label, is_complete in checks
                ],
                style={"marginBottom": "0", "marginTop": "6px", "fontSize": "0.88rem"},
            ),
        ],
        color="success" if ready else "warning",
        style={"marginBottom": "12px"},
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
        dash.State(ids.output_channel_name, "value"),
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

    callback_outputs = [
        dash.Output(ids.save_out, "children"),
        dash.Output(ids.download, "data"),
    ]
    if page_state_store_id is not None and config.page_state_saved_field:
        callback_outputs.append(
            dash.Output(
                page_state_store_id,
                "data",
                allow_duplicate=True,
            )
        )

    @dash.callback(
        *callback_outputs,
        dash.Input(ids.save_calibration_btn, "n_clicks"),
        *callback_states,
        prevent_initial_call=True,
    )
    def save_callback(
        n_clicks: int,
        file_name: str,
        output_channel_name: str,
        *optional_state_payloads: Any,
    ) -> tuple[Any, ...]:
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
            output_channel_name=output_channel_name,
            calibration_payload=calibration_payload,
            config=config,
            logger=logger,
        )

        page_state_update = dash.no_update
        if (
            page_state_store_id is not None
            and config.page_state_saved_field
            and result.download_data is not dash.no_update
        ):
            page_state_update = dict(page_state_payload or {})
            page_state_update[config.page_state_saved_field] = True

        logger.debug(
            "save_callback returning save_out=%r download_data_type=%s",
            result.save_out,
            type(result.download_data).__name__,
        )

        if page_state_store_id is not None and config.page_state_saved_field:
            return (*result.to_tuple(), page_state_update)

        return result.to_tuple()
