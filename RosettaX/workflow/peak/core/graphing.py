# -*- coding: utf-8 -*-

from typing import Any, Optional
import inspect
import logging

import numpy as np
import plotly.graph_objs as go

from . import detectors
from .. import registry
from RosettaX.utils import casting, plottings
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from RosettaX.workflow.plotting.scatter2d import Scatter2DTrace


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
    Return whether a checklist style scale selection requests log scale.

    Compatibility wrapper for older peak workflow code.
    """
    if isinstance(scale_selection, str):
        return scale_selection == "log"

    if isinstance(scale_selection, (list, tuple, set)):
        return "log" in scale_selection

    if isinstance(scale_selection, (list, tuple, set)):
        return Scatter2DGraph.x_log_value in scale_selection or Scatter2DGraph.y_log_value in scale_selection

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
        xscale_selection=xscale_selection,
        yscale_selection=yscale_selection,
        nbins=nbins,
        peak_lines_payload=peak_lines_payload,
        max_events_for_plots=max_events_for_plots,
        runtime_config_data=runtime_config_data,
    ).build()


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
        return build_process_settings(
            process_setting_ids=self.process_setting_ids,
            process_setting_values=self.process_setting_values,
            process_name=self.resolved_process_name,
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

        histogram_result = plottings.build_histogram(
            fcs_file_path=self.backend.fcs_file_path,
            detector_column=detector_column,
            n_bins_for_plots=self._resolve_number_of_bins(),
            max_events_for_analysis=self._resolve_max_events_for_plots(),
        )

        peak_positions = self._extract_x_positions_from_peak_lines_payload()

        return plottings.build_histogram_figure(
            histogram_result=histogram_result,
            detector_column=detector_column,
            use_log_counts=scale_selection_is_log(
                self.yscale_selection,
            ),
            peak_positions=peak_positions,
        )

    def _build_default_2d_scatter_figure(self) -> go.Figure:
        """
        Build a fallback two dimensional scatter figure.

        Generic formatting is delegated to ``Scatter2DGraph``. Peak specific
        overlays and gate shading are added after the data axis range is fixed,
        so overlays do not rescale the graph.
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

        axis_scale_toggle_values = self._build_scatter2d_axis_scale_toggle_values()

        figure = Scatter2DGraph.build_figure(
            traces=[
                Scatter2DTrace(
                    x_values=x_values,
                    y_values=y_values,
                    name="Events",
                    marker_size=self._get_default_marker_size(),
                    marker_opacity=0.5,
                )
            ],
            title=str(
                getattr(
                    self.process,
                    "process_label",
                    "2D peak workflow scatter",
                )
            ),
            x_axis_title=f"{x_detector_column} [a.u.]",
            y_axis_title=f"{y_detector_column} [a.u.]",
            axis_scale_toggle_values=axis_scale_toggle_values,
            show_grid=self._show_grid_by_default(),
            hovermode="closest",
            uirevision=f"peak_workflow_{self.resolved_process_name}_2d_scatter",
        )

        filtered_x_values, filtered_y_values = self._filter_2d_values_for_axis_scale(
            x_values=x_values,
            y_values=y_values,
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

        return figure

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

        for point in points:
            self._add_vertical_shape_line(
                figure=figure,
                x=point["x"],
                line_width=1,
                line_dash="dot",
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

        if upper_gate is not None and np.isfinite(upper_gate):
            shaded_lower_y = max(
                float(
                    upper_gate,
                ),
                float(
                    visible_lower_y,
                ),
            )

            shaded_upper_y = float(
                visible_upper_y,
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

    def _add_vertical_shape_line(
        self,
        *,
        figure: go.Figure,
        x: float,
        line_width: float,
        line_dash: str,
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

        figure.update_layout(
            font={
                "size": default_font_size,
            },
            legend={
                "x": 0.99,
                "y": 0.99,
                "xanchor": "right",
                "yanchor": "top",
                "bgcolor": "rgba(255, 255, 255, 0.72)",
                "bordercolor": "rgba(0, 0, 0, 0.18)",
                "borderwidth": 1,
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
            self._apply_trace_visualization_settings(
                trace=trace,
                default_marker_size=default_marker_size,
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
        return scale_selection_is_log(
            self.xscale_selection,
        ) or (
            isinstance(self.xscale_selection, (list, tuple, set))
            and Scatter2DGraph.x_log_value in self.xscale_selection
        )

    def _y_axis_is_log(self) -> bool:
        """
        Return whether y axis log scale is enabled.
        """
        return scale_selection_is_log(
            self.yscale_selection,
        ) or (
            isinstance(self.yscale_selection, (list, tuple, set))
            and Scatter2DGraph.y_log_value in self.yscale_selection
        )

    def _get_default_marker_size(self) -> float:
        """
        Return default marker size from runtime config.
        """
        return self._get_nested_config_float(
            path="visualization.default_marker_size",
            default=10.0,
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