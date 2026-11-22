"""Apply the state changes produced by peak workflow actions."""

import logging
import time
import uuid
from ..models import PeakTransition
from .process_calls import call_run_automatic_action_with_supported_arguments
from .process_settings import build_process_settings
from RosettaX.utils import casting
from RosettaX.utils.runtime_config import RuntimeConfig
from types import SimpleNamespace
from typing import Any

logger = logging.getLogger(__name__)


def touch_peak_graph_revision(
    *,
    adapter: Any,
    page_state: Any,
    reason: str,
    process_name: Any,
    process_settings: dict[str, Any] | None = None,
    state_changes: dict[str, Any] | None = None,
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
    if state_changes is not None:
        payload.update(state_changes)

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


def resolve_detector_change(
    *,
    page_state_payload: dict[str, Any],
    process_name: str,
    detector_channels: dict[str, Any],
) -> bool | None:
    """Decide whether a selection change invalidates measured table rows.

    Parameters
    ----------
    page_state_payload : dict
        Stored page state, including detector channels from the last table update.
    process_name : str
        Active peak process.
    detector_channels : dict
        Currently selected FCS channel names by detector role.

    Returns
    -------
    bool or None
        True clears the graph and measured rows. False clears the graph alone.
        None leaves results intact when the same selection is hydrated again.
    """
    table_context = page_state_payload.get("peak_table_context")
    if isinstance(table_context, dict) and table_context.get("process_name") == process_name:
        return True if table_context.get("detector_channels") != detector_channels else None

    # Older scattering sessions only recorded context for provisional assignments.
    return bool(page_state_payload.get("rosetta_assignment_evidence"))


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


def synchronize_page_state_table_rows(
    *,
    adapter: Any,
    page_state: Any,
    table_result: Any,
) -> Any:
    """
    Mirror updated table rows into page state when that state owns table rows.

    This keeps table hydration callbacks deterministic when a peak action
    updates both page state and table in the same interaction.
    """
    if not isinstance(table_result, list):
        return page_state

    payload = adapter.get_page_state_payload(
        page_state=page_state,
    )

    if "reference_table_rows" not in payload:
        return page_state

    normalize_table_data = getattr(
        adapter,
        "normalize_table_data",
        None,
    )

    if callable(normalize_table_data):
        normalized_table_rows = normalize_table_data(
            table_data=table_result,
        )

    else:
        normalized_table_rows = table_result

    if payload.get("reference_table_rows") == normalized_table_rows:
        return page_state

    payload["reference_table_rows"] = normalized_table_rows

    return adapter.build_page_state(
        payload=payload,
    )


def clear_peak_context(
    *,
    adapter: Any,
    page_state: Any,
    context: dict[str, Any],
    clear_table: bool,
    table_data: list[dict[str, Any]] | None,
    status: str = "",
    reason: str = "clear_peak_context",
) -> PeakTransition:
    """Invalidate the previous peak graph and optionally its measured table rows."""
    table_rows = None
    if clear_table:
        table_rows = _update_peak_table(
            adapter=adapter, table_data=table_data,
            result=SimpleNamespace(clear_existing_table_peaks=True), context=context,
        )

    page_state = adapter.clear_peak_lines_payload(page_state=page_state)
    page_state = touch_peak_graph_revision(
        adapter=adapter, page_state=page_state, reason=reason, process_name=context["process_name"],
        state_changes={"peak_table_context": None} if clear_table else None,
    )
    return PeakTransition(
        page_state=synchronize_page_state_table_rows(adapter=adapter, page_state=page_state, table_result=table_rows),
        table_rows=table_rows,
        status=status,
    )


def _update_peak_table(
    *,
    adapter: Any,
    table_data: list[dict[str, Any]] | None,
    result: Any,
    context: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """Translate a process result into table rows when the adapter changes them."""
    table_result = adapter.apply_peak_process_result_to_table(
        table_data=table_data, result=result, context=context, logger=logger,
    )
    return table_result if isinstance(table_result, list) else None


def apply_peak_result(
    *,
    adapter: Any,
    page_state: Any,
    result: Any,
    reason: str,
    table_data: list[dict[str, Any]] | None,
    context: dict[str, Any],
    process_settings: dict[str, Any] | None = None,
    status: str,
    debug_payload: Any = None,
) -> PeakTransition:
    """Apply graph and table updates together and mirror rows into page state."""
    page_state = adapter.update_peak_lines_payload(
        page_state=page_state, peak_lines_payload=result.peak_lines_payload,
    )
    table_rows = _update_peak_table(adapter=adapter, table_data=table_data, result=result, context=context)
    detector_channels = context.get("detector_channels")
    table_context = (
        {"process_name": context["process_name"], "detector_channels": dict(detector_channels)}
        if detector_channels and not getattr(result, "clear_existing_table_peaks", False)
        else None
    )
    page_state = touch_peak_graph_revision(
        adapter=adapter, page_state=page_state, reason=reason,
        process_name=context["process_name"], process_settings=process_settings,
        state_changes={"peak_table_context": table_context} if table_rows is not None else None,
    )
    return PeakTransition(
        page_state=synchronize_page_state_table_rows(adapter=adapter, page_state=page_state, table_result=table_rows),
        table_rows=table_rows,
        status=status,
        debug_payload=debug_payload,
    )


def run_peak_process(
    *,
    adapter: Any,
    process: Any,
    target_process_name: str,
    page_state: Any,
    uploaded_fcs_path: Any,
    detector_channels: dict[str, Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    advanced_mode_value: Any,
    data_filter_value: Any,
    axis_scale_toggle_values: Any,
    max_events_for_plots: Any,
    table_data: list[dict[str, Any]] | None,
    mie_model: Any,
    runtime_config_data: Any,
    preview_only: bool,
) -> PeakTransition:
    """Run peak detection and resolve the resulting graph, table, and feedback."""
    context = {
        "mie_model": mie_model,
        "process_name": target_process_name,
        "detector_channels": detector_channels,
        "runtime_config_data": runtime_config_data,
        "replace_existing_table_peaks": True,
    }
    if not context_is_valid_for_process(
        process=process, uploaded_fcs_path=uploaded_fcs_path, detector_channels=detector_channels,
    ):
        if preview_only:
            return PeakTransition()
        status = build_missing_context_message(
            process=process, uploaded_fcs_path=uploaded_fcs_path, detector_channels=detector_channels,
        )
        return clear_peak_context(
            adapter=adapter, page_state=page_state, context=context, clear_table=True,
            table_data=table_data, status=status, reason="run_action_failed",
        )

    runtime_config = RuntimeConfig.from_dict(runtime_config_data if isinstance(runtime_config_data, dict) else None)
    process_settings = build_process_settings(
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        process_name=target_process_name,
    )
    process_settings["advanced_mode"] = advanced_mode_value
    process_settings["filter_edge_artifacts"] = data_filter_value
    process_settings["axis_scale_toggle_values"] = axis_scale_toggle_values
    if preview_only:
        process_settings["preview_only"] = True

    max_events = casting.as_int(
        max_events_for_plots,
        default=runtime_config.get_int("calibration.max_events_for_analysis"),
        min_value=1,
        max_value=5_000_000,
    )
    result = call_run_automatic_action_with_supported_arguments(
        process=process,
        backend=adapter.get_backend(uploaded_fcs_path=uploaded_fcs_path),
        detector_channels=detector_channels,
        process_settings=process_settings,
        peak_count=process_settings.get("peak_count"),
        max_events_for_analysis=max_events,
        max_events_for_plots=max_events,
        runtime_config_data=runtime_config_data,
    )
    if result is None:
        if preview_only:
            return PeakTransition(
                status="No peaks were detected.",
                debug_payload={"rosetta_settings_preview": True},
            )
        return clear_peak_context(
            adapter=adapter, page_state=page_state, context=context, clear_table=True,
            table_data=table_data, status="Run completed with no detected peaks.", reason="run_action_failed",
        )

    warning = getattr(result, "warning", False)
    if preview_only:
        preview_payload = dict(result.peak_lines_payload, rosetta_settings_preview=True)
        page_state = adapter.update_peak_lines_payload(
            page_state=page_state,
            peak_lines_payload=preview_payload,
        )
        return PeakTransition(
            page_state=touch_peak_graph_revision(
                adapter=adapter, page_state=page_state, reason="settings_preview",
                process_name=target_process_name, process_settings=process_settings,
            ),
            status=result.status,
            debug_payload=preview_payload,
        )

    preserve_measured_rows = getattr(process, "allow_unassigned_sizes", False) and result.table_prefill_rows
    if warning and not preserve_measured_rows:
        if not getattr(process, "preserve_graph_payload_on_warning", False):
            return PeakTransition(
                status=result.status,
                debug_payload=result.peak_lines_payload if getattr(process, "supports_debug_diagnostics", False) else None,
            )

        page_state = adapter.update_peak_lines_payload(
            page_state=page_state, peak_lines_payload=result.peak_lines_payload,
        )
        clear_table = getattr(process, "clear_table_on_warning", False)
        page_state = touch_peak_graph_revision(
            adapter=adapter, page_state=page_state, reason="run_action_warning",
            process_name=target_process_name, process_settings=process_settings,
            state_changes={"peak_table_context": None} if clear_table else None,
        )
        table_rows = None
        if clear_table:
            table_rows = _update_peak_table(
                adapter=adapter, table_data=table_data,
                result=SimpleNamespace(clear_existing_table_peaks=True), context=context,
            )
        return PeakTransition(
            page_state=synchronize_page_state_table_rows(adapter=adapter, page_state=page_state, table_result=table_rows),
            table_rows=table_rows,
            status=result.status,
            debug_payload=result.peak_lines_payload,
        )

    return apply_peak_result(
        adapter=adapter, page_state=page_state, result=result, reason="run_action",
        table_data=table_data,
        context=context, process_settings=process_settings, status=result.status,
        debug_payload=result.peak_lines_payload,
    )
