"""Peak graph overlays."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objs as go

from .graph_interaction import (
    unique_finite_preserving_order,
)

if TYPE_CHECKING:
    from .graphing import PeakWorkflowGraphBuilder

from . import graph_payload

logger = logging.getLogger(__name__)


def add_1d_advanced_overlays(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add compact diagnostic overlays for 1D automatic peak detection.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return figure

    debug_payload = builder.peak_lines_payload.get("debug", {})

    if not isinstance(debug_payload, dict):
        return figure

    bin_centers = np.asarray(
        debug_payload.get("histogram_bin_centers", []),
        dtype=float,
    )

    smoothed_counts = np.asarray(
        debug_payload.get("smoothed_counts", []),
        dtype=float,
    )

    if bin_centers.size == 0 or smoothed_counts.size == 0:
        return figure

    if bin_centers.size != smoothed_counts.size:
        minimum_size = int(min(bin_centers.size, smoothed_counts.size))

        if minimum_size <= 0:
            return figure

        bin_centers = bin_centers[:minimum_size]
        smoothed_counts = smoothed_counts[:minimum_size]

    finite_mask = np.isfinite(bin_centers) & np.isfinite(smoothed_counts)

    if not np.any(finite_mask):
        return figure

    bin_centers = bin_centers[finite_mask]
    smoothed_counts = smoothed_counts[finite_mask]

    figure.add_trace(
        go.Scatter(
            x=bin_centers,
            y=smoothed_counts,
            mode="lines",
            name="Smoothed curve",
            line={
                "width": 2,
                "dash": "dot",
                "color": "rgba(30, 30, 30, 0.85)",
            },
            hovertemplate=("x=%{x:.6g}<br>smoothed=%{y:.6g}<extra></extra>"),
        )
    )

    minimum_prominence = debug_payload.get("minimum_prominence", None)

    try:
        minimum_prominence_value = float(minimum_prominence)
    except (TypeError, ValueError):
        minimum_prominence_value = None

    if minimum_prominence_value is not None and np.isfinite(minimum_prominence_value):
        figure.add_hline(
            y=minimum_prominence_value,
            line_dash="dash",
            line_width=1,
            line_color="rgba(120, 35, 35, 0.9)",
            annotation_text="Min prominence",
            annotation_position="top left",
        )

    return figure


def add_2d_overlays(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add gate overlays and selected peak markers.
    """
    figure = add_x_axis_gate_overlay(
        builder,
        figure=figure,
    )

    figure = add_y_axis_gate_overlay(
        builder,
        figure=figure,
    )

    figure = add_selected_peak_markers(
        builder,
        figure=figure,
    )

    return figure


def add_x_axis_gate_overlay(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add x axis lower and upper gate lines and shade rejected x regions.

    Accepted region
    ---------------
    x_lower_gate <= x <= x_upper_gate
    """
    x_lower_gate = graph_payload.extract_x_axis_lower_gate_from_peak_lines_payload(
        builder
    )
    x_upper_gate = graph_payload.extract_x_axis_upper_gate_from_peak_lines_payload(
        builder
    )

    if x_lower_gate is None and x_upper_gate is None:
        return figure

    add_out_of_x_interval_gate_shading(
        builder,
        figure=figure,
        lower_gate=x_lower_gate,
        upper_gate=x_upper_gate,
    )

    if x_lower_gate is not None:
        add_vertical_shape_line(
            builder,
            figure=figure,
            x=x_lower_gate,
            line_width=2,
            line_dash="dash",
        )

    if x_upper_gate is not None:
        add_vertical_shape_line(
            builder,
            figure=figure,
            x=x_upper_gate,
            line_width=2,
            line_dash="dash",
        )

    return figure


def add_y_axis_gate_overlay(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add y axis lower and upper gate lines and shade rejected y regions.

    Accepted region
    ---------------
    y_lower_gate <= y <= y_upper_gate
    """
    y_lower_gate = graph_payload.extract_y_axis_lower_gate_from_peak_lines_payload(
        builder
    )
    y_upper_gate = graph_payload.extract_y_axis_upper_gate_from_peak_lines_payload(
        builder
    )

    if y_lower_gate is None and y_upper_gate is None:
        return figure

    add_out_of_y_interval_gate_shading(
        builder,
        figure=figure,
        lower_gate=y_lower_gate,
        upper_gate=y_upper_gate,
    )

    if y_lower_gate is not None:
        add_horizontal_shape_line(
            builder,
            figure=figure,
            y=y_lower_gate,
            line_width=2,
            line_dash="dash",
        )

    if y_upper_gate is not None:
        add_horizontal_shape_line(
            builder,
            figure=figure,
            y=y_upper_gate,
            line_width=2,
            line_dash="dash",
        )

    if builder._is_rosetta_script_process():
        add_rosetta_y_gate_helper(
            builder,
            figure=figure,
            y_lower_gate=y_lower_gate,
            y_upper_gate=y_upper_gate,
        )

    return figure


def add_selected_peak_markers(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add selected peak markers without visible text labels.

    Labels are shown in hover only. This prevents long labels from shrinking
    the plot area.
    """
    points = graph_payload.extract_points_from_peak_lines_payload(builder)

    if not points:
        return figure

    labels = graph_payload.extract_labels_from_peak_lines_payload(
        builder,
        point_count=len(points),
    )

    if builder._is_rosetta_script_process():
        scatter_guide_positions = (
            graph_payload.extract_numeric_list_from_peak_lines_payload(
                builder,
                key="scatter_guide_positions",
            )
        )
        fluorescence_guide_positions = (
            graph_payload.extract_numeric_list_from_peak_lines_payload(
                builder,
                key="fluorescence_guide_positions",
            )
        )

        if not scatter_guide_positions:
            scatter_guide_positions = unique_finite_preserving_order(
                [point["x"] for point in points]
            )

        if not fluorescence_guide_positions:
            fluorescence_guide_positions = unique_finite_preserving_order(
                [
                    point["y"]
                    for point in points
                    if str(point.get("kind", "")).strip().lower() == "marker"
                ]
            )

        for scatter_position in scatter_guide_positions:
            add_vertical_shape_line(
                builder,
                figure=figure,
                x=scatter_position,
                line_width=2,
                line_dash="dash",
                line_color="#1f9d55",
            )

        if builder._advanced_mode_is_enabled():
            for fluorescence_position in fluorescence_guide_positions:
                add_horizontal_shape_line(
                    builder,
                    figure=figure,
                    y=fluorescence_position,
                    line_width=2,
                    line_dash="dash",
                    line_color="#d64545",
                )

    else:
        for point in points:
            add_vertical_shape_line(
                builder,
                figure=figure,
                x=point["x"],
                line_width=1,
                line_dash="dot",
                line_color=None,
            )

    figure.add_trace(
        go.Scatter(
            x=[point["x"] for point in points],
            y=[point["y"] for point in points],
            mode="markers",
            customdata=[
                [
                    labels[index],
                    points[index]["x"],
                    points[index]["y"],
                ]
                for index in range(
                    len(
                        points,
                    )
                )
            ],
            hovertemplate=(
                "%{customdata[0]}<br>"
                "x=%{customdata[1]:.6g}<br>"
                "y=%{customdata[2]:.6g}"
                "<extra></extra>"
            ),
            marker={
                "size": 10,
                "symbol": "x",
            },
            cliponaxis=True,
            name="Selected peaks",
        )
    )

    return figure


def add_2d_advanced_overlays(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Add the smoothed 2D density map used by automatic peak detection.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return figure

    debug_payload = builder.peak_lines_payload.get("debug", {})

    if not isinstance(debug_payload, dict):
        return figure

    debug_grid = debug_payload.get("debug_grid", {})

    if not isinstance(debug_grid, dict):
        return figure

    x_centers = np.asarray(
        debug_grid.get("x_centers", []),
        dtype=float,
    )
    y_centers = np.asarray(
        debug_grid.get("y_centers", []),
        dtype=float,
    )
    smoothed_histogram = np.asarray(
        debug_grid.get("smoothed_histogram", []),
        dtype=float,
    )

    if x_centers.size == 0 or y_centers.size == 0 or smoothed_histogram.size == 0:
        return figure

    if smoothed_histogram.ndim != 2:
        return figure

    if smoothed_histogram.shape != (
        x_centers.size,
        y_centers.size,
    ):
        return figure

    if not (
        np.all(np.isfinite(x_centers))
        and np.all(np.isfinite(y_centers))
        and np.all(np.isfinite(smoothed_histogram))
    ):
        return figure

    figure.add_trace(
        go.Heatmap(
            x=x_centers,
            y=y_centers,
            z=np.log10(
                smoothed_histogram.T + 1.0,
            ),
            colorscale="Turbo",
            opacity=0.50,
            showscale=False,
            hovertemplate=(
                "Smoothed density<br>"
                "x=%{x:.6g}<br>"
                "y=%{y:.6g}<br>"
                "log10(count+1)=%{z:.6g}<extra></extra>"
            ),
        )
    )

    figure.data = (
        figure.data[-1],
        *figure.data[:-1],
    )

    return figure


def add_out_of_x_interval_gate_shading(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    lower_gate: float | None,
    upper_gate: float | None,
) -> None:
    """
    Shade x regions outside the accepted interval.
    """
    visible_x_range = get_visible_axis_range(
        builder,
        figure=figure,
        axis_name="xaxis",
    )

    if visible_x_range is None:
        logger.debug(
            "Could not add x gate shading because visible x range is unavailable."
        )

        return

    visible_lower_x, visible_upper_x = visible_x_range

    if lower_gate is not None and np.isfinite(lower_gate):
        shaded_lower_x = float(
            visible_lower_x,
        )

        shaded_upper_x = min(
            float(
                lower_gate,
            ),
            float(
                visible_upper_x,
            ),
        )

        if shaded_upper_x > shaded_lower_x:
            figure.add_shape(
                type="rect",
                xref="x",
                yref="paper",
                x0=shaded_lower_x,
                x1=shaded_upper_x,
                y0=0.0,
                y1=1.0,
                fillcolor=builder.rejected_x_fill_color,
                line={
                    "width": 0,
                },
                layer="below",
            )

    if upper_gate is not None and np.isfinite(upper_gate):
        shaded_lower_x = max(
            float(
                upper_gate,
            ),
            float(
                visible_lower_x,
            ),
        )

        shaded_upper_x = float(
            visible_upper_x,
        )

        if shaded_upper_x > shaded_lower_x:
            figure.add_shape(
                type="rect",
                xref="x",
                yref="paper",
                x0=shaded_lower_x,
                x1=shaded_upper_x,
                y0=0.0,
                y1=1.0,
                fillcolor=builder.rejected_x_fill_color,
                line={
                    "width": 0,
                },
                layer="below",
            )


def add_out_of_y_interval_gate_shading(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    lower_gate: float | None,
    upper_gate: float | None,
) -> None:
    """
    Shade y regions outside the accepted interval.
    """
    visible_y_range = get_visible_axis_range(
        builder,
        figure=figure,
        axis_name="yaxis",
    )

    if visible_y_range is None:
        logger.debug(
            "Could not add y gate shading because visible y range is unavailable."
        )

        return

    visible_lower_y, visible_upper_y = visible_y_range

    if lower_gate is not None and np.isfinite(lower_gate):
        shaded_lower_y = float(
            visible_lower_y,
        )

        shaded_upper_y = min(
            float(
                lower_gate,
            ),
            float(
                visible_upper_y,
            ),
        )

        if shaded_upper_y > shaded_lower_y:
            figure.add_shape(
                type="rect",
                xref="paper",
                yref="y",
                x0=0.0,
                x1=1.0,
                y0=shaded_lower_y,
                y1=shaded_upper_y,
                fillcolor=builder.rejected_y_fill_color,
                line={
                    "width": 0,
                },
                layer="below",
            )


def add_rosetta_y_gate_helper(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    y_lower_gate: float | None,
    y_upper_gate: float | None,
) -> None:
    """
    Add explicit Rosetta helper bands for the accepted scatter gate and the
    fluorescence region above it.
    """
    visible_y_range = get_visible_axis_range(
        builder,
        figure=figure,
        axis_name="yaxis",
    )

    if visible_y_range is None:
        return

    visible_lower_y, visible_upper_y = visible_y_range

    accepted_lower_y = (
        float(y_lower_gate)
        if y_lower_gate is not None and np.isfinite(y_lower_gate)
        else float(visible_lower_y)
    )
    accepted_upper_y = (
        float(y_upper_gate)
        if y_upper_gate is not None and np.isfinite(y_upper_gate)
        else float(visible_upper_y)
    )

    accepted_lower_y = max(float(visible_lower_y), accepted_lower_y)
    accepted_upper_y = min(float(visible_upper_y), accepted_upper_y)

    if accepted_upper_y > accepted_lower_y:
        figure.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0.0,
            x1=1.0,
            y0=accepted_lower_y,
            y1=accepted_upper_y,
            fillcolor=builder.accepted_y_fill_color,
            line={"width": 0},
            layer="below",
        )

    if (
        y_upper_gate is not None
        and np.isfinite(y_upper_gate)
        and float(visible_upper_y) > float(y_upper_gate)
    ):
        fluorescence_lower_y = max(float(y_upper_gate), float(visible_lower_y))
        fluorescence_upper_y = float(visible_upper_y)

        if fluorescence_upper_y > fluorescence_lower_y:
            figure.add_shape(
                type="rect",
                xref="paper",
                yref="y",
                x0=0.0,
                x1=1.0,
                y0=fluorescence_lower_y,
                y1=fluorescence_upper_y,
                fillcolor=builder.fluorescence_helper_fill_color,
                line={"width": 0},
                layer="below",
            )


def add_vertical_shape_line(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    x: float,
    line_width: float,
    line_dash: str,
    line_color: str | None = None,
) -> None:
    """
    Add a vertical line as a shape, not as an annotation.
    """
    if not np.isfinite(
        float(
            x,
        )
    ):
        return

    figure.add_shape(
        type="line",
        xref="x",
        yref="paper",
        x0=float(
            x,
        ),
        x1=float(
            x,
        ),
        y0=0.0,
        y1=1.0,
        line={
            "width": line_width,
            "dash": line_dash,
            **(
                {
                    "color": line_color,
                }
                if isinstance(line_color, str) and line_color
                else {}
            ),
        },
        layer="above",
    )


def add_horizontal_shape_line(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    y: float,
    line_width: float,
    line_dash: str,
    line_color: str | None = None,
) -> None:
    """
    Add a horizontal line as a shape, not as an annotation.
    """
    if not np.isfinite(
        float(
            y,
        )
    ):
        return

    figure.add_shape(
        type="line",
        xref="paper",
        yref="y",
        x0=0.0,
        x1=1.0,
        y0=float(
            y,
        ),
        y1=float(
            y,
        ),
        line={
            "width": line_width,
            "dash": line_dash,
            **(
                {
                    "color": line_color,
                }
                if isinstance(line_color, str) and line_color
                else {}
            ),
        },
        layer="above",
    )


def get_visible_axis_range(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
    axis_name: str,
) -> tuple[float, float] | None:
    """
    Return the visible axis range in data coordinates.

    Plotly stores log axis ranges in log10 coordinates. Shape coordinates
    still use data coordinates, so the range is converted back when needed.
    """
    axis = getattr(
        figure.layout,
        axis_name,
        None,
    )

    if axis is None:
        return None

    axis_range = getattr(
        axis,
        "range",
        None,
    )

    if axis_range is None or len(axis_range) != 2:
        return None

    try:
        lower_value = float(
            axis_range[0],
        )

        upper_value = float(
            axis_range[1],
        )

    except (TypeError, ValueError):
        return None

    if not np.isfinite(lower_value) or not np.isfinite(upper_value):
        return None

    axis_type = getattr(
        axis,
        "type",
        None,
    )

    if axis_type == "log":
        lower_value = 10.0**lower_value
        upper_value = 10.0**upper_value

    if lower_value > upper_value:
        lower_value, upper_value = upper_value, lower_value

    return (
        float(
            lower_value,
        ),
        float(
            upper_value,
        ),
    )
