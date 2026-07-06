# -*- coding: utf-8 -*-

from typing import Any, Optional
import inspect
import logging

import numpy as np
import plotly.graph_objs as go

from . import detectors
from .rosetta_annotations import (
    add_rosetta_scatter_guide_annotations,
    extract_rosetta_scatter_guide_annotations,
)
from .. import registry
from RosettaX.utils import casting, plottings
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph

from ..scripts.base import (
    filter_edge_artifact_pairs,
    filter_edge_artifact_values,
    resolve_edge_artifact_filter_enabled,
)


logger = logging.getLogger(__name__)

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
    Return whether a legacy scale selection requests generic log scale.

    Compatibility wrapper for older peak workflow code.
    """
    if isinstance(scale_selection, str):
        return scale_selection == "log"

    if isinstance(scale_selection, (list, tuple, set)):
        return "log" in scale_selection

    return False


def axis_scale_selection_is_log(
    *,
    scale_selection: Any,
    axis: str,
) -> bool:
    """
    Return whether one axis is configured for log scaling.
    """
    expected_toggle = (
        Scatter2DGraph.x_log_value
        if axis == "x"
        else Scatter2DGraph.y_log_value
    )

    if isinstance(scale_selection, str):
        return scale_selection in {
            "log",
            expected_toggle,
        }

    if isinstance(scale_selection, (list, tuple, set)):
        return (
            "log" in scale_selection
            or expected_toggle in scale_selection
        )

    return False


def compute_stable_axis_range(
    *,
    values: Any,
    log_scale: bool,
) -> Optional[list[float]]:
    """
    Compute a robust Plotly axis range from finite data values.

    For log axes, Plotly expects the axis range in log10 coordinates.

    This remains here because peak overlays need the visible data range before
    gate shading is added.
    """
    value_array = np.asarray(
        values,
        dtype=float,
    )

    value_array = value_array[
        np.isfinite(
            value_array,
        )
    ]

    if log_scale:
        value_array = value_array[
            value_array > 0.0
        ]

    if value_array.size < 2:
        return None

    lower_value, upper_value = np.quantile(
        value_array,
        [
            0.001,
            0.999,
        ],
    )

    if not np.isfinite(lower_value) or not np.isfinite(upper_value):
        return None

    if lower_value == upper_value:
        span = abs(lower_value) * 0.05

        if span == 0.0:
            span = 1.0

        lower_value -= span
        upper_value += span

    if log_scale:
        lower_value = max(
            lower_value,
            np.nextafter(
                0.0,
                1.0,
            ),
        )

        upper_value = max(
            upper_value,
            lower_value * 1.01,
        )

        return [
            float(
                np.log10(
                    lower_value,
                )
            ),
            float(
                np.log10(
                    upper_value,
                )
            ),
        ]

    padding = 0.05 * float(
        upper_value - lower_value,
    )

    return [
        float(
            lower_value - padding,
        ),
        float(
            upper_value + padding,
        ),
    ]


def apply_stable_2d_axis_ranges(
    *,
    figure: go.Figure,
    x_values: Any,
    y_values: Any,
    x_log_scale: bool,
    y_log_scale: bool,
) -> go.Figure:
    """
    Clamp 2D scatter plot ranges using only finite event data.

    Peak markers, gate overlays, helper traces, and annotations must not define
    the displayed range.
    """
    x_range = compute_stable_axis_range(
        values=x_values,
        log_scale=x_log_scale,
    )

    y_range = compute_stable_axis_range(
        values=y_values,
        log_scale=y_log_scale,
    )

    if x_range is not None:
        figure.update_xaxes(
            autorange=False,
            range=x_range,
        )

    if y_range is not None:
        figure.update_yaxes(
            autorange=False,
            range=y_range,
        )

    return figure


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
    advanced_mode_value: Any = None,
    data_filter_value: Any = None,
    xscale_selection: Any = None,
    yscale_selection: Any = None,
    nbins: Any = None,
    peak_lines_payload: Any = None,
    max_events_for_plots: Any = None,
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build the graph for the selected peak workflow process.

    This function is the public API used by the Dash callback. The implementation
    is delegated to PeakWorkflowGraphBuilder.
    """
    return PeakWorkflowGraphBuilder(
        backend=backend,
        uploaded_fcs_path=uploaded_fcs_path,
        process_name=process_name,
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        graph_toggle_value=graph_toggle_value,
        advanced_mode_value=advanced_mode_value,
        data_filter_value=data_filter_value,
        xscale_selection=xscale_selection,
        yscale_selection=yscale_selection,
        nbins=nbins,
        peak_lines_payload=peak_lines_payload,
        max_events_for_plots=max_events_for_plots,
        runtime_config_data=runtime_config_data,
    ).build()


