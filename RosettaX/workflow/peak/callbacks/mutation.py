# -*- coding: utf-8 -*-

from typing import Any, Optional
import inspect
import logging
import time
import uuid

import dash

from ..core import detectors
from .. import registry
from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


def register_mutation_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: Any,
    table_id: str,
    page_state_store_id: str,
    max_events_input_id: Any,
    runtime_config_store_id: str,
    mie_model_input_id: Any = None,
) -> None:
    """
    Register the peak workflow mutation callback.

    This callback handles process selection changes, detector changes, manual
    graph clicks, run actions, clear actions, table updates, page state updates,
    and process status updates.
    """
    input_components: list[Any] = [
        dash.Input(ids.process_dropdown, "value"),
        dash.Input(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(
            ids.process_action_button_pattern(),
            "n_clicks",
        ),
        dash.Input(ids.graph_hist, "clickData"),
    ]

    state_components: list[Any] = [
        dash.State(page_state_store_id, "data"),
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            ids.process_action_button_pattern(),
            "id",
        ),
        dash.State(
            ids.process_setting_pattern(),
            "id",
        ),
        dash.State(
            ids.process_setting_pattern(),
            "value",
        ),
    ]

    if max_events_input_id is not None:
        state_components.append(
            dash.State(
                max_events_input_id,
                "value",
                allow_optional=True,
            )
        )

    state_components.extend(
        [
            dash.State(table_id, "data"),
            dash.State(runtime_config_store_id, "data"),
            dash.State(
                ids.process_status_pattern(),
                "id",
            ),
        ]
    )

    if mie_model_input_id is not None:
        state_components.append(
            dash.State(mie_model_input_id, "value"),
        )

    @dash.callback(
        dash.Output(
            page_state_store_id,
            "data",
            allow_duplicate=True,
        ),
        dash.Output(
            table_id,
            "data",
            allow_duplicate=True,
        ),
        dash.Output(
            ids.process_status_pattern(),
            "children",
            allow_duplicate=True,
        ),
        *input_components,
        *state_components,
        prevent_initial_call=True,
    )
    def reduce_peak_workflow_event(
        process_name: Any,
        detector_dropdown_values: list[Any],
        action_clicks: list[Any],
        click_data: Any,
        page_state_payload: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        action_ids: list[dict[str, Any]],
        process_setting_ids: list[dict[str, Any]],
        process_setting_values: list[Any],
        *state_values: Any,
    ) -> tuple[Any, Any, list[Any]]:
        del action_clicks
        del action_ids

        unpacked_state = unpack_mutation_state_values(
            state_values=state_values,
            has_max_events_input=max_events_input_id is not None,
            has_mie_model_input=mie_model_input_id is not None,
        )

        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        triggered_id = dash.ctx.triggered_id

        if triggered_id == ids.process_dropdown:
            return clear_peak_context(
                ids=ids,
                adapter=adapter,
                page_state=page_state,
                process_name=process_name,
                status_component_ids=unpacked_state["status_component_ids"],
            )

        if trigger_is_detector_dropdown_change(
            ids=ids,
            triggered_id=triggered_id,
        ):
            return clear_peak_context(
                ids=ids,
                adapter=adapter,
                page_state=page_state,
                process_name=process_name,
                status_component_ids=unpacked_state["status_component_ids"],
            )

        if triggered_id == ids.graph_hist:
            return handle_manual_graph_click(
                ids=ids,
                adapter=adapter,
                click_data=click_data,
                process_name=process_name,
                page_state=page_state,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        if trigger_is_action_button(
            ids=ids,
            triggered_id=triggered_id,
        ):
            return handle_process_action(
                page=page,
                ids=ids,
                adapter=adapter,
                triggered_action_id=triggered_id,
                page_state=page_state,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_setting_ids=process_setting_ids,
                process_setting_values=process_setting_values,
                max_events_for_plots=unpacked_state["max_events_for_plots"],
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                runtime_config_data=unpacked_state["runtime_config_data"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        return build_no_update_callback_result(
            status_component_ids=unpacked_state["status_component_ids"],
        )


def unpack_mutation_state_values(
    *,
    state_values: tuple[Any, ...],
    has_max_events_input: bool,
    has_mie_model_input: bool,
) -> dict[str, Any]:
    """
    Unpack optional mutation callback state values.
    """
    state_value_index = 0

    if has_max_events_input:
        max_events_for_plots = state_values[state_value_index]
        state_value_index += 1

    else:
        max_events_for_plots = None

    table_data = state_values[state_value_index]
    state_value_index += 1

    runtime_config_data = state_values[state_value_index]
    state_value_index += 1

    status_component_ids = state_values[state_value_index]
    state_value_index += 1

    if has_mie_model_input:
        mie_model = state_values[state_value_index]

    else:
        mie_model = None

    return {
        "max_events_for_plots": max_events_for_plots,
        "table_data": table_data,
        "runtime_config_data": runtime_config_data,
        "status_component_ids": status_component_ids,
        "mie_model": mie_model,
    }


def trigger_is_detector_dropdown_change(
    *,
    ids: Any,
    triggered_id: Any,
) -> bool:
    """
    Return whether the trigger came from a detector dropdown.
    """
    if not isinstance(triggered_id, dict):
        return False

    pattern = ids.process_detector_dropdown_pattern()

    if not isinstance(pattern, dict):
        raise TypeError(
            "ids.process_detector_dropdown_pattern() must return a dictionary."
        )

    return triggered_id.get("type") == pattern.get("type")


def trigger_is_action_button(
    *,
    ids: Any,
    triggered_id: Any,
) -> bool:
    """
    Return whether the trigger came from a process action button.
    """
    if not isinstance(triggered_id, dict):
        return False

    pattern = ids.process_action_button_pattern()

    if not isinstance(pattern, dict):
        raise TypeError(
            "ids.process_action_button_pattern() must return a dictionary."
        )

    return triggered_id.get("type") == pattern.get("type")


def clear_peak_context(
    *,
    ids: Any,
    adapter: Any,
    page_state: Any,
    process_name: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[dict[str, Any], Any, list[Any]]:
    """
    Clear peak line context after process or detector changes.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    page_state = adapter.clear_peak_lines_payload(
        page_state=page_state,
    )

    page_state = touch_peak_graph_revision(
        adapter=adapter,
        page_state=page_state,
        reason="clear_peak_context",
        process_name=resolved_process_name,
    )

    status_children = build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=resolved_process_name,
        status="",
    )

    return (
        page_state.to_dict(),
        dash.no_update,
        status_children,
    )


def handle_manual_graph_click(
    *,
    ids: Any,
    adapter: Any,
    click_data: Any,
    process_name: Any,
    page_state: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle a graph click for manual peak selection processes.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    process = registry.get_process_instance(
        process_name=resolved_process_name,
    )

    if process is None or not process.supports_manual_click:
        return build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    uploaded_fcs_path = adapter.get_uploaded_fcs_path(
        page_state=page_state,
    )

    detector_channels = detectors.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
    )

    if not context_is_valid_for_process(
        process=process,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channels=detector_channels,
    ):
        status = build_missing_context_message(
            process=process,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
        )

        return (
            dash.no_update,
            dash.no_update,
            build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=resolved_process_name,
                status=status,
            ),
        )

    result = process.add_clicked_peak(
        click_data=click_data,
        existing_peak_lines_payload=adapter.get_peak_lines_payload(
            page_state=page_state,
        ),
    )

    if result is None:
        return build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    page_state = adapter.update_peak_lines_payload(
        page_state=page_state,
        peak_lines_payload=result.peak_lines_payload,
    )

    page_state = touch_peak_graph_revision(
        adapter=adapter,
        page_state=page_state,
        reason="manual_graph_click",
        process_name=resolved_process_name,
    )

    table_result = adapter.apply_peak_process_result_to_table(
        table_data=table_data,
        result=result,
        context={
            "mie_model": mie_model,
            "process_name": resolved_process_name,
        },
        logger=logger,
    )

    status_children = build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=resolved_process_name,
        status=result.status,
    )

    return (
        page_state.to_dict(),
        table_result,
        status_children,
    )


def handle_process_action(
    *,
    page: Any,
    ids: Any,
    adapter: Any,
    triggered_action_id: Any,
    page_state: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    max_events_for_plots: Any,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle run and clear actions for peak processes.
    """
    del ids

    if not isinstance(triggered_action_id, dict):
        return build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    target_process_name = registry.resolve_process_name(
        triggered_action_id.get("process"),
    )

    action_name = triggered_action_id.get("action")

    process = registry.get_process_instance(
        process_name=target_process_name,
    )

    if process is None:
        return build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    uploaded_fcs_path = adapter.get_uploaded_fcs_path(
        page_state=page_state,
    )

    detector_channels = detectors.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=target_process_name,
    )

    if action_name == "clear" and process.supports_clear:
        return handle_clear_action(
            adapter=adapter,
            process=process,
            target_process_name=target_process_name,
            page_state=page_state,
            table_data=table_data,
            mie_model=mie_model,
            status_component_ids=status_component_ids,
        )

    if action_name == "run" and process.supports_automatic_action:
        return handle_run_action(
            page=page,
            adapter=adapter,
            process=process,
            target_process_name=target_process_name,
            page_state=page_state,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
            process_setting_ids=process_setting_ids,
            process_setting_values=process_setting_values,
            max_events_for_plots=max_events_for_plots,
            table_data=table_data,
            mie_model=mie_model,
            runtime_config_data=runtime_config_data,
            status_component_ids=status_component_ids,
        )

    return build_no_update_callback_result(
        status_component_ids=status_component_ids,
    )


def handle_clear_action(
    *,
    adapter: Any,
    process: Any,
    target_process_name: str,
    page_state: Any,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle a clear action.
    """
    result = process.clear_peaks()

    page_state = adapter.update_peak_lines_payload(
        page_state=page_state,
        peak_lines_payload=result.peak_lines_payload,
    )

    page_state = touch_peak_graph_revision(
        adapter=adapter,
        page_state=page_state,
        reason="clear_action",
        process_name=target_process_name,
    )

    table_result = adapter.apply_peak_process_result_to_table(
        table_data=table_data,
        result=result,
        context={
            "mie_model": mie_model,
            "process_name": target_process_name,
        },
        logger=logger,
    )

    status_children = build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=target_process_name,
        status=result.status,
    )

    return (
        page_state.to_dict(),
        table_result,
        status_children,
    )


def handle_run_action(
    *,
    page: Any,
    adapter: Any,
    process: Any,
    target_process_name: str,
    page_state: Any,
    uploaded_fcs_path: Any,
    detector_channels: dict[str, Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    max_events_for_plots: Any,
    table_data: Optional[list[dict[str, Any]]],
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle an automatic run action.
    """
    if not context_is_valid_for_process(
        process=process,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channels=detector_channels,
    ):
        status = build_missing_context_message(
            process=process,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
        )

        return (
            dash.no_update,
            dash.no_update,
            build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=target_process_name,
                status=status,
            ),
        )

    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    process_settings = build_process_settings(
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        process_name=target_process_name,
    )

    resolved_peak_count = casting.as_int(
        process_settings.get("peak_count"),
        default=runtime_config.get_int(
            "calibration.peak_count",
            default=3,
        ),
        min_value=1,
        max_value=50,
    )

    resolved_max_events = casting.as_int(
        max_events_for_plots,
        default=runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=10000,
        ),
        min_value=1,
        max_value=5_000_000,
    )

    if hasattr(adapter, "get_backend"):
        backend = adapter.get_backend(
            page=page,
            uploaded_fcs_path=uploaded_fcs_path,
        )
    else:
        backend = None

    result = call_run_automatic_action_with_supported_arguments(
        process=process,
        backend=backend,
        detector_channels=detector_channels,
        process_settings=process_settings,
        peak_count=resolved_peak_count,
        max_events_for_analysis=resolved_max_events,
        max_events_for_plots=resolved_max_events,
        runtime_config_data=runtime_config_data,
    )

    if result is None:
        return build_no_update_callback_result(
            status_component_ids=status_component_ids,
        )

    page_state = adapter.update_peak_lines_payload(
        page_state=page_state,
        peak_lines_payload=result.peak_lines_payload,
    )

    page_state = touch_peak_graph_revision(
        adapter=adapter,
        page_state=page_state,
        reason="run_action",
        process_name=target_process_name,
        process_settings=process_settings,
    )

    table_result = adapter.apply_peak_process_result_to_table(
        table_data=table_data,
        result=result,
        context={
            "mie_model": mie_model,
            "process_name": target_process_name,
        },
        logger=logger,
    )

    status_children = build_status_children(
        status_component_ids=status_component_ids,
        target_process_name=target_process_name,
        status=result.status,
    )

    logger.debug(
        "Completed run action for process=%r with peak_graph_revision=%r.",
        target_process_name,
        adapter.get_page_state_payload(
            page_state=page_state,
        ).get("peak_graph_revision"),
    )

    return (
        page_state.to_dict(),
        table_result,
        status_children,
    )


def call_run_automatic_action_with_supported_arguments(
    *,
    process: Any,
    backend: Any,
    detector_channels: dict[str, Any],
    process_settings: dict[str, Any],
    peak_count: int,
    max_events_for_analysis: int,
    max_events_for_plots: int,
    runtime_config_data: Any,
) -> Any:
    """
    Call ``process.run_automatic_action`` with only the arguments supported by
    that process.

    This keeps old peak scripts working while allowing newer scripts to use
    richer context such as ``process_settings`` and ``runtime_config_data``.
    """
    method = getattr(
        process,
        "run_automatic_action",
        None,
    )

    if not callable(method):
        logger.debug(
            "Process %r does not implement run_automatic_action.",
            getattr(process, "process_name", process),
        )

        return None

    candidate_arguments = {
        "backend": backend,
        "detector_channels": detector_channels,
        "process_settings": process_settings,
        "peak_count": peak_count,
        "max_events_for_analysis": max_events_for_analysis,
        "max_events_for_plots": max_events_for_plots,
        "runtime_config_data": runtime_config_data,
    }

    signature = inspect.signature(
        method,
    )

    accepts_arbitrary_keywords = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )

    if accepts_arbitrary_keywords:
        logger.debug(
            "Calling automatic process %r with all candidate arguments.",
            getattr(process, "process_name", process),
        )

        return method(
            **candidate_arguments,
        )

    supported_arguments = {
        argument_name: argument_value
        for argument_name, argument_value in candidate_arguments.items()
        if argument_name in signature.parameters
    }

    logger.debug(
        "Calling automatic process %r with supported arguments=%r.",
        getattr(process, "process_name", process),
        list(supported_arguments.keys()),
    )

    return method(
        **supported_arguments,
    )


def touch_peak_graph_revision(
    *,
    adapter: Any,
    page_state: Any,
    reason: str,
    process_name: Any,
    process_settings: Optional[dict[str, Any]] = None,
) -> Any:
    """
    Force downstream graph callbacks to rebuild after a peak workflow mutation.

    Dash compares store data structurally. A revision token makes every run,
    clear, or manual click produce a distinct page state payload even if the
    peak positions or gates are numerically identical.
    """
    payload = adapter.get_page_state_payload(
        page_state=page_state,
    )

    payload["peak_graph_revision"] = {
        "id": uuid.uuid4().hex,
        "timestamp": time.time(),
        "reason": str(reason),
        "process_name": str(process_name or ""),
        "process_settings": dict(process_settings or {}),
    }

    return adapter.build_page_state(
        payload=payload,
    )


def build_process_settings(
    *,
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    process_name: str,
) -> dict[str, Any]:
    """
    Build a dictionary of process setting values for the selected process.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    process_settings: dict[str, Any] = {}

    for process_setting_id, process_setting_value in zip(
        process_setting_ids or [],
        process_setting_values or [],
        strict=False,
    ):
        if not isinstance(process_setting_id, dict):
            continue

        if process_setting_id.get("process") != resolved_process_name:
            continue

        setting_name = process_setting_id.get("setting")

        if not isinstance(setting_name, str):
            continue

        process_settings[setting_name] = process_setting_value

    return process_settings


def context_is_valid_for_process(
    *,
    process: Any,
    uploaded_fcs_path: Any,
    detector_channels: dict[str, Any],
) -> bool:
    """
    Return whether the uploaded file and required channels are available.
    """
    if not str(uploaded_fcs_path or "").strip():
        return False

    for channel_name in process.get_required_detector_channels():
        if not str(detector_channels.get(channel_name) or "").strip():
            return False

    return True


def build_missing_context_message(
    *,
    process: Any,
    uploaded_fcs_path: Any,
    detector_channels: dict[str, Any],
) -> str:
    """
    Build a user visible missing context message.
    """
    if not str(uploaded_fcs_path or "").strip():
        return "Upload an FCS file first."

    missing_channel_names: list[str] = []

    for channel_name in process.get_required_detector_channels():
        if not str(detector_channels.get(channel_name) or "").strip():
            missing_channel_names.append(
                str(channel_name),
            )

    if len(missing_channel_names) == 1:
        return f"Select the {missing_channel_names[0]} detector channel first."

    if missing_channel_names:
        missing_channel_text = " and ".join(
            missing_channel_names,
        )

        return f"Select the {missing_channel_text} detector channels first."

    return "Upload an FCS file and select the required detector channel(s) first."


def build_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
    target_process_name: str,
    status: str,
) -> list[Any]:
    """
    Build status children for pattern matched status outputs.
    """
    children: list[Any] = []

    for status_component_id in status_component_ids or []:
        if status_component_id.get("process") == target_process_name:
            children.append(
                status,
            )

        else:
            children.append(
                "",
            )

    return children


def build_no_update_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
) -> list[Any]:
    """
    Build a valid no update list for wildcard status outputs.
    """
    return [
        dash.no_update
        for _ in (status_component_ids or [])
    ]


def build_no_update_callback_result(
    *,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Build a valid no update result for the mutation callback.
    """
    return (
        dash.no_update,
        dash.no_update,
        build_no_update_status_children(
            status_component_ids=status_component_ids,
        ),
    )