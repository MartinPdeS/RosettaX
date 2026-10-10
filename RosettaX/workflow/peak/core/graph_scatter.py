"""Peak graph scatter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import casting, plottings
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.axis_ranges import (
    apply_stable_2d_axis_ranges,
)
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph

from ..scripts.base import (
    filter_edge_artifact_pairs,
)

if TYPE_CHECKING:
    from .graphing import PeakWorkflowGraphBuilder

from . import graph_overlays, graph_settings

logger = logging.getLogger(__name__)


def build_default_2d_scatter_figure(builder: PeakWorkflowGraphBuilder) -> go.Figure:
    """
    Build a fallback two dimensional scatter figure.

    Event density is shown through marker color. The density is estimated with a
    two dimensional histogram, and for log axes the density is computed in log10
    space so that the color mapping follows the displayed geometry.
    """
    required_channel_names = graph_settings.get_required_detector_channels(builder)

    if len(required_channel_names) < 2:
        return plottings._make_info_figure(
            "This process does not define two required detector channels.",
        )

    x_detector_column = builder.detector_channels.get(
        required_channel_names[0],
    )

    y_detector_column = builder.detector_channels.get(
        required_channel_names[1],
    )

    if not x_detector_column or not y_detector_column:
        return plottings._make_info_figure(
            "Select both detector channels first.",
        )

    payload_plot_values = extract_plot_values_from_peak_lines_payload(builder)

    if payload_plot_values is not None:
        x_values, y_values = payload_plot_values
    else:
        x_values = np.asarray(
            column_copy(
                fcs_file_path=builder.backend.fcs_file_path,
                detector_column=str(
                    x_detector_column,
                ),
                dtype=float,
                n=graph_settings.resolve_max_events_for_plots(builder),
            ),
            dtype=float,
        )

        y_values = np.asarray(
            column_copy(
                fcs_file_path=builder.backend.fcs_file_path,
                detector_column=str(
                    y_detector_column,
                ),
                dtype=float,
                n=graph_settings.resolve_max_events_for_plots(builder),
            ),
            dtype=float,
        )

    if builder._edge_artifact_filter_is_enabled():
        x_values, y_values = filter_edge_artifact_pairs(
            x_values=x_values,
            y_values=y_values,
            remove_x_min=True,
            remove_x_max=True,
            remove_y_min=True,
            remove_y_max=False,
        )

    filtered_x_values, filtered_y_values = filter_2d_values_for_axis_scale(
        builder,
        x_values=x_values,
        y_values=y_values,
    )

    if filtered_x_values.size == 0 or filtered_y_values.size == 0:
        return plottings._make_info_figure(
            "No finite events are available for the selected axis scale.",
        )

    density_values = compute_2d_density_values(
        builder,
        x_values=filtered_x_values,
        y_values=filtered_y_values,
        x_log_scale=graph_settings.x_axis_is_log(builder),
        y_log_scale=graph_settings.y_axis_is_log(builder),
        colormap_log_scale=colormap_is_log(builder),
        number_of_bins=resolve_density_colormap_number_of_bins(builder),
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scattergl(
            x=filtered_x_values,
            y=filtered_y_values,
            mode="markers",
            name="Events",
            marker={
                "size": graph_settings.get_default_marker_size(builder),
                "opacity": graph_settings.get_default_marker_opacity(builder),
                "color": density_values,
                "colorscale": "Turbo",
                "showscale": False,
            },
            customdata=density_values,
            hovertemplate=(
                f"{x_detector_column}=%{{x:.6g}}<br>"
                f"{y_detector_column}=%{{y:.6g}}<br>"
                "density=%{customdata:.6g}"
                "<extra></extra>"
            ),
        )
    )

    Scatter2DGraph.apply_formatting(
        figure=figure,
        title=str(
            getattr(
                builder.process,
                "process_label",
                "2D peak workflow scatter",
            )
        ),
        x_axis_title=f"{x_detector_column} [a.u.]",
        y_axis_title=f"{y_detector_column} [a.u.]",
        x_axis_type="log" if graph_settings.x_axis_is_log(builder) else "linear",
        y_axis_type="log" if graph_settings.y_axis_is_log(builder) else "linear",
        show_grid=graph_settings.show_grid_by_default(builder),
        hovermode="closest",
        uirevision=f"peak_workflow_{builder.resolved_process_name}_2d_scatter",
    )

    figure = apply_stable_2d_axis_ranges(
        figure=figure,
        x_values=filtered_x_values,
        y_values=filtered_y_values,
        x_log_scale=graph_settings.x_axis_is_log(builder),
        y_log_scale=graph_settings.y_axis_is_log(builder),
    )

    figure = graph_overlays.add_2d_overlays(
        builder,
        figure=figure,
    )

    if builder._advanced_mode_is_enabled():
        figure = graph_overlays.add_2d_advanced_overlays(
            builder,
            figure=figure,
        )

    figure.update_layout(
        showlegend=False,
    )

    return figure


def extract_plot_values_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Extract plot event coordinates from the peak payload when provided.

    This lets a process override the displayed point cloud so the graph can
    reflect process-specific filtering such as Rosetta saturated-event removal.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return None

    raw_x_values = builder.peak_lines_payload.get("plot_x_values")
    raw_y_values = builder.peak_lines_payload.get("plot_y_values")

    if not isinstance(raw_x_values, list) or not isinstance(raw_y_values, list):
        return None

    resolved_x_values: list[float] = []
    resolved_y_values: list[float] = []

    for raw_x_value, raw_y_value in zip(
        raw_x_values,
        raw_y_values,
        strict=False,
    ):
        try:
            x_value = float(raw_x_value)
            y_value = float(raw_y_value)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(x_value) or not np.isfinite(y_value):
            continue

        resolved_x_values.append(x_value)
        resolved_y_values.append(y_value)

    if not resolved_x_values or not resolved_y_values:
        return None

    return (
        np.asarray(resolved_x_values, dtype=float),
        np.asarray(resolved_y_values, dtype=float),
    )


def compute_2d_density_values(
    builder: PeakWorkflowGraphBuilder,
    *,
    x_values: Any,
    y_values: Any,
    x_log_scale: bool,
    y_log_scale: bool,
    colormap_log_scale: bool,
    number_of_bins: int,
) -> np.ndarray:
    """
    Compute local point density values for 2D scatter color mapping.
    """
    x_array = np.asarray(
        x_values,
        dtype=float,
    )

    y_array = np.asarray(
        y_values,
        dtype=float,
    )

    if x_array.size == 0 or y_array.size == 0:
        return np.asarray(
            [],
            dtype=float,
        )

    density_x_values = x_array.copy()
    density_y_values = y_array.copy()

    if x_log_scale:
        density_x_values = np.log10(
            density_x_values,
        )

    if y_log_scale:
        density_y_values = np.log10(
            density_y_values,
        )

    finite_mask = np.isfinite(
        density_x_values,
    ) & np.isfinite(
        density_y_values,
    )

    if not np.all(finite_mask):
        density_values = np.zeros(
            x_array.shape,
            dtype=float,
        )

        valid_density_values = compute_2d_density_values(
            builder,
            x_values=x_array[finite_mask],
            y_values=y_array[finite_mask],
            x_log_scale=x_log_scale,
            y_log_scale=y_log_scale,
            colormap_log_scale=colormap_log_scale,
            number_of_bins=number_of_bins,
        )

        density_values[finite_mask] = valid_density_values

        return density_values

    if x_array.size < 2:
        return np.ones(
            x_array.shape,
            dtype=float,
        )

    histogram, x_edges, y_edges = np.histogram2d(
        density_x_values,
        density_y_values,
        bins=number_of_bins,
    )

    x_bin_indices = (
        np.searchsorted(
            x_edges,
            density_x_values,
            side="right",
        )
        - 1
    )

    y_bin_indices = (
        np.searchsorted(
            y_edges,
            density_y_values,
            side="right",
        )
        - 1
    )

    x_bin_indices = np.clip(
        x_bin_indices,
        0,
        histogram.shape[0] - 1,
    )

    y_bin_indices = np.clip(
        y_bin_indices,
        0,
        histogram.shape[1] - 1,
    )

    raw_density_values = histogram[
        x_bin_indices,
        y_bin_indices,
    ]

    if colormap_log_scale:
        return np.log10(
            raw_density_values + 1.0,
        )

    return raw_density_values.astype(
        float,
        copy=False,
    )


def resolve_density_colormap_number_of_bins(builder: PeakWorkflowGraphBuilder) -> int:
    """
    Resolve the number of bins used for 2D density color mapping.
    """
    default_number_of_bins = graph_settings.resolve_number_of_bins(builder)

    return casting.as_int(
        graph_settings.get_nested_config_value(
            builder,
            path="visualization.density_colormap_n_bins",
            default=default_number_of_bins,
        ),
        default=default_number_of_bins,
        min_value=10,
        max_value=1000,
    )


def filter_2d_values_for_axis_scale(
    builder: PeakWorkflowGraphBuilder,
    *,
    x_values: Any,
    y_values: Any,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Filter event values using finite and log scale constraints.
    """
    x_array = np.asarray(
        x_values,
        dtype=float,
    )

    y_array = np.asarray(
        y_values,
        dtype=float,
    )

    finite_mask = (
        np.isfinite(
            x_array,
        )
        & np.isfinite(
            y_array,
        )
        & (x_array != 0.0)
        & (y_array != 0.0)
    )

    if graph_settings.x_axis_is_log(builder):
        finite_mask = finite_mask & (x_array > 0.0)

    if graph_settings.y_axis_is_log(builder):
        finite_mask = finite_mask & (y_array > 0.0)

    return (
        x_array[finite_mask],
        y_array[finite_mask],
    )


def build_scatter2d_axis_scale_toggle_values(
    builder: PeakWorkflowGraphBuilder,
) -> list[str]:
    """
    Convert peak workflow x/y scale selections into Scatter2DGraph values.
    """
    axis_scale_toggle_values: list[str] = []

    if graph_settings.x_axis_is_log(builder):
        axis_scale_toggle_values.append(
            Scatter2DGraph.x_log_value,
        )

    if graph_settings.y_axis_is_log(builder):
        axis_scale_toggle_values.append(
            Scatter2DGraph.y_log_value,
        )

    return axis_scale_toggle_values


def colormap_is_log(builder: PeakWorkflowGraphBuilder) -> bool:
    """
    Return whether the 2D density colormap should use logarithmic scaling.
    """
    if isinstance(builder.xscale_selection, (list, tuple, set)):
        return Scatter2DGraph.colormap_log_value in builder.xscale_selection

    return False