def build_peak_workflow_uirevision(
    *,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_values: list[Any],
    xscale_selection: Any,
    yscale_selection: Any,
) -> str:
    """
    Build a stable Plotly UI revision token for peak workflow graphs.

    Preserve the current zoom/pan only when the user is still looking at the
    same underlying graph identity: same file, same process, same detector
    selection, and same axis scale modes.

    Changes such as overlays, helper traces, peak payload updates, or histogram
    bin counts should not invalidate the interaction state.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    normalized_detector_values = tuple(
        str(value or "").strip()
        for value in (
            detector_dropdown_values
            if isinstance(detector_dropdown_values, list)
            else []
        )
    )

    return repr(
        (
            "peak_workflow_graph",
            str(uploaded_fcs_path or ""),
            str(resolved_process_name or ""),
            normalized_detector_values,
            bool(
                axis_scale_selection_is_log(
                    scale_selection=xscale_selection,
                    axis="x",
                )
            ),
            bool(
                axis_scale_selection_is_log(
                    scale_selection=yscale_selection,
                    axis="y",
                )
            ),
        )
    )


def apply_peak_workflow_interaction_revision(
    *,
    figure: go.Figure,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_values: list[Any],
    xscale_selection: Any,
    yscale_selection: Any,
) -> go.Figure:
    """
    Apply a stable Plotly interaction contract to a peak workflow figure.
    """
    figure.update_layout(
        uirevision=build_peak_workflow_uirevision(
            uploaded_fcs_path=uploaded_fcs_path,
            process_name=process_name,
            detector_dropdown_values=detector_dropdown_values,
            xscale_selection=xscale_selection,
            yscale_selection=yscale_selection,
        ),
    )

    return figure


def add_peak_workflow_post_layout_overlays(
    *,
    figure: go.Figure,
    process_name: Any,
    peak_lines_payload: Any,
) -> go.Figure:
    """
    Add overlays that must run after callback-level layout and trace updates.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    if not _is_rosetta_script_process_name(
        resolved_process_name,
    ):
        return figure

    process = registry.get_process_instance(
        process_name=resolved_process_name,
    )

    if getattr(process, "graph_type", "2d_scatter") != "2d_scatter":
        return figure

    annotation_entries = extract_rosetta_scatter_guide_annotations(
        peak_lines_payload=peak_lines_payload,
    )

    if not annotation_entries:
        return figure

    return add_rosetta_scatter_guide_annotations(
        figure=figure,
        annotation_entries=annotation_entries,
    )


def unique_finite_preserving_order(
    values: list[Any],
) -> list[float]:
    """
    Return finite floats in first-seen order with near-duplicates collapsed.
    """
    resolved_values: list[float] = []

    for raw_value in values:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(value):
            continue

        if any(
            np.isclose(
                value,
                existing_value,
                rtol=0.0,
                atol=max(abs(existing_value) * 1e-6, 1e-9),
            )
            for existing_value in resolved_values
        ):
            continue

        resolved_values.append(value)

    return resolved_values


def _is_rosetta_script_process_name(
    process_name: Any,
) -> bool:
    """
    Return whether a process name refers to one of the Rosetta scripts.
    """
    normalized_name = str(process_name or "").strip().lower()

    return normalized_name in {
        "rosetta script",
        "rosetta script v1",
    }


