# -*- coding: utf-8 -*-

from typing import Any
import inspect

import numpy as np
import plotly.graph_objs as go

from RosettaX.workflow.peak_workflow.core import detectors
from RosettaX.workflow.peak_workflow.scripts import registry
from RosettaX.utils import casting
from RosettaX.utils import plottings
from RosettaX.utils.runtime_config import RuntimeConfig


def is_enabled(
    graph_toggle_value: Any,
) -> bool:
    """
    Return whether the graph should be displayed.
    """
    if isinstance(graph_toggle_value, str):
        return graph_toggle_value == "enabled"

    if isinstance(graph_toggle_value, (list, tuple, set)):
        return "enabled" in graph_toggle_value

    if isinstance(graph_toggle_value, bool):
        return graph_toggle_value

    return False


def scale_selection_is_log(
    scale_selection: Any,
) -> bool:
    """
    Return whether a checklist style scale selection requests log scale.
    """
    if isinstance(scale_selection, str):
        return scale_selection == "log"

    if isinstance(scale_selection, (list, tuple, set)):
        return "log" in scale_selection

    return False


def build_peak_workflow_graph_figure(
    *,
    backend: Any,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_ids: list[dict[str, Any]],
    detector_dropdown_values: list[Any],
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    graph_toggle_value: Any,
    xscale_selection: Any = None,
    yscale_selection: Any = None,
    nbins: Any = None,
    peak_lines_payload: Any = None,
    max_events_for_plots: Any = None,
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build the graph for the selected peak workflow process.
    """
    if not is_enabled(
        graph_toggle_value,
    ):
        return plottings._make_info_figure(
            "Graph disabled.",
        )

    if not str(uploaded_fcs_path or "").strip():
        return plottings._make_info_figure(
            "Upload an FCS file first.",
        )

    if backend is None:
        return plottings._make_info_figure(
            "No backend available for this file.",
        )

    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    process = registry.get_process_instance(
        process_name=resolved_process_name,
    )

    if process is None:
        return plottings._make_info_figure(
            "Select a valid peak process.",
        )

    detector_channels = detectors.resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
    )

    missing_channel_names = get_missing_detector_channel_names(
        process=process,
        detector_channels=detector_channels,
    )

    if missing_channel_names:
        return plottings._make_info_figure(
            build_missing_detector_message(
                missing_channel_names=missing_channel_names,
            )
        )

    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    resolved_number_of_bins = casting.as_int(
        nbins,
        default=runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        ),
        min_value=1,
        max_value=10_000,
    )

    resolved_max_events_for_plots = casting.as_int(
        max_events_for_plots,
        default=runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=10000,
        ),
        min_value=1,
        max_value=5_000_000,
    )

    process_settings = build_process_settings(
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        process_name=resolved_process_name,
    )

    figure = build_process_specific_figure(
        process=process,
        backend=backend,
        uploaded_fcs_path=uploaded_fcs_path,
        process_name=resolved_process_name,
        detector_channels=detector_channels,
        process_settings=process_settings,
        peak_lines_payload=peak_lines_payload,
        number_of_bins=resolved_number_of_bins,
        max_events_for_plots=resolved_max_events_for_plots,
        xscale_selection=xscale_selection,
        yscale_selection=yscale_selection,
        runtime_config_data=runtime_config_data,
    )

    figure.update_xaxes(
        type="log" if scale_selection_is_log(xscale_selection) else "linear",
    )

    figure.update_yaxes(
        type="log" if scale_selection_is_log(yscale_selection) else "linear",
    )

    apply_runtime_visualization_settings(
        figure=figure,
        runtime_config_data=runtime_config_data,
    )

    return figure


def build_process_specific_figure(
    *,
    process: Any,
    backend: Any,
    uploaded_fcs_path: Any,
    process_name: str,
    detector_channels: dict[str, Any],
    process_settings: dict[str, Any],
    peak_lines_payload: Any,
    number_of_bins: int,
    max_events_for_plots: int,
    xscale_selection: Any,
    yscale_selection: Any,
    runtime_config_data: Any,
) -> go.Figure:
    """
    Build a process specific figure.

    The function first delegates to process graph methods when they exist. If a
    process does not expose one, it falls back to the backend graph API.
    """
    for method_name in (
        "build_graph_figure",
        "build_figure",
        "build_plot",
    ):
        method = getattr(
            process,
            method_name,
            None,
        )

        if callable(method):
            figure = call_with_supported_arguments(
                method,
                backend=backend,
                uploaded_fcs_path=uploaded_fcs_path,
                process_name=process_name,
                detector_channels=detector_channels,
                process_settings=process_settings,
                peak_lines_payload=peak_lines_payload,
                n_bins_for_plots=number_of_bins,
                nbins=number_of_bins,
                max_events_for_plots=max_events_for_plots,
                max_events_for_analysis=max_events_for_plots,
                xscale_selection=xscale_selection,
                yscale_selection=yscale_selection,
                runtime_config_data=runtime_config_data,
            )

            if getattr(process, "graph_type", None) == "2d_scatter":
                return add_manual_2d_peak_annotations(
                    figure=figure,
                    peak_lines_payload=peak_lines_payload,
                )

            return figure

    graph_type = getattr(
        process,
        "graph_type",
        None,
    )

    if graph_type == "1d_histogram":
        return build_default_1d_histogram_figure(
            backend=backend,
            process=process,
            detector_channels=detector_channels,
            peak_lines_payload=peak_lines_payload,
            number_of_bins=number_of_bins,
            max_events_for_plots=max_events_for_plots,
            yscale_selection=yscale_selection,
        )

    if graph_type == "2d_scatter":
        return build_default_2d_scatter_figure(
            backend=backend,
            process=process,
            detector_channels=detector_channels,
            peak_lines_payload=peak_lines_payload,
            max_events_for_plots=max_events_for_plots,
        )

    return plottings._make_info_figure(
        "No graph implementation is available for this peak process.",
    )


def build_default_1d_histogram_figure(
    *,
    backend: Any,
    process: Any,
    detector_channels: dict[str, Any],
    peak_lines_payload: Any,
    number_of_bins: int,
    max_events_for_plots: int,
    yscale_selection: Any,
) -> go.Figure:
    """
    Build a fallback one dimensional histogram figure.
    """
    detector_column = get_first_required_detector_column(
        process=process,
        detector_channels=detector_channels,
    )

    if not detector_column:
        return plottings._make_info_figure(
            "Select a detector channel first.",
        )

    histogram_result = backend.build_histogram(
        detector_column=detector_column,
        n_bins_for_plots=number_of_bins,
        max_events_for_analysis=max_events_for_plots,
    )

    peak_positions = extract_x_positions_from_peak_lines_payload(
        peak_lines_payload=peak_lines_payload,
    )

    if hasattr(backend, "build_histogram_figure"):
        return backend.build_histogram_figure(
            histogram_result=histogram_result,
            detector_column=detector_column,
            use_log_counts=scale_selection_is_log(
                yscale_selection,
            ),
            peak_positions=peak_positions,
        )

    values = np.asarray(
        getattr(histogram_result, "values", []),
        dtype=float,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Histogram(
            x=values,
            nbinsx=int(number_of_bins),
            name=str(detector_column),
        )
    )

    if peak_positions:
        figure = plottings.add_vertical_lines(
            fig=figure,
            line_positions=peak_positions,
            line_labels=[
                f"Peak {index + 1}"
                for index in range(len(peak_positions))
            ],
        )

    figure.update_layout(
        xaxis_title=f"{detector_column} [a.u.]",
        yaxis_title="Counts",
        hovermode="closest",
    )

    return figure


def build_default_2d_scatter_figure(
    *,
    backend: Any,
    process: Any,
    detector_channels: dict[str, Any],
    peak_lines_payload: Any,
    max_events_for_plots: int,
) -> go.Figure:
    """
    Build a fallback two dimensional scatter figure.

    Manual 2D clicks are rendered as vertical guide lines at the clicked x
    positions, plus markers at the clicked coordinates.
    """
    required_channel_names = get_required_detector_channels(
        process=process,
    )

    if len(required_channel_names) < 2:
        return plottings._make_info_figure(
            "This process does not define two required detector channels.",
        )

    x_detector_column = detector_channels.get(
        required_channel_names[0],
    )

    y_detector_column = detector_channels.get(
        required_channel_names[1],
    )

    if not x_detector_column or not y_detector_column:
        return plottings._make_info_figure(
            "Select both detector channels first.",
        )

    if not hasattr(backend, "column_copy"):
        return plottings._make_info_figure(
            "The backend does not expose column_copy.",
        )

    x_values = backend.column_copy(
        str(x_detector_column),
        dtype=float,
        n=max_events_for_plots,
    )

    y_values = backend.column_copy(
        str(y_detector_column),
        dtype=float,
        n=max_events_for_plots,
    )

    x_values = np.asarray(
        x_values,
        dtype=float,
    )

    y_values = np.asarray(
        y_values,
        dtype=float,
    )

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)

    x_values = x_values[finite_mask]
    y_values = y_values[finite_mask]

    figure = go.Figure()

    figure.add_trace(
        go.Scattergl(
            x=x_values,
            y=y_values,
            mode="markers",
            marker={
                "size": 4,
                "opacity": 0.5,
            },
            name="Events",
        )
    )

    figure.update_layout(
        xaxis_title=f"{x_detector_column} [a.u.]",
        yaxis_title=f"{y_detector_column} [a.u.]",
        hovermode="closest",
    )

    return add_manual_2d_peak_annotations(
        figure=figure,
        peak_lines_payload=peak_lines_payload,
    )


def add_manual_2d_peak_annotations(
    *,
    figure: go.Figure,
    peak_lines_payload: Any,
) -> go.Figure:
    """
    Add manual 2D click annotations to a figure.

    Each clicked point is shown as:

    - a vertical guide line at x
    - a marker at x, y
    - a peak label
    """
    points = extract_points_from_peak_lines_payload(
        peak_lines_payload=peak_lines_payload,
    )

    if not points:
        return figure

    for point_index, point in enumerate(points):
        figure.add_vline(
            x=point["x"],
            line_width=1,
            line_dash="dash",
            annotation_text=f"Peak {point_index + 1}",
            annotation_position="top",
        )

    figure.add_trace(
        go.Scatter(
            x=[
                point["x"]
                for point in points
            ],
            y=[
                point["y"]
                for point in points
            ],
            mode="markers+text",
            text=[
                f"Peak {index + 1}"
                for index in range(len(points))
            ],
            textposition="top center",
            marker={
                "size": 10,
                "symbol": "x",
            },
            name="Selected peaks",
        )
    )

    return figure


def apply_runtime_visualization_settings(
    *,
    figure: go.Figure,
    runtime_config_data: Any,
) -> None:
    """
    Apply profile visualization settings to a peak workflow figure.

    Supported profile keys:

    - visualization.default_marker_size
    - visualization.default_line_width
    - visualization.default_font_size
    - visualization.default_tick_size
    - visualization.show_grid_by_default
    """
    default_marker_size = get_nested_config_float(
        runtime_config_data=runtime_config_data,
        path="visualization.default_marker_size",
        default=10.0,
    )

    default_line_width = get_nested_config_float(
        runtime_config_data=runtime_config_data,
        path="visualization.default_line_width",
        default=3.0,
    )

    default_font_size = get_nested_config_float(
        runtime_config_data=runtime_config_data,
        path="visualization.default_font_size",
        default=34.0,
    )

    default_tick_size = get_nested_config_float(
        runtime_config_data=runtime_config_data,
        path="visualization.default_tick_size",
        default=18.0,
    )

    show_grid_by_default = get_nested_config_bool(
        runtime_config_data=runtime_config_data,
        path="visualization.show_grid_by_default",
        default=False,
    )

    figure.update_layout(
        font={
            "size": default_font_size,
        },
        legend={
            "font": {
                "size": default_tick_size,
            },
        },
    )

    figure.update_xaxes(
        tickfont={
            "size": default_tick_size,
        },
        title_font={
            "size": default_font_size,
        },
        showgrid=show_grid_by_default,
    )

    figure.update_yaxes(
        tickfont={
            "size": default_tick_size,
        },
        title_font={
            "size": default_font_size,
        },
        showgrid=show_grid_by_default,
    )

    for trace in figure.data:
        apply_trace_visualization_settings(
            trace=trace,
            default_marker_size=default_marker_size,
            default_line_width=default_line_width,
        )

    for shape in figure.layout.shapes or []:
        if hasattr(shape, "line"):
            shape.line.width = default_line_width


def apply_trace_visualization_settings(
    *,
    trace: Any,
    default_marker_size: float,
    default_line_width: float,
) -> None:
    """
    Apply marker and line defaults to one Plotly trace.
    """
    trace_type = getattr(
        trace,
        "type",
        "",
    )

    if trace_type in (
        "scatter",
        "scattergl",
    ):
        if hasattr(trace, "marker"):
            trace.marker.size = default_marker_size

        if hasattr(trace, "line"):
            trace.line.width = default_line_width

    if trace_type == "bar":
        if hasattr(trace, "marker"):
            trace.marker.line.width = default_line_width

    if trace_type == "histogram":
        if hasattr(trace, "marker"):
            trace.marker.line.width = default_line_width


def get_nested_config_float(
    *,
    runtime_config_data: Any,
    path: str,
    default: float,
) -> float:
    """
    Return a float from a nested runtime config dictionary.
    """
    value = get_nested_config_value(
        runtime_config_data=runtime_config_data,
        path=path,
        default=default,
    )

    try:
        value_float = float(value)

    except (TypeError, ValueError):
        return float(default)

    if not np.isfinite(value_float):
        return float(default)

    return value_float


def get_nested_config_bool(
    *,
    runtime_config_data: Any,
    path: str,
    default: bool,
) -> bool:
    """
    Return a bool from a nested runtime config dictionary.
    """
    value = get_nested_config_value(
        runtime_config_data=runtime_config_data,
        path=path,
        default=default,
    )

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
            "enabled",
        )

    return bool(value)


def get_nested_config_value(
    *,
    runtime_config_data: Any,
    path: str,
    default: Any,
) -> Any:
    """
    Return a value from a nested dictionary using a dot separated path.
    """
    if not isinstance(runtime_config_data, dict):
        return default

    current_value: Any = runtime_config_data

    for key in path.split("."):
        if not isinstance(current_value, dict):
            return default

        if key not in current_value:
            return default

        current_value = current_value[key]

    return current_value


def get_missing_detector_channel_names(
    *,
    process: Any,
    detector_channels: dict[str, Any],
) -> list[str]:
    """
    Return required detector channels that do not have selected columns.
    """
    missing_channel_names: list[str] = []

    for channel_name in get_required_detector_channels(
        process=process,
    ):
        if not str(detector_channels.get(channel_name) or "").strip():
            missing_channel_names.append(
                str(channel_name),
            )

    return missing_channel_names


def build_missing_detector_message(
    *,
    missing_channel_names: list[str],
) -> str:
    """
    Build a missing detector message.
    """
    if len(missing_channel_names) == 1:
        return f"Select the {missing_channel_names[0]} detector channel first."

    return "Select the required detector channels first."


def get_required_detector_channels(
    *,
    process: Any,
) -> list[str]:
    """
    Return required detector channel names for a process.
    """
    if hasattr(process, "get_required_detector_channels"):
        channel_names = process.get_required_detector_channels()

        if channel_names is None:
            return []

        return [
            str(channel_name)
            for channel_name in channel_names
        ]

    channel_names = getattr(
        process,
        "required_detector_channels",
        [],
    )

    if channel_names is None:
        return []

    return [
        str(channel_name)
        for channel_name in channel_names
    ]


def get_first_required_detector_column(
    *,
    process: Any,
    detector_channels: dict[str, Any],
) -> Any:
    """
    Return the detector column for the first required channel.
    """
    for channel_name in get_required_detector_channels(
        process=process,
    ):
        detector_column = detector_channels.get(
            channel_name,
        )

        if str(detector_column or "").strip():
            return detector_column

    return None


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
    ):
        if process_setting_id.get("process") != resolved_process_name:
            continue

        setting_name = process_setting_id.get("setting")

        if not isinstance(setting_name, str):
            continue

        process_settings[setting_name] = process_setting_value

    return process_settings


def extract_x_positions_from_peak_lines_payload(
    *,
    peak_lines_payload: Any,
) -> list[float]:
    """
    Extract x positions from a peak line payload.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    candidate_values = (
        peak_lines_payload.get("x_positions")
        or peak_lines_payload.get("positions")
        or []
    )

    if not candidate_values and isinstance(peak_lines_payload.get("points"), list):
        candidate_values = [
            point.get("x")
            for point in peak_lines_payload["points"]
            if isinstance(point, dict)
        ]

    x_positions: list[float] = []

    for value in candidate_values:
        try:
            x_positions.append(
                float(value),
            )

        except (TypeError, ValueError):
            continue

    return x_positions


def extract_points_from_peak_lines_payload(
    *,
    peak_lines_payload: Any,
) -> list[dict[str, float]]:
    """
    Extract two dimensional points from a peak line payload.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    points = peak_lines_payload.get("points")

    if isinstance(points, list):
        resolved_points: list[dict[str, float]] = []

        for point in points:
            if not isinstance(point, dict):
                continue

            try:
                resolved_points.append(
                    {
                        "x": float(point["x"]),
                        "y": float(point["y"]),
                    }
                )

            except (KeyError, TypeError, ValueError):
                continue

        return resolved_points

    x_positions = peak_lines_payload.get("x_positions") or []
    y_positions = peak_lines_payload.get("y_positions") or []

    resolved_points: list[dict[str, float]] = []

    for x_value, y_value in zip(
        x_positions,
        y_positions,
    ):
        try:
            resolved_points.append(
                {
                    "x": float(x_value),
                    "y": float(y_value),
                }
            )

        except (TypeError, ValueError):
            continue

    return resolved_points


def call_with_supported_arguments(
    callable_object: Any,
    **candidate_arguments: Any,
) -> Any:
    """
    Call a function with only the keyword arguments it accepts.
    """
    signature = inspect.signature(
        callable_object,
    )

    accepted_arguments: dict[str, Any] = {}

    accepts_arbitrary_keywords = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )

    if accepts_arbitrary_keywords:
        return callable_object(
            **candidate_arguments,
        )

    for argument_name, argument_value in candidate_arguments.items():
        if argument_name in signature.parameters:
            accepted_arguments[argument_name] = argument_value

    return callable_object(
        **accepted_arguments,
    )