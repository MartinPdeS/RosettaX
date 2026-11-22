
import dash
import logging
from .. import registry
from ..core import detectors
from ..core import mutation as peak_mutation
from ..core.process_calls import call_add_clicked_peak_with_supported_arguments
from ..core.process_settings import build_process_settings
from ..models import PeakMutationOutput, PeakTransition
from .debug_panel import build_rosetta_result_panel
from dash import html
from typing import Any

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
        dash.Input(ids.graph_hist, "selectedData"),
        dash.Input(ids.process_setting_pattern(), "value"),
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
        dash.State(ids.advanced_mode_switch, "value"),
        dash.State(ids.data_filter_switch, "value"),
        dash.State(ids.axis_scale_toggle, "value"),
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
        selected_data: Any,
        process_setting_values: list[Any],
        page_state_payload: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        action_ids: list[dict[str, Any]],
        process_setting_ids: list[dict[str, Any]],
        advanced_mode_value: Any,
        data_filter_value: Any,
        axis_scale_toggle_values: Any,
        *state_values: Any,
    ) -> tuple[Any, Any, list[Any]]:
        unpacked_state = unpack_mutation_state_values(
            state_values=state_values,
            has_max_events_input=max_events_input_id is not None,
            has_mie_model_input=mie_model_input_id is not None,
        )

        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        triggered_id = dash.ctx.triggered_id
        triggered_graph_property = resolve_triggered_graph_property_name()

        if triggered_id == ids.process_dropdown:
            return clear_peak_context(
                ids=ids,
                adapter=adapter,
                page_state=page_state,
                process_name=process_name,
                clear_table=True,
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                runtime_config_data=unpacked_state["runtime_config_data"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        if any(
            trigger_is_detector_dropdown_change(ids=ids, triggered_id=changed_id)
            and changed_id.get("process") == process_name
            for changed_id in dash.ctx.triggered_prop_ids.values()
        ):
            detector_channels = detectors.resolve_detector_channels_for_process(
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_name=process_name,
            )
            clear_table = peak_mutation.resolve_detector_change(
                page_state_payload=page_state_payload if isinstance(page_state_payload, dict) else {},
                process_name=process_name,
                detector_channels=detector_channels,
            )
            if clear_table is None:
                return build_no_update_callback_result(status_component_ids=unpacked_state["status_component_ids"])
            return clear_peak_context(
                ids=ids,
                adapter=adapter,
                page_state=page_state,
                process_name=process_name,
                clear_table=clear_table,
                status="Warning: The detector selection changed. Detect peaks again to refill the calibration table." if clear_table else "",
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                runtime_config_data=unpacked_state["runtime_config_data"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        if triggered_id == ids.graph_hist:
            return handle_manual_graph_click(
                ids=ids,
                adapter=adapter,
                triggered_graph_property=triggered_graph_property,
                click_data=click_data,
                selected_data=selected_data,
                process_name=process_name,
                page_state=page_state,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_setting_ids=process_setting_ids,
                process_setting_values=process_setting_values,
                data_filter_value=data_filter_value,
                axis_scale_toggle_values=axis_scale_toggle_values,
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                runtime_config_data=unpacked_state["runtime_config_data"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        preview_only = (
            process_name == "Rosetta Script Mixture"
            and triggered_id == ids.process_setting(
                process_name=process_name, setting_name="marker_fit_strictness",
            )
        )
        active_action = (
            trigger_is_action_button(ids=ids, triggered_id=triggered_id)
            and triggered_id.get("process") == process_name
            and any(
                button_id == triggered_id and click_count
                for button_id, click_count in zip(action_ids or [], action_clicks or [], strict=False)
            )
        )
        if preview_only or active_action:
            return handle_process_action(
                page=page,
                ids=ids,
                adapter=adapter,
                triggered_action_id=ids.process_action_button(process_name=process_name, action_name="run")
                if preview_only else triggered_id,
                preview_only=preview_only,
                page_state=page_state,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_setting_ids=process_setting_ids,
                process_setting_values=process_setting_values,
                advanced_mode_value=advanced_mode_value,
                data_filter_value=data_filter_value,
                axis_scale_toggle_values=axis_scale_toggle_values,
                max_events_for_plots=unpacked_state["max_events_for_plots"],
                table_data=unpacked_state["table_data"],
                mie_model=unpacked_state["mie_model"],
                runtime_config_data=unpacked_state["runtime_config_data"],
                status_component_ids=unpacked_state["status_component_ids"],
            )

        return build_no_update_callback_result(
            status_component_ids=unpacked_state["status_component_ids"],
        )


    dash.clientside_callback(
        """
        function(clicks, settings, pageState, statusIds, selectedProcess) {
            const context = dash_clientside.callback_context;
            const trigger = context.triggered_id;
            const newFile = typeof trigger === "string" && !pageState?.peak_graph_revision;
            const run = trigger && trigger.action === "run" && context.triggered[0].value > 0;
            const preview = trigger && trigger.setting === "marker_fit_strictness" &&
                trigger.process === selectedProcess;
            return (statusIds || []).map(id => (
                newFile || ((run || preview) && id.process === trigger.process)
                    ? null : dash_clientside.no_update
            ));
        }
        """,
        dash.Output(ids.process_status_pattern(), "children", allow_duplicate=True),
        dash.Input(ids.process_action_button_pattern(), "n_clicks"),
        dash.Input(ids.process_setting_pattern(), "value"),
        dash.Input(page_state_store_id, "data"),
        dash.State(ids.process_status_pattern(), "id"),
        dash.State(ids.process_dropdown, "value"),
        prevent_initial_call=True,
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


def resolve_triggered_graph_property_name() -> str | None:
    """
    Return the triggering property name for the active graph callback.
    """
    triggered = getattr(
        dash.ctx,
        "triggered",
        None,
    )

    if not isinstance(triggered, list) or not triggered:
        return None

    first_trigger = triggered[0]

    if not isinstance(first_trigger, dict):
        return None

    prop_id = first_trigger.get("prop_id")

    if not isinstance(prop_id, str) or "." not in prop_id:
        return None

    return prop_id.rsplit(".", 1)[1]


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
        raise TypeError("ids.process_action_button_pattern() must return a dictionary.")

    return triggered_id.get("type") == pattern.get("type")


def clear_peak_context(
    *,
    ids: Any,
    adapter: Any,
    page_state: Any,
    process_name: Any,
    clear_table: bool = False,
    status: str = "",
    table_data: list[dict[str, Any]] | None = None,
    mie_model: Any = None,
    runtime_config_data: Any = None,
    status_component_ids: list[dict[str, Any]],
) -> tuple[dict[str, Any], Any, list[Any]]:
    """
    Clear peak line context after process or detector changes.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    transition = peak_mutation.clear_peak_context(
        adapter=adapter, page_state=page_state, clear_table=clear_table, table_data=table_data, status=status,
        context={
            "mie_model": mie_model,
            "process_name": resolved_process_name,
            "runtime_config_data": runtime_config_data,
            "replace_existing_table_peaks": True,
        },
    )
    return render_peak_transition(
        transition=transition, status_component_ids=status_component_ids, process_name=resolved_process_name,
    )


def handle_manual_graph_click(
    *,
    ids: Any,
    adapter: Any,
    triggered_graph_property: str | None,
    click_data: Any,
    selected_data: Any,
    process_name: Any,
    page_state: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    data_filter_value: Any,
    axis_scale_toggle_values: Any,
    table_data: list[dict[str, Any]] | None,
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle a graph click for manual peak selection processes.
    """
    effective_click_data = click_data
    effective_selected_data = selected_data

    if triggered_graph_property == "selectedData":
        effective_click_data = None
    elif triggered_graph_property == "clickData":
        effective_selected_data = None

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

    if not manual_graph_event_has_actionable_payload(
        process=process,
        triggered_graph_property=triggered_graph_property,
        click_data=effective_click_data,
        selected_data=effective_selected_data,
    ):
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
    process_settings = build_process_settings(
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        process_name=resolved_process_name,
    )
    process_settings["filter_edge_artifacts"] = data_filter_value
    backend = adapter.get_backend(
        uploaded_fcs_path=uploaded_fcs_path,
    )

    if not peak_mutation.context_is_valid_for_process(
        process=process,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channels=detector_channels,
    ):
        status = peak_mutation.build_missing_context_message(
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

    result = call_add_clicked_peak_with_supported_arguments(
        process=process,
        click_data=effective_click_data,
        selected_data=effective_selected_data,
        existing_peak_lines_payload=adapter.get_peak_lines_payload(
            page_state=page_state,
        ),
        backend=backend,
        detector_channels=detector_channels,
        process_settings=process_settings,
        runtime_config_data=runtime_config_data,
        axis_scale_toggle_values=axis_scale_toggle_values,
    )

    if result is None:
        return (
            dash.no_update,
            dash.no_update,
            build_status_children(
                status_component_ids=status_component_ids,
                target_process_name=resolved_process_name,
                status="That click did not resolve to a selectable peak. Try clicking directly on the plotted signal.",
            ),
        )

    transition = peak_mutation.apply_peak_result(
        adapter=adapter, page_state=page_state, result=result, reason="manual_graph_click",
        table_data=table_data,
        context={
            "mie_model": mie_model,
            "process_name": resolved_process_name,
            "runtime_config_data": runtime_config_data,
            "detector_channels": detector_channels,
        },
        status=result.status,
    )
    return render_peak_transition(
        transition=transition, status_component_ids=status_component_ids, process_name=resolved_process_name,
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
    advanced_mode_value: Any = None,
    data_filter_value: Any = None,
    axis_scale_toggle_values: Any = None,
    max_events_for_plots: Any,
    table_data: list[dict[str, Any]] | None,
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
    preview_only: bool = False,
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
            runtime_config_data=runtime_config_data,
            status_component_ids=status_component_ids,
        )

    if action_name == "run" and process.supports_automatic_action:
        return handle_run_action(
            page=page,
            preview_only=preview_only,
            adapter=adapter,
            process=process,
            target_process_name=target_process_name,
            page_state=page_state,
            uploaded_fcs_path=uploaded_fcs_path,
            detector_channels=detector_channels,
            process_setting_ids=process_setting_ids,
            process_setting_values=process_setting_values,
            advanced_mode_value=advanced_mode_value,
            data_filter_value=data_filter_value,
            axis_scale_toggle_values=axis_scale_toggle_values,
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
    table_data: list[dict[str, Any]] | None,
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any]]:
    """
    Handle a clear action.
    """
    result = process.clear_peaks()
    transition = peak_mutation.apply_peak_result(
        adapter=adapter, page_state=page_state, result=result, reason="clear_action",
        table_data=table_data,
        context={
            "mie_model": mie_model,
            "process_name": target_process_name,
            "runtime_config_data": runtime_config_data,
            "replace_existing_table_peaks": True,
        },
        status="" if target_process_name.startswith("Rosetta Script") else result.status,
    )
    return render_peak_transition(
        transition=transition, status_component_ids=status_component_ids, process_name=target_process_name,
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
    advanced_mode_value: Any = None,
    data_filter_value: Any = None,
    axis_scale_toggle_values: Any = None,
    max_events_for_plots: Any,
    table_data: list[dict[str, Any]] | None,
    mie_model: Any,
    runtime_config_data: Any,
    status_component_ids: list[dict[str, Any]],
    preview_only: bool = False,
) -> tuple[Any, Any, list[Any]]:
    """Run peak detection and render its workflow transition for Dash."""
    transition = peak_mutation.run_peak_process(
        adapter=adapter, process=process, target_process_name=target_process_name,
        page_state=page_state, uploaded_fcs_path=uploaded_fcs_path, detector_channels=detector_channels,
        process_setting_ids=process_setting_ids, process_setting_values=process_setting_values,
        advanced_mode_value=advanced_mode_value, data_filter_value=data_filter_value,
        axis_scale_toggle_values=axis_scale_toggle_values, max_events_for_plots=max_events_for_plots,
        table_data=table_data, mie_model=mie_model, runtime_config_data=runtime_config_data,
        preview_only=preview_only,
    )
    return render_peak_transition(
        transition=transition, status_component_ids=status_component_ids, process_name=target_process_name,
    )


def render_peak_transition(
    *,
    transition: PeakTransition,
    status_component_ids: list[dict[str, Any]],
    process_name: str,
) -> PeakMutationOutput:
    """Convert workflow state, table rows, and feedback into Dash outputs."""
    if transition.status is None:
        status_children = build_no_update_status_children(status_component_ids=status_component_ids)
    else:
        status_children = build_status_children(
            status_component_ids=status_component_ids, target_process_name=process_name,
            status=transition.status, debug_payload=transition.debug_payload,
        )

    return PeakMutationOutput(
        page_state=transition.page_state.to_dict() if transition.page_state is not None else dash.no_update,
        table_data=transition.table_rows if transition.table_rows is not None else dash.no_update,
        status_children=status_children,
    )


def manual_graph_event_has_actionable_payload(
    *,
    process: Any,
    triggered_graph_property: str | None,
    click_data: Any,
    selected_data: Any,
) -> bool:
    """
    Return whether the active manual graph event contains usable selection data.
    """
    if triggered_graph_property == "selectedData":
        extractor = getattr(
            process,
            "extract_selected_xy_range",
            None,
        )

        if callable(extractor):
            return extractor(selected_data) is not None

        extractor = getattr(
            process,
            "extract_selected_x_range",
            None,
        )

        if callable(extractor):
            return extractor(selected_data) is not None

        return bool(selected_data)

    if triggered_graph_property == "clickData":
        extractor = getattr(
            process,
            "extract_clicked_xy_position",
            None,
        )

        if callable(extractor):
            return extractor(click_data) is not None

        extractor = getattr(
            process,
            "extract_clicked_x_position",
            None,
        )

        if callable(extractor):
            return extractor(click_data) is not None

        return bool(click_data)

    return bool(click_data) or bool(selected_data)


def build_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
    target_process_name: str,
    status: str,
    debug_payload: Any = None,
) -> list[Any]:
    """
    Build status children for pattern matched status outputs.
    """
    if target_process_name.startswith("Rosetta Script"):
        result_panel = build_rosetta_result_panel(status=status, peak_lines_payload=debug_payload)
        status_component = result_panel if result_panel is not None else build_status_alert(status=status)
        if result_panel is None and status_component:
            status_component = html.Div(status_component, className="app-diagnostics-inline peak-result-message")
    else:
        status_component = build_status_alert(status=status)

    return [
        status_component if status_component_id.get("process") == target_process_name else ""
        for status_component_id in status_component_ids or []
    ]


def build_status_alert(
    *,
    status: Any,
) -> Any:
    """
    Render errors, warnings, and preview messages as text.
    """
    status_text = str(status or "").strip()

    if not status_text:
        return ""

    status_color = classify_status_alert_color(status_text=status_text)
    if status_color == "success":
        return ""
    text_colors = {
        "danger": "var(--bs-danger-text-emphasis)",
        "warning": "#8a5a00",
    }
    return html.Div(
        status_text,
        role="alert" if status_color == "danger" else "status",
        **{"data-severity": "error" if status_color == "danger" else "warning"},
        style={
            "marginBottom": "0px",
            "whiteSpace": "pre-wrap",
            "lineHeight": "1.45",
            "fontSize": "0.95rem",
            "color": text_colors.get(status_color, "var(--bs-secondary-color)"),
        },
    )


def classify_status_alert_color(
    *,
    status_text: str,
) -> str:
    """
    Classify one status message into a Bootstrap alert color.
    """
    normalized_status_text = str(status_text or "").strip().lower()

    if not normalized_status_text:
        return "secondary"

    if normalized_status_text.startswith(("warning:", "partial result:")):
        return "warning"

    error_markers = [
        "error",
        "failed",
        "unable",
        "could not",
        "missing",
        "select ",
        "upload ",
        "no finite",
        "not available",
        "not initialized",
        "stopping",
        "no validated",
        "0 fluorescent marker peaks",
        "did not resolve",
        "requires",
        "invalid",
    ]

    if any(marker in normalized_status_text for marker in error_markers):
        return "danger"

    warning_markers = [
        "warning",
        "cleared",
        "rejected:",
        "run completed with no detected peaks",
        "remain unsized",
        "two fluorescent candidates",
        "saturation guard excluded",
    ]

    if any(marker in normalized_status_text for marker in warning_markers):
        return "warning"

    return "success"


def build_no_update_status_children(
    *,
    status_component_ids: list[dict[str, Any]],
) -> list[Any]:
    """
    Build a valid no update list for wildcard status outputs.
    """
    return [dash.no_update for _ in (status_component_ids or [])]


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