class PeakWorkflowGraphBuilder:
    """
    Build the graph figure for the selected peak workflow process.

    This class owns peak workflow orchestration:

    - process dispatch
    - detector channel resolution
    - process setting resolution
    - custom process figure dispatch
    - histogram fallback
    - 2D scatter fallback
    - peak markers
    - gate overlays
    - runtime visualization settings

    Generic 2D scatter formatting is delegated to
    ``RosettaX.workflow.plotting.scatter2d.Scatter2DGraph``.
    """

    default_margin: dict[str, int] = {
        "l": 80,
        "r": 30,
        "t": 55,
        "b": 70,
    }

    rejected_x_fill_color = "rgba(20, 20, 20, 0.16)"
    rejected_y_fill_color = "rgba(20, 20, 20, 0.22)"
    accepted_y_fill_color = "rgba(38, 196, 78, 0.20)"
    fluorescence_helper_fill_color = "rgba(64, 138, 255, 0.12)"

    def __init__(
        self,
        *,
        backend: Any,
        uploaded_fcs_path: Any,
        process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
        process_setting_ids: list[dict[str, Any]],
        process_setting_values: list[Any],
        graph_toggle_value: Any,
        advanced_mode_value: Any = None,
        data_filter_value: Any = None,
        xscale_selection: Any = None,
        yscale_selection: Any = None,
        nbins: Any = None,
        peak_lines_payload: Any = None,
        max_events_for_plots: Any = None,
        runtime_config_data: Any = None,
    ) -> None:
        self.backend = backend
        self.uploaded_fcs_path = uploaded_fcs_path
        self.process_name = process_name
        self.detector_dropdown_ids = detector_dropdown_ids or []
        self.detector_dropdown_values = detector_dropdown_values or []
        self.process_setting_ids = process_setting_ids or []
        self.process_setting_values = process_setting_values or []
        self.graph_toggle_value = graph_toggle_value
        self.advanced_mode_value = advanced_mode_value
        self.data_filter_value = data_filter_value
        self.xscale_selection = xscale_selection
        self.yscale_selection = yscale_selection
        self.nbins = nbins
        self.peak_lines_payload = peak_lines_payload
        self.max_events_for_plots = max_events_for_plots
        self.runtime_config_data = runtime_config_data

        self.runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )

        self.resolved_process_name = registry.resolve_process_name(
            process_name,
        )

        self.process = registry.get_process_instance(
            process_name=self.resolved_process_name,
        )

        self.detector_channels: dict[str, Any] = {}
        self.process_settings: dict[str, Any] = {}
        self._stable_histogram_count_values: Optional[np.ndarray] = None

    def build(self) -> go.Figure:
        """
        Build the complete Plotly figure.
        """
        validation_figure = self._validate_context()

        if validation_figure is not None:
            return validation_figure

        self.detector_channels = self._resolve_detector_channels()

        missing_channel_names = self._get_missing_detector_channel_names()

        if missing_channel_names:
            return plottings._make_info_figure(
                self._build_missing_detector_message(
                    missing_channel_names=missing_channel_names,
                )
            )

        self.process_settings = self._build_process_settings()

        figure = self._build_process_specific_figure()

        self._apply_axis_types(
            figure=figure,
        )

        self._apply_stable_1d_histogram_y_range(
            figure=figure,
        )

        self._apply_runtime_visualization_settings(
            figure=figure,
        )

        figure.update_layout(
            margin=self.default_margin,
        )

        return figure

    def _validate_context(self) -> Optional[go.Figure]:
        """
        Validate the graph context.

        Returns an information figure when the context is not usable.
        """
        if not is_enabled(
            self.graph_toggle_value,
        ):
            return plottings._make_info_figure(
                "Graph disabled.",
            )

        if not str(self.uploaded_fcs_path or "").strip():
            return plottings._make_info_figure(
                "Upload an FCS file first.",
            )

        if self.backend is None:
            return plottings._make_info_figure(
                "No backend available for this file.",
            )

        if self.process is None:
            return plottings._make_info_figure(
                "Select a valid peak process.",
            )

        return None

    def _resolve_detector_channels(self) -> dict[str, Any]:
        """
        Resolve detector channel selections for the selected process.
        """
        return detectors.resolve_detector_channels_for_process(
            detector_dropdown_ids=self.detector_dropdown_ids,
            detector_dropdown_values=self.detector_dropdown_values,
            process_name=self.resolved_process_name,
        )

    def _get_missing_detector_channel_names(self) -> list[str]:
        """
        Return required detector channels that do not have selected columns.
        """
        missing_channel_names: list[str] = []

        for channel_name in self._get_required_detector_channels():
            if not str(self.detector_channels.get(channel_name) or "").strip():
                missing_channel_names.append(
                    str(
                        channel_name,
                    )
                )

        return missing_channel_names

    def _build_missing_detector_message(
        self,
        *,
        missing_channel_names: list[str],
    ) -> str:
        """
        Build a user visible missing detector message.
        """
        if len(missing_channel_names) == 1:
            return f"Select the {missing_channel_names[0]} detector channel first."

        return "Select the required detector channels first."

    def _build_process_settings(self) -> dict[str, Any]:
        """
        Build a dictionary of process setting values for the selected process.
        """
        process_settings = build_process_settings(
            process_setting_ids=self.process_setting_ids,
            process_setting_values=self.process_setting_values,
            process_name=self.resolved_process_name,
        )

        process_settings["filter_edge_artifacts"] = self.data_filter_value

        return process_settings

    def _edge_artifact_filter_is_enabled(self) -> bool:
        """
        Return whether shared zero/saturation filtering is enabled.
        """
        return resolve_edge_artifact_filter_enabled(
            process_settings=self.process_settings,
            default=True,
        )

    def _build_process_specific_figure(self) -> go.Figure:
        """
        Build the selected process figure.
        """
        custom_figure = self._try_build_custom_process_figure()

        if custom_figure is not None:
            return custom_figure

        graph_type = getattr(
            self.process,
            "graph_type",
            None,
        )

        if graph_type == "1d_histogram":
            return self._build_default_1d_histogram_figure()

        if graph_type == "2d_scatter":
            return self._build_default_2d_scatter_figure()

        return plottings._make_info_figure(
            "No graph implementation is available for this peak process.",
        )

    def _try_build_custom_process_figure(self) -> Optional[go.Figure]:
        """
        Let a process provide its own figure implementation when available.
        """
        for method_name in (
            "build_graph_figure",
            "build_figure",
            "build_plot",
        ):
            method = getattr(
                self.process,
                method_name,
                None,
            )

            if not callable(method):
                continue

            figure = self._call_with_supported_arguments(
                method,
                backend=self.backend,
                uploaded_fcs_path=self.uploaded_fcs_path,
                process_name=self.resolved_process_name,
                detector_channels=self.detector_channels,
                process_settings=self.process_settings,
                peak_lines_payload=self.peak_lines_payload,
                n_bins_for_plots=self._resolve_number_of_bins(),
                nbins=self._resolve_number_of_bins(),
                max_events_for_plots=self._resolve_max_events_for_plots(),
                max_events_for_analysis=self._resolve_max_events_for_plots(),
                xscale_selection=self.xscale_selection,
                yscale_selection=self.yscale_selection,
                runtime_config_data=self.runtime_config_data,
            )

            if getattr(self.process, "graph_type", None) == "2d_scatter":
                Scatter2DGraph.apply_formatting(
                    figure=figure,
                    title=str(
                        getattr(
                            self.process,
                            "process_label",
                            "2D scatter",
                        )
                    ),
                    x_axis_title=str(
                        figure.layout.xaxis.title.text or "x",
                    ),
                    y_axis_title=str(
                        figure.layout.yaxis.title.text or "y",
                    ),
                    x_axis_type="log" if self._x_axis_is_log() else "linear",
                    y_axis_type="log" if self._y_axis_is_log() else "linear",
                    show_grid=self._show_grid_by_default(),
                    hovermode="closest",
                    uirevision=f"peak_workflow_{self.resolved_process_name}_2d_scatter",
                )

                figure = self._add_2d_overlays(
                    figure=figure,
                )

                if self._advanced_mode_is_enabled():
                    figure = self._add_2d_advanced_overlays(
                        figure=figure,
                    )

            return figure

        return None

    def _build_default_1d_histogram_figure(self) -> go.Figure:
        """
        Build a fallback one dimensional histogram figure.
        """
        detector_column = self._get_first_required_detector_column()

        if not detector_column:
            return plottings._make_info_figure(
                "Select a detector channel first.",
            )

        if self._edge_artifact_filter_is_enabled():
            raw_values = np.asarray(
                column_copy(
                    fcs_file_path=self.backend.fcs_file_path,
                    detector_column=str(detector_column),
                    dtype=float,
                    n=self._resolve_max_events_for_plots(),
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

            histogram_values = filtered_values[
                filtered_values > 0.0
            ] if self._x_axis_is_log() else filtered_values

            if histogram_values.size == 0:
                return plottings._make_info_figure(
                    "No positive events remain after filtering for the selected axis scale.",
                )

            if self._x_axis_is_log():
                lower_edge = float(np.min(histogram_values))
                upper_edge = float(np.max(histogram_values))

                if lower_edge == upper_edge:
                    upper_edge = lower_edge * 1.01

                histogram_edges = np.geomspace(
                    lower_edge,
                    upper_edge,
                    num=self._resolve_number_of_bins() + 1,
                )
                histogram_counts, histogram_edges = np.histogram(
                    histogram_values,
                    bins=histogram_edges,
                )
                histogram_centers = np.sqrt(
                    histogram_edges[:-1] * histogram_edges[1:]
                )
            else:
                histogram_counts, histogram_edges = np.histogram(
                    histogram_values,
                    bins=self._resolve_number_of_bins(),
                )
                histogram_centers = 0.5 * (
                    histogram_edges[:-1] + histogram_edges[1:]
                )

            histogram_result = plottings.HistogramResult(
                values=np.asarray(histogram_values, dtype=float),
                counts=np.asarray(histogram_counts, dtype=float),
                edges=np.asarray(histogram_edges, dtype=float),
                centers=np.asarray(histogram_centers, dtype=float),
            )
        else:
            histogram_result = plottings.build_histogram(
                fcs_file_path=self.backend.fcs_file_path,
                detector_column=detector_column,
                n_bins_for_plots=self._resolve_number_of_bins(),
                max_events_for_analysis=self._resolve_max_events_for_plots(),
                use_log_x_bins=self._x_axis_is_log(),
            )
        self._stable_histogram_count_values = np.asarray(
            histogram_result.counts,
            dtype=float,
        )

        peak_positions = self._extract_x_positions_from_peak_lines_payload()

        figure = plottings.build_histogram_figure(
            histogram_result=histogram_result,
            detector_column=detector_column,
            use_log_counts=axis_scale_selection_is_log(
                scale_selection=self.yscale_selection,
                axis="y",
            ),
            peak_positions=peak_positions,
        )

        if self._advanced_mode_is_enabled():
            figure = self._add_1d_advanced_overlays(
                figure=figure,
            )

        figure.update_layout(
            showlegend=False,
        )

        return figure

    def _apply_stable_1d_histogram_y_range(
        self,
        *,
        figure: go.Figure,
    ) -> None:
        """
        Clamp 1D histogram y range using only histogram counts.

        Diagnostic overlays such as smoothed curves and threshold guide lines
        must not redefine the displayed histogram count range.
        """
        histogram_count_values = self._stable_histogram_count_values

        if histogram_count_values is None:
            return

        y_range = compute_stable_axis_range(
            values=histogram_count_values,
            log_scale=self._y_axis_is_log(),
        )

        if y_range is None:
            return

        figure.update_yaxes(
            autorange=False,
            range=y_range,
        )

    def _advanced_mode_is_enabled(self) -> bool:
        """
        Return whether advanced mode is enabled for graph diagnostics.
        """
        return is_enabled(
            self.advanced_mode_value,
        )

    def _add_1d_advanced_overlays(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add compact diagnostic overlays for 1D automatic peak detection.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return figure

        debug_payload = self.peak_lines_payload.get("debug", {})

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
                hovertemplate=(
                    "x=%{x:.6g}<br>smoothed=%{y:.6g}<extra></extra>"
                ),
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

    def _build_default_2d_scatter_figure(self) -> go.Figure:
        """
        Build a fallback two dimensional scatter figure.

        Event density is shown through marker color. The density is estimated with a
        two dimensional histogram, and for log axes the density is computed in log10
        space so that the color mapping follows the displayed geometry.
        """
        required_channel_names = self._get_required_detector_channels()

        if len(required_channel_names) < 2:
            return plottings._make_info_figure(
                "This process does not define two required detector channels.",
            )

        x_detector_column = self.detector_channels.get(
            required_channel_names[0],
        )

        y_detector_column = self.detector_channels.get(
            required_channel_names[1],
        )

        if not x_detector_column or not y_detector_column:
            return plottings._make_info_figure(
                "Select both detector channels first.",
            )

        payload_plot_values = self._extract_plot_values_from_peak_lines_payload()

        if payload_plot_values is not None:
            x_values, y_values = payload_plot_values
        else:
            x_values = np.asarray(
                column_copy(
                    fcs_file_path=self.backend.fcs_file_path,
                    detector_column=str(
                        x_detector_column,
                    ),
                    dtype=float,
                    n=self._resolve_max_events_for_plots(),
                ),
                dtype=float,
            )

            y_values = np.asarray(
                column_copy(
                    fcs_file_path=self.backend.fcs_file_path,
                    detector_column=str(
                        y_detector_column,
                    ),
                    dtype=float,
                    n=self._resolve_max_events_for_plots(),
                ),
                dtype=float,
            )

        if self._edge_artifact_filter_is_enabled():
            x_values, y_values = filter_edge_artifact_pairs(
                x_values=x_values,
                y_values=y_values,
                remove_x_min=True,
                remove_x_max=True,
                remove_y_min=True,
                remove_y_max=False,
            )

        filtered_x_values, filtered_y_values = self._filter_2d_values_for_axis_scale(
            x_values=x_values,
            y_values=y_values,
        )

        if filtered_x_values.size == 0 or filtered_y_values.size == 0:
            return plottings._make_info_figure(
                "No finite events are available for the selected axis scale.",
            )

        density_values = self._compute_2d_density_values(
            x_values=filtered_x_values,
            y_values=filtered_y_values,
            x_log_scale=self._x_axis_is_log(),
            y_log_scale=self._y_axis_is_log(),
            colormap_log_scale=self._colormap_is_log(),
            number_of_bins=self._resolve_density_colormap_number_of_bins(),
        )

        figure = go.Figure()

        figure.add_trace(
            go.Scattergl(
                x=filtered_x_values,
                y=filtered_y_values,
                mode="markers",
                name="Events",
                marker={
                    "size": self._get_default_marker_size(),
                    "opacity": self._get_default_marker_opacity(),
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
                    self.process,
                    "process_label",
                    "2D peak workflow scatter",
                )
            ),
            x_axis_title=f"{x_detector_column} [a.u.]",
            y_axis_title=f"{y_detector_column} [a.u.]",
            x_axis_type="log" if self._x_axis_is_log() else "linear",
            y_axis_type="log" if self._y_axis_is_log() else "linear",
            show_grid=self._show_grid_by_default(),
            hovermode="closest",
            uirevision=f"peak_workflow_{self.resolved_process_name}_2d_scatter",
        )

        figure = apply_stable_2d_axis_ranges(
            figure=figure,
            x_values=filtered_x_values,
            y_values=filtered_y_values,
            x_log_scale=self._x_axis_is_log(),
            y_log_scale=self._y_axis_is_log(),
        )

        figure = self._add_2d_overlays(
            figure=figure,
        )

        if self._advanced_mode_is_enabled():
            figure = self._add_2d_advanced_overlays(
                figure=figure,
            )

        figure.update_layout(
            showlegend=False,
        )

        return figure

    def _extract_plot_values_from_peak_lines_payload(
        self,
    ) -> Optional[tuple[np.ndarray, np.ndarray]]:
        """
        Extract plot event coordinates from the peak payload when provided.

        This lets a process override the displayed point cloud so the graph can
        reflect process-specific filtering such as Rosetta saturated-event removal.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return None

        raw_x_values = self.peak_lines_payload.get("plot_x_values")
        raw_y_values = self.peak_lines_payload.get("plot_y_values")

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



    def _compute_2d_density_values(
        self,
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

        finite_mask = (
            np.isfinite(
                density_x_values,
            )
            & np.isfinite(
                density_y_values,
            )
        )

        if not np.all(finite_mask):
            density_values = np.zeros(
                x_array.shape,
                dtype=float,
            )

            valid_density_values = self._compute_2d_density_values(
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

        x_bin_indices = np.searchsorted(
            x_edges,
            density_x_values,
            side="right",
        ) - 1

        y_bin_indices = np.searchsorted(
            y_edges,
            density_y_values,
            side="right",
        ) - 1

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


    def _resolve_density_colormap_number_of_bins(self) -> int:
        """
        Resolve the number of bins used for 2D density color mapping.
        """
        default_number_of_bins = self._resolve_number_of_bins()

        return casting.as_int(
            self._get_nested_config_value(
                path="visualization.density_colormap_n_bins",
                default=default_number_of_bins,
            ),
            default=default_number_of_bins,
            min_value=10,
            max_value=1000,
        )









    def _filter_2d_values_for_axis_scale(
        self,
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

        if self._x_axis_is_log():
            finite_mask = finite_mask & (
                x_array > 0.0
            )

        if self._y_axis_is_log():
            finite_mask = finite_mask & (
                y_array > 0.0
            )

        return (
            x_array[
                finite_mask
            ],
            y_array[
                finite_mask
            ],
        )

    def _build_scatter2d_axis_scale_toggle_values(self) -> list[str]:
        """
        Convert peak workflow x/y scale selections into Scatter2DGraph values.
        """
        axis_scale_toggle_values: list[str] = []

        if self._x_axis_is_log():
            axis_scale_toggle_values.append(
                Scatter2DGraph.x_log_value,
            )

        if self._y_axis_is_log():
            axis_scale_toggle_values.append(
                Scatter2DGraph.y_log_value,
            )

        return axis_scale_toggle_values

    def _colormap_is_log(self) -> bool:
        """
        Return whether the 2D density colormap should use logarithmic scaling.
        """
        if isinstance(self.xscale_selection, (list, tuple, set)):
            return Scatter2DGraph.colormap_log_value in self.xscale_selection

        return False

    def _add_2d_overlays(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add gate overlays and selected peak markers.
        """
        figure = self._add_x_axis_gate_overlay(
            figure=figure,
        )

        figure = self._add_y_axis_gate_overlay(
            figure=figure,
        )

        figure = self._add_selected_peak_markers(
            figure=figure,
        )

        return figure

    def _add_x_axis_gate_overlay(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add x axis lower and upper gate lines and shade rejected x regions.

        Accepted region
        ---------------
        x_lower_gate <= x <= x_upper_gate
        """
        x_lower_gate = self._extract_x_axis_lower_gate_from_peak_lines_payload()
        x_upper_gate = self._extract_x_axis_upper_gate_from_peak_lines_payload()

        if x_lower_gate is None and x_upper_gate is None:
            return figure

        self._add_out_of_x_interval_gate_shading(
            figure=figure,
            lower_gate=x_lower_gate,
            upper_gate=x_upper_gate,
        )

        if x_lower_gate is not None:
            self._add_vertical_shape_line(
                figure=figure,
                x=x_lower_gate,
                line_width=2,
                line_dash="dash",
            )

        if x_upper_gate is not None:
            self._add_vertical_shape_line(
                figure=figure,
                x=x_upper_gate,
                line_width=2,
                line_dash="dash",
            )

        return figure

    def _add_y_axis_gate_overlay(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add y axis lower and upper gate lines and shade rejected y regions.

        Accepted region
        ---------------
        y_lower_gate <= y <= y_upper_gate
        """
        y_lower_gate = self._extract_y_axis_lower_gate_from_peak_lines_payload()
        y_upper_gate = self._extract_y_axis_upper_gate_from_peak_lines_payload()

        if y_lower_gate is None and y_upper_gate is None:
            return figure

        self._add_out_of_y_interval_gate_shading(
            figure=figure,
            lower_gate=y_lower_gate,
            upper_gate=y_upper_gate,
        )

        if y_lower_gate is not None:
            self._add_horizontal_shape_line(
                figure=figure,
                y=y_lower_gate,
                line_width=2,
                line_dash="dash",
            )

        if y_upper_gate is not None:
            self._add_horizontal_shape_line(
                figure=figure,
                y=y_upper_gate,
                line_width=2,
                line_dash="dash",
            )

        if self._is_rosetta_script_process():
            self._add_rosetta_y_gate_helper(
                figure=figure,
                y_lower_gate=y_lower_gate,
                y_upper_gate=y_upper_gate,
            )

        return figure

    def _add_selected_peak_markers(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add selected peak markers without visible text labels.

        Labels are shown in hover only. This prevents long labels from shrinking
        the plot area.
        """
        points = self._extract_points_from_peak_lines_payload()

        if not points:
            return figure

        labels = self._extract_labels_from_peak_lines_payload(
            point_count=len(points),
        )

        if self._is_rosetta_script_process():
            scatter_guide_positions = self._extract_numeric_list_from_peak_lines_payload(
                key="scatter_guide_positions",
            )
            fluorescence_guide_positions = self._extract_numeric_list_from_peak_lines_payload(
                key="fluorescence_guide_positions",
            )

            if not scatter_guide_positions:
                scatter_guide_positions = unique_finite_preserving_order(
                    [
                        point["x"]
                        for point in points
                    ]
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
                self._add_vertical_shape_line(
                    figure=figure,
                    x=scatter_position,
                    line_width=2,
                    line_dash="dash",
                    line_color="#1f9d55",
                )

            if self._advanced_mode_is_enabled():
                for fluorescence_position in fluorescence_guide_positions:
                    self._add_horizontal_shape_line(
                        figure=figure,
                        y=fluorescence_position,
                        line_width=2,
                        line_dash="dash",
                        line_color="#d64545",
                    )

        else:
            for point in points:
                self._add_vertical_shape_line(
                    figure=figure,
                    x=point["x"],
                    line_width=1,
                    line_dash="dot",
                    line_color=None,
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

    def _add_2d_advanced_overlays(
        self,
        *,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Add the smoothed 2D density map used by automatic peak detection.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return figure

        debug_payload = self.peak_lines_payload.get("debug", {})

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

        if (
            x_centers.size == 0
            or y_centers.size == 0
            or smoothed_histogram.size == 0
        ):
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

        figure.data = tuple(
            [
                figure.data[-1],
                *figure.data[:-1],
            ]
        )

        return figure

    def _add_out_of_x_interval_gate_shading(
        self,
        *,
        figure: go.Figure,
        lower_gate: Optional[float],
        upper_gate: Optional[float],
    ) -> None:
        """
        Shade x regions outside the accepted interval.
        """
        visible_x_range = self._get_visible_axis_range(
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
                    fillcolor=self.rejected_x_fill_color,
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
                    fillcolor=self.rejected_x_fill_color,
                    line={
                        "width": 0,
                    },
                    layer="below",
                )

    def _add_out_of_y_interval_gate_shading(
        self,
        *,
        figure: go.Figure,
        lower_gate: Optional[float],
        upper_gate: Optional[float],
    ) -> None:
        """
        Shade y regions outside the accepted interval.
        """
        visible_y_range = self._get_visible_axis_range(
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
                    fillcolor=self.rejected_y_fill_color,
                    line={
                        "width": 0,
                    },
                    layer="below",
                )

    def _add_rosetta_y_gate_helper(
        self,
        *,
        figure: go.Figure,
        y_lower_gate: Optional[float],
        y_upper_gate: Optional[float],
    ) -> None:
        """
        Add explicit Rosetta helper bands for the accepted scatter gate and the
        fluorescence region above it.
        """
        visible_y_range = self._get_visible_axis_range(
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
                fillcolor=self.accepted_y_fill_color,
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
                    fillcolor=self.fluorescence_helper_fill_color,
                    line={"width": 0},
                    layer="below",
                )

    def _add_vertical_shape_line(
        self,
        *,
        figure: go.Figure,
        x: float,
        line_width: float,
        line_dash: str,
        line_color: Optional[str] = None,
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

    def _add_horizontal_shape_line(
        self,
        *,
        figure: go.Figure,
        y: float,
        line_width: float,
        line_dash: str,
        line_color: Optional[str] = None,
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

    def _get_visible_axis_range(
        self,
        *,
        figure: go.Figure,
        axis_name: str,
    ) -> Optional[tuple[float, float]]:
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
            lower_value = 10.0 ** lower_value
            upper_value = 10.0 ** upper_value

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

    def _extract_x_axis_lower_gate_from_peak_lines_payload(self) -> Optional[float]:
        """
        Extract the x axis lower gate threshold from the peak line payload.
        """
        return self._extract_first_finite_float_from_peak_payload(
            keys=(
                "x_axis_lower_gate",
                "x_lower_gate",
                "x_lower_gate_threshold",
                "x_axis_gate",
                "x_gate",
                "x_gate_threshold",
                "scatter_gate",
                "scatter_limit_of_detection",
                "limit_of_detection_x",
                "lod_x",
                "x_lod",
            )
        )

    def _extract_x_axis_upper_gate_from_peak_lines_payload(self) -> Optional[float]:
        """
        Extract the x axis upper gate threshold from the peak line payload.
        """
        return self._extract_first_finite_float_from_peak_payload(
            keys=(
                "x_axis_upper_gate",
                "x_upper_gate",
                "x_upper_gate_threshold",
            )
        )

    def _extract_y_axis_lower_gate_from_peak_lines_payload(self) -> Optional[float]:
        """
        Extract the y axis lower gate threshold from the peak line payload.
        """
        return self._extract_first_finite_float_from_peak_payload(
            keys=(
                "y_axis_lower_gate",
                "y_lower_gate",
                "y_lower_gate_threshold",
                "y_axis_gate",
                "y_gate",
                "y_gate_threshold",
                "green_fluorescence_gate",
                "fluorescence_gate",
                "fluorescence_threshold_y",
            )
        )

    def _extract_y_axis_upper_gate_from_peak_lines_payload(self) -> Optional[float]:
        """
        Extract the y axis upper gate threshold from the peak line payload.
        """
        return self._extract_first_finite_float_from_peak_payload(
            keys=(
                "y_axis_upper_gate",
                "y_upper_gate",
                "y_upper_gate_threshold",
            )
        )

    def _extract_first_finite_float_from_peak_payload(
        self,
        *,
        keys: tuple[str, ...],
    ) -> Optional[float]:
        """
        Extract the first finite float value matching one of the provided keys.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return None

        for key in keys:
            value = self.peak_lines_payload.get(
                key,
            )

            if value is None:
                continue

            try:
                value_float = float(
                    value,
                )

            except (TypeError, ValueError):
                continue

            if np.isfinite(value_float):
                return value_float

        return None

    def _extract_x_positions_from_peak_lines_payload(self) -> list[float]:
        """
        Extract x positions from a peak line payload.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return []

        candidate_values = (
            self.peak_lines_payload.get(
                "x_positions",
            )
            or self.peak_lines_payload.get(
                "positions",
            )
            or []
        )

        if not candidate_values and isinstance(
            self.peak_lines_payload.get(
                "points",
            ),
            list,
        ):
            candidate_values = [
                point.get(
                    "x",
                )
                for point in self.peak_lines_payload["points"]
                if isinstance(point, dict)
            ]

        x_positions: list[float] = []

        for value in candidate_values:
            try:
                value_float = float(
                    value,
                )

            except (TypeError, ValueError):
                continue

            if np.isfinite(value_float):
                x_positions.append(
                    value_float,
                )

        return x_positions

    def _extract_points_from_peak_lines_payload(self) -> list[dict[str, float]]:
        """
        Extract two dimensional points from a peak line payload.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return []

        points = self.peak_lines_payload.get(
            "points",
        )

        if isinstance(points, list):
            resolved_points: list[dict[str, float]] = []

            for point in points:
                if not isinstance(point, dict):
                    continue

                try:
                    x_value = float(
                        point["x"],
                    )

                    y_value = float(
                        point["y"],
                    )

                except (KeyError, TypeError, ValueError):
                    continue

                if not np.isfinite(x_value) or not np.isfinite(y_value):
                    continue

                resolved_points.append(
                    {
                        "x": x_value,
                        "y": y_value,
                    }
                )

            return resolved_points

        x_positions = self.peak_lines_payload.get(
            "x_positions",
        ) or []

        y_positions = self.peak_lines_payload.get(
            "y_positions",
        ) or []

        resolved_points: list[dict[str, float]] = []

        for x_value, y_value in zip(
            x_positions,
            y_positions,
            strict=False,
        ):
            try:
                x_float = float(
                    x_value,
                )

                y_float = float(
                    y_value,
                )

            except (TypeError, ValueError):
                continue

            if not np.isfinite(x_float) or not np.isfinite(y_float):
                continue

            resolved_points.append(
                {
                    "x": x_float,
                    "y": y_float,
                }
            )

        return resolved_points

    def _extract_labels_from_peak_lines_payload(
        self,
        *,
        point_count: int,
    ) -> list[str]:
        """
        Extract peak labels from a peak line payload.
        """
        if isinstance(self.peak_lines_payload, dict):
            labels = self.peak_lines_payload.get(
                "labels",
            )

            if isinstance(labels, list):
                resolved_labels = [
                    str(
                        label,
                    )
                    for label in labels[:point_count]
                ]

                while len(resolved_labels) < point_count:
                    resolved_labels.append(
                        f"Peak {len(resolved_labels) + 1}",
                    )

                return resolved_labels

        return [
            f"Peak {index + 1}"
            for index in range(
                point_count,
            )
        ]

    def _extract_numeric_list_from_peak_lines_payload(
        self,
        *,
        key: str,
    ) -> list[float]:
        """
        Extract one finite unique float list from the peak payload.
        """
        if not isinstance(self.peak_lines_payload, dict):
            return []

        raw_values = self.peak_lines_payload.get(
            key,
        )

        if not isinstance(raw_values, list):
            return []

        return unique_finite_preserving_order(
            raw_values,
        )

    def _is_rosetta_script_process(self) -> bool:
        """
        Return whether the currently selected process is the Rosetta Script.
        """
        return _is_rosetta_script_process_name(
            self.resolved_process_name,
        )

    def _apply_axis_types(
        self,
        *,
        figure: go.Figure,
    ) -> None:
        """
        Apply selected axis scale types.
        """
        figure.update_xaxes(
            type="log" if self._x_axis_is_log() else "linear",
        )

        figure.update_yaxes(
            type="log" if self._y_axis_is_log() else "linear",
        )

    def _apply_runtime_visualization_settings(
        self,
        *,
        figure: go.Figure,
    ) -> None:
        """
        Apply profile visualization settings to a peak workflow figure.
        """
        default_marker_size = self._get_default_marker_size()
        default_marker_opacity = self._get_default_marker_opacity()

        default_line_width = self._get_nested_config_float(
            path="visualization.default_line_width",
            default=3.0,
        )

        default_font_size = self._get_nested_config_float(
            path="visualization.default_font_size",
            default=34.0,
        )

        default_tick_size = self._get_nested_config_float(
            path="visualization.default_tick_size",
            default=18.0,
        )

        show_grid_by_default = self._show_grid_by_default()

        plottings.apply_default_visual_style(
            figure,
            marker_size=default_marker_size,
            line_width=default_line_width,
            font_size=default_font_size,
            tick_size=default_tick_size,
            show_grid=show_grid_by_default,
        )

        for trace in figure.data:
            self._apply_trace_visualization_settings(
                trace=trace,
                default_marker_size=default_marker_size,
                default_marker_opacity=default_marker_opacity,
                default_line_width=default_line_width,
            )

        for shape in figure.layout.shapes or []:
            if hasattr(shape, "line"):
                shape.line.width = default_line_width

    def _apply_trace_visualization_settings(
        self,
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

        if trace_type == "bar":
            if hasattr(trace, "marker"):
                trace.marker.line.width = default_line_width

        if trace_type == "histogram":
            if hasattr(trace, "marker"):
                trace.marker.line.width = default_line_width

    def _resolve_number_of_bins(self) -> int:
        """
        Resolve the number of bins used for 1D histogram figures.
        """
        return casting.as_int(
            self.nbins,
            default=self.runtime_config.get_int(
                "calibration.n_bins_for_plots",
                default=100,
            ),
            min_value=1,
            max_value=10_000,
        )

    def _resolve_max_events_for_plots(self) -> int:
        """
        Resolve the maximum number of events shown in graphs.
        """
        return casting.as_int(
            self.max_events_for_plots,
            default=self.runtime_config.get_int(
                "calibration.max_events_for_analysis",
                default=10000,
            ),
            min_value=1,
            max_value=5_000_000,
        )

    def _get_required_detector_channels(self) -> list[str]:
        """
        Return required detector channel names for the selected process.
        """
        if hasattr(self.process, "get_required_detector_channels"):
            channel_names = self.process.get_required_detector_channels()

            if channel_names is None:
                return []

            return [
                str(
                    channel_name,
                )
                for channel_name in channel_names
            ]

        channel_names = getattr(
            self.process,
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

    def _get_first_required_detector_column(self) -> Any:
        """
        Return the detector column for the first required channel.
        """
        for channel_name in self._get_required_detector_channels():
            detector_column = self.detector_channels.get(
                channel_name,
            )

            if str(detector_column or "").strip():
                return detector_column

        return None

    def _x_axis_is_log(self) -> bool:
        """
        Return whether x axis log scale is enabled.
        """
        xscale_selection = getattr(
            self,
            "xscale_selection",
            None,
        )

        return scale_selection_is_log(
            xscale_selection,
        ) or axis_scale_selection_is_log(
            scale_selection=xscale_selection,
            axis="x",
        )

    def _y_axis_is_log(self) -> bool:
        """
        Return whether y axis log scale is enabled.
        """
        yscale_selection = getattr(
            self,
            "yscale_selection",
            None,
        )

        return scale_selection_is_log(
            yscale_selection,
        ) or axis_scale_selection_is_log(
            scale_selection=yscale_selection,
            axis="y",
        )

    def _get_default_marker_size(self) -> float:
        """
        Return default marker size from runtime config.
        """
        return self._get_nested_config_float(
            path="visualization.default_marker_size",
            default=10.0,
        )

    def _get_default_marker_opacity(self) -> float:
        """
        Return default marker opacity from runtime config.
        """
        return self._get_nested_config_float(
            path="visualization.default_marker_opacity",
            default=0.72,
        )

    def _show_grid_by_default(self) -> bool:
        """
        Return whether grid lines should be shown by default.
        """
        return self._get_nested_config_bool(
            path="visualization.show_grid_by_default",
            default=False,
        )

    def _get_nested_config_float(
        self,
        *,
        path: str,
        default: float,
    ) -> float:
        """
        Return a float from a nested runtime config dictionary.
        """
        value = self._get_nested_config_value(
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

    def _get_nested_config_bool(
        self,
        *,
        path: str,
        default: bool,
    ) -> bool:
        """
        Return a bool from a nested runtime config dictionary.
        """
        value = self._get_nested_config_value(
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

    def _get_nested_config_value(
        self,
        *,
        path: str,
        default: Any,
    ) -> Any:
        """
        Return a value from a nested dictionary using a dot separated path.
        """
        if not isinstance(self.runtime_config_data, dict):
            return default

        current_value: Any = self.runtime_config_data

        for key in path.split("."):
            if not isinstance(current_value, dict):
                return default

            if key not in current_value:
                return default

            current_value = current_value[key]

        return current_value

    def _call_with_supported_arguments(
        self,
        callable_object: Any,
        **candidate_arguments: Any,
    ) -> Any:
        """
        Call a function with only the keyword arguments it accepts.
        """
        signature = inspect.signature(
            callable_object,
        )

        accepts_arbitrary_keywords = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )

        if accepts_arbitrary_keywords:
            return callable_object(
                **candidate_arguments,
            )

        accepted_arguments = {
            argument_name: argument_value
            for argument_name, argument_value in candidate_arguments.items()
            if argument_name in signature.parameters
        }

        return callable_object(
            **accepted_arguments,
        )


def build_process_settings(
    *,
    process_setting_ids: list[dict[str, Any]],
    process_setting_values: list[Any],
    process_name: str,
) -> dict[str, Any]:
    """
    Build a dictionary of process setting values for the selected process.

    Kept as a module level helper for compatibility with older imports.
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

        setting_name = process_setting_id.get(
            "setting",
        )

        if not isinstance(setting_name, str):
            continue

        process_settings[setting_name] = process_setting_value

    return process_settings
