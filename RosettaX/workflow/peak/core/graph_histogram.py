"""Peak graph histogram."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils import plottings
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.axis_ranges import (
    compute_stable_axis_range,
)

from ..scripts.base import (
    filter_edge_artifact_values,
)
from .graph_interaction import (
    axis_scale_selection_is_log,
)

if TYPE_CHECKING:
    from .graphing import PeakWorkflowGraphBuilder

from . import graph_overlays, graph_payload, graph_settings

logger = logging.getLogger(__name__)


def build_default_1d_histogram_figure(builder: PeakWorkflowGraphBuilder) -> go.Figure:
    """
    Build a fallback one dimensional histogram figure.
    """
    detector_column = graph_settings.get_first_required_detector_column(builder)

    if not detector_column:
        return plottings._make_info_figure(
            "Select a detector channel first.",
        )

    if builder._edge_artifact_filter_is_enabled():
        raw_values = np.asarray(
            column_copy(
                fcs_file_path=builder.backend.fcs_file_path,
                detector_column=str(detector_column),
                dtype=float,
                n=graph_settings.resolve_max_events_for_plots(builder),
            ),
            dtype=float,
        )

        filtered_values = filter_edge_artifact_values(
            values=raw_values,
            remove_min=True,
            remove_max=True,
        )

        if filtered_values.size == 0:
            return plottings._make_info_figure(
                "No finite events remain after filtering zeros and saturated values.",
            )

        histogram_values = (
            filtered_values[filtered_values > 0.0]
            if graph_settings.x_axis_is_log(builder)
            else filtered_values
        )

        if histogram_values.size == 0:
            return plottings._make_info_figure(
                "No positive events remain after filtering for the selected axis scale.",
            )

        if graph_settings.x_axis_is_log(builder):
            lower_edge = float(np.min(histogram_values))
            upper_edge = float(np.max(histogram_values))

            if lower_edge == upper_edge:
                upper_edge = lower_edge * 1.01

            histogram_edges = np.geomspace(
                lower_edge,
                upper_edge,
                num=graph_settings.resolve_number_of_bins(builder) + 1,
            )
            histogram_counts, histogram_edges = np.histogram(
                histogram_values,
                bins=histogram_edges,
            )
            histogram_centers = np.sqrt(histogram_edges[:-1] * histogram_edges[1:])
        else:
            histogram_counts, histogram_edges = np.histogram(
                histogram_values,
                bins=graph_settings.resolve_number_of_bins(builder),
            )
            histogram_centers = 0.5 * (histogram_edges[:-1] + histogram_edges[1:])

        histogram_result = plottings.HistogramResult(
            values=np.asarray(histogram_values, dtype=float),
            counts=np.asarray(histogram_counts, dtype=float),
            edges=np.asarray(histogram_edges, dtype=float),
            centers=np.asarray(histogram_centers, dtype=float),
        )
    else:
        histogram_result = plottings.build_histogram(
            fcs_file_path=builder.backend.fcs_file_path,
            detector_column=detector_column,
            n_bins_for_plots=graph_settings.resolve_number_of_bins(builder),
            max_events_for_analysis=graph_settings.resolve_max_events_for_plots(
                builder
            ),
            use_log_x_bins=graph_settings.x_axis_is_log(builder),
        )
    builder._stable_histogram_count_values = np.asarray(
        histogram_result.counts,
        dtype=float,
    )

    peak_positions = graph_payload.extract_x_positions_from_peak_lines_payload(builder)

    figure = plottings.build_histogram_figure(
        histogram_result=histogram_result,
        detector_column=detector_column,
        use_log_counts=axis_scale_selection_is_log(
            scale_selection=builder.yscale_selection,
            axis="y",
        ),
        peak_positions=peak_positions,
    )

    if builder._advanced_mode_is_enabled():
        figure = graph_overlays.add_1d_advanced_overlays(
            builder,
            figure=figure,
        )

    figure.update_layout(
        showlegend=False,
    )

    return figure


def apply_stable_1d_histogram_y_range(
    builder: PeakWorkflowGraphBuilder,
    *,
    figure: go.Figure,
) -> None:
    """
    Clamp 1D histogram y range using only histogram counts.

    Diagnostic overlays such as smoothed curves and threshold guide lines
    must not redefine the displayed histogram count range.
    """
    histogram_count_values = builder._stable_histogram_count_values

    if histogram_count_values is None:
        return

    y_range = compute_stable_axis_range(
        values=histogram_count_values,
        log_scale=graph_settings.y_axis_is_log(builder),
    )

    if y_range is None:
        return

    figure.update_yaxes(
        autorange=False,
        range=y_range,
    )
