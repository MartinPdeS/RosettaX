"""Peak graph settings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import casting, plottings

from .graph_interaction import (
    axis_scale_selection_is_log,
    scale_selection_is_log,
)

if TYPE_CHECKING:
    from .graphing import PeakWorkflowGraphBuilder

logger = logging.getLogger(__name__)


def apply_axis_types(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> None:
    """
    Apply selected axis scale types.
    """
    figure.update_xaxes(
        type="log" if x_axis_is_log(builder) else "linear",
    )

    figure.update_yaxes(
        type="log" if y_axis_is_log(builder) else "linear",
    )


def apply_runtime_visualization_settings(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> None:
    """
    Apply profile visualization settings to a peak workflow figure.
    """
    default_marker_size = get_default_marker_size(builder)
    default_marker_opacity = get_default_marker_opacity(builder)

    default_line_width = get_nested_config_float(
        builder,
        path="visualization.default_line_width",
        default=3.0,
    )

    default_font_size = get_nested_config_float(
        builder,
        path="visualization.default_font_size",
        default=34.0,
    )

    default_tick_size = get_nested_config_float(
        builder,
        path="visualization.default_tick_size",
        default=18.0,
    )

    show_grid_by_default = resolve_show_grid_by_default(builder)

    plottings.apply_default_visual_style(
        figure,
        marker_size=default_marker_size,
        line_width=default_line_width,
        font_size=default_font_size,
        tick_size=default_tick_size,
        show_grid=show_grid_by_default,
    )

    for trace in figure.data:
        apply_trace_visualization_settings(
            builder,
            trace=trace,
            default_marker_size=default_marker_size,
            default_marker_opacity=default_marker_opacity,
            default_line_width=default_line_width,
        )

    for shape in figure.layout.shapes or []:
        if hasattr(shape, "line"):
            shape.line.width = default_line_width


def apply_trace_visualization_settings(
    builder: PeakWorkflowGraphBuilder,
    *,
    trace: Any,
    default_marker_size: float,
    default_marker_opacity: float,
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
            trace.marker.opacity = default_marker_opacity

        if hasattr(trace, "line"):
            trace.line.width = default_line_width

    if trace_type == "bar" and hasattr(trace, "marker"):
        trace.marker.line.width = default_line_width

    if trace_type == "histogram" and hasattr(trace, "marker"):
        trace.marker.line.width = default_line_width


def resolve_number_of_bins(builder: PeakWorkflowGraphBuilder) -> int:
    """
    Resolve the number of bins used for 1D histogram figures.
    """
    return casting.as_int(
        builder.nbins,
        default=builder.runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        ),
        min_value=1,
        max_value=10_000,
    )


def resolve_max_events_for_plots(builder: PeakWorkflowGraphBuilder) -> int:
    """
    Resolve the maximum number of events shown in graphs.
    """
    return casting.as_int(
        builder.max_events_for_plots,
        default=builder.runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=10000,
        ),
        min_value=1,
        max_value=5_000_000,
    )


def get_required_detector_channels(builder: PeakWorkflowGraphBuilder) -> list[str]:
    """
    Return required detector channel names for the selected process.
    """
    if hasattr(builder.process, "get_required_detector_channels"):
        channel_names = builder.process.get_required_detector_channels()

        if channel_names is None:
            return []

        return [
            str(
                channel_name,
            )
            for channel_name in channel_names
        ]

    channel_names = getattr(
        builder.process,
        "required_detector_channels",
        [],
    )

    if channel_names is None:
        return []

    return [
        str(
            channel_name,
        )
        for channel_name in channel_names
    ]


def get_first_required_detector_column(builder: PeakWorkflowGraphBuilder) -> Any:
    """
    Return the detector column for the first required channel.
    """
    for channel_name in get_required_detector_channels(builder):
        detector_column = builder.detector_channels.get(
            channel_name,
        )

        if str(detector_column or "").strip():
            return detector_column

    return None


def x_axis_is_log(builder: PeakWorkflowGraphBuilder) -> bool:
    """
    Return whether x axis log scale is enabled.
    """
    xscale_selection = getattr(
        builder,
        "xscale_selection",
        None,
    )

    return scale_selection_is_log(
        xscale_selection,
    ) or axis_scale_selection_is_log(
        scale_selection=xscale_selection,
        axis="x",
    )


def y_axis_is_log(builder: PeakWorkflowGraphBuilder) -> bool:
    """
    Return whether y axis log scale is enabled.
    """
    yscale_selection = getattr(
        builder,
        "yscale_selection",
        None,
    )

    return scale_selection_is_log(
        yscale_selection,
    ) or axis_scale_selection_is_log(
        scale_selection=yscale_selection,
        axis="y",
    )


def get_default_marker_size(builder: PeakWorkflowGraphBuilder) -> float:
    """
    Return default marker size from runtime config.
    """
    configured_value = get_nested_config_float(
        builder,
        path="visualization.default_marker_size",
        default=10.0,
    )
    if builder.marker_size is not None:
        configured_value = casting.as_float(builder.marker_size) or configured_value
    return max(1.0, min(24.0, float(configured_value)))


def get_default_marker_opacity(builder: PeakWorkflowGraphBuilder) -> float:
    """
    Return default marker opacity from runtime config.
    """
    configured_value = get_nested_config_float(
        builder,
        path="visualization.default_marker_opacity",
        default=0.72,
    )
    if builder.marker_opacity is not None:
        configured_value = casting.as_float(builder.marker_opacity) or configured_value
    return max(0.05, min(1.0, float(configured_value)))


def resolve_show_grid_by_default(builder: PeakWorkflowGraphBuilder) -> bool:
    """
    Return whether grid lines should be shown by default.
    """
    return get_nested_config_bool(
        builder,
        path="visualization.show_grid_by_default",
        default=False,
    )


def get_nested_config_float(
    builder: PeakWorkflowGraphBuilder,
    *,
    path: str,
    default: float,
) -> float:
    """
    Return a float from a nested runtime config dictionary.
    """
    value = get_nested_config_value(
        builder,
        path=path,
        default=default,
    )

    try:
        value_float = float(
            value,
        )

    except (TypeError, ValueError):
        return float(
            default,
        )

    if not np.isfinite(value_float):
        return float(
            default,
        )

    return value_float


def get_nested_config_bool(
    builder: PeakWorkflowGraphBuilder,
    *,
    path: str,
    default: bool,
) -> bool:
    """
    Return a bool from a nested runtime config dictionary.
    """
    value = get_nested_config_value(
        builder,
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

    return bool(
        value,
    )


def get_nested_config_value(
    builder: PeakWorkflowGraphBuilder,
    *,
    path: str,
    default: Any,
) -> Any:
    """
    Return a value from a nested dictionary using a dot separated path.
    """
    if not isinstance(builder.runtime_config_data, dict):
        return default

    current_value: Any = builder.runtime_config_data

    for key in path.split("."):
        if not isinstance(current_value, dict):
            return default

        if key not in current_value:
            return default

        current_value = current_value[key]

    return current_value
