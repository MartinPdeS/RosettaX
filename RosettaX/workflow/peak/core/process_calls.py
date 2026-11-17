"""Invoke peak processes with the context their signatures support."""

import inspect
import logging
from typing import Any

logger = logging.getLogger(__name__)


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
    return _call_process_method(
        process=process, method_name="run_automatic_action", candidate_arguments={
            "backend": backend,
            "detector_channels": detector_channels,
            "process_settings": process_settings,
            "peak_count": peak_count,
            "max_events_for_analysis": max_events_for_analysis,
            "max_events_for_plots": max_events_for_plots,
            "runtime_config_data": runtime_config_data,
        },
    )



def call_add_clicked_peak_with_supported_arguments(
    *,
    process: Any,
    click_data: Any,
    selected_data: Any,
    existing_peak_lines_payload: Any,
    backend: Any,
    detector_channels: dict[str, Any],
    process_settings: dict[str, Any],
    runtime_config_data: Any,
    axis_scale_toggle_values: Any,
) -> Any:
    """
    Call ``process.add_clicked_peak`` with only the arguments it supports.
    """
    return _call_process_method(
        process=process, method_name="add_clicked_peak", candidate_arguments={
            "click_data": click_data,
            "selected_data": selected_data,
            "existing_peak_lines_payload": existing_peak_lines_payload,
            "backend": backend,
            "detector_channels": detector_channels,
            "process_settings": process_settings,
            "runtime_config_data": runtime_config_data,
            "axis_scale_toggle_values": axis_scale_toggle_values,
        },
    )


def _call_process_method(
    *, process: Any, method_name: str, candidate_arguments: dict[str, Any],
) -> Any:
    """Call a process method with the keyword arguments it supports.

    Parameters
    ----------
    process : Any
        Selected peak process.
    method_name : str
        Name of the optional method to call.
    candidate_arguments : dict[str, Any]
        Available execution context.

    Returns
    -------
    Any
        The process result, or None if the method is unavailable.
    """
    method = getattr(process, method_name, None)
    if not callable(method):
        logger.debug("Process %r does not implement %s.", getattr(process, "process_name", process), method_name)
        return None
    signature = inspect.signature(method)
    accepts_arbitrary_keywords = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    arguments = candidate_arguments if accepts_arbitrary_keywords else {
        name: value for name, value in candidate_arguments.items()
        if name in signature.parameters
    }
    return method(**arguments)
