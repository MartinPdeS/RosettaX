# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import numpy as np
import plotly.graph_objs as go

from ..core import graphing
from RosettaX.utils import plottings


logger = logging.getLogger(__name__)


PEAK_GRAPH_HEIGHT = 850


def register_graph_callbacks(
    *,
    page: Any,
    ids: Any,
    adapter: Any,
    page_state_store_id: str,
    max_events_input_id: Any,
    runtime_config_store_id: str,
) -> None:
    """
    Register the main peak workflow graph callback.
    """
    del page

    axis_scale_toggle_id = resolve_axis_scale_toggle_id(
        ids=ids,
    )

    state_components: list[Any] = [
        dash.State(
            ids.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            ids.process_setting_pattern(),
            "id",
        ),
    ]

    if max_events_input_id is not None:
        state_components.append(
            dash.State(
                max_events_input_id,
                "value",
                allow_optional=True,
            )
        )

    state_components.append(
        dash.State(
            runtime_config_store_id,
            "data",
        )
    )

    @dash.callback(
        dash.Output(
            ids.graph_hist,
            "figure",
        ),
        dash.Input(
            ids.graph_toggle_switch,
            "value",
        ),
        dash.Input(
            axis_scale_toggle_id,
            "value",
        ),
        dash.Input(
            page_state_store_id,
            "data",
        ),
        dash.Input(
            ids.nbins_input,
            "value",
        ),
        dash.Input(
            ids.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(
            ids.process_dropdown,
            "value",
        ),
        dash.Input(
            ids.process_setting_pattern(),
            "value",
        ),
        *state_components,
        prevent_initial_call=False,
    )
    def update_graph(
        graph_toggle_value: Any,
        axis_scale_toggle_values: Any,
        page_state_payload: Any,
        nbins: Any,
        detector_dropdown_values: list[Any],
        process_name: Any,
        process_setting_values: list[Any],
        detector_dropdown_ids: list[dict[str, Any]],
        process_setting_ids: list[dict[str, Any]],
        *state_values: Any,
    ) -> go.Figure:
        """
        Build the peak workflow graph.

        The base graph construction is delegated to ``graphing``. This callback
        then optionally adds grouped traces when a peak process stores group
        payloads in the peak line payload.
        """
        if max_events_input_id is not None:
            max_events_for_plots = state_values[0]
            runtime_config_data = state_values[1] if len(state_values) > 1 else None

        else:
            max_events_for_plots = None
            runtime_config_data = state_values[0] if state_values else None

        page_state = adapter.get_page_state_from_payload(
            page_state_payload,
        )

        uploaded_fcs_path = adapter.get_uploaded_fcs_path(
            page_state=page_state,
        )

        peak_lines_payload = adapter.get_peak_lines_payload(
            page_state=page_state,
        )

        backend = adapter.get_backend(
            uploaded_fcs_path=uploaded_fcs_path,
        )

        x_log_scale = axis_scale_toggle_contains(
            axis_scale_toggle_values=axis_scale_toggle_values,
            expected_value="x_log",
        )

        y_log_scale = axis_scale_toggle_contains(
            axis_scale_toggle_values=axis_scale_toggle_values,
            expected_value="y_log",
        )

        try:
            figure = graphing.build_peak_workflow_graph_figure(
                backend=backend,
                uploaded_fcs_path=uploaded_fcs_path,
                process_name=process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
                process_setting_ids=process_setting_ids,
                process_setting_values=process_setting_values,
                graph_toggle_value=graph_toggle_value,
                xscale_selection=axis_scale_toggle_values,
                yscale_selection=axis_scale_toggle_values,
                nbins=nbins,
                peak_lines_payload=peak_lines_payload,
                max_events_for_plots=max_events_for_plots,
                runtime_config_data=runtime_config_data,
            )

            figure = add_grouped_payload_traces(
                figure=figure,
                peak_lines_payload=peak_lines_payload,
                nbins=nbins,
                x_log_scale=x_log_scale,
                y_log_scale=y_log_scale,
            )

            apply_peak_graph_layout(
                figure=figure,
            )

            return figure

        except Exception as exc:
            logger.exception(
                "Failed to build peak workflow graph."
            )

            figure = plottings._make_info_figure(
                f"{type(exc).__name__}: {exc}",
            )

            apply_peak_graph_layout(
                figure=figure,
            )

            return figure


def resolve_axis_scale_toggle_id(
    *,
    ids: Any,
) -> str:
    """
    Resolve the shared Scatter2DGraph axis scale toggle ID.

    Prefer the explicit ``ids.axis_scale_toggle`` field. Fall back to a
    deterministic ID only for older ID classes during migration.
    """
    axis_scale_toggle_id = getattr(
        ids,
        "axis_scale_toggle",
        None,
    )

    if isinstance(axis_scale_toggle_id, str) and axis_scale_toggle_id:
        return axis_scale_toggle_id

    if callable(axis_scale_toggle_id):
        resolved_axis_scale_toggle_id = axis_scale_toggle_id()

        if isinstance(resolved_axis_scale_toggle_id, str) and resolved_axis_scale_toggle_id:
            return resolved_axis_scale_toggle_id

    return f"{ids.graph_hist}-axis-scale-toggle"


def axis_scale_toggle_contains(
    *,
    axis_scale_toggle_values: Any,
    expected_value: str,
) -> bool:
    """
    Return whether the shared axis scale toggle contains a value.
    """
    if isinstance(axis_scale_toggle_values, str):
        return axis_scale_toggle_values == expected_value

    if isinstance(axis_scale_toggle_values, (list, tuple, set)):
        return expected_value in axis_scale_toggle_values

    return False


def apply_peak_graph_layout(
    *,
    figure: go.Figure,
) -> go.Figure:
    """
    Apply shared peak graph layout settings.
    """
    figure.update_layout(
        height=PEAK_GRAPH_HEIGHT,
        margin={
            "l": 70,
            "r": 30,
            "t": 55,
            "b": 70,
        },
    )

    return figure


def add_grouped_payload_traces(
    *,
    figure: go.Figure,
    peak_lines_payload: Any,
    nbins: Any,
    x_log_scale: bool,
    y_log_scale: bool,
) -> go.Figure:
    """
    Add grouped traces stored by peak processes.

    ``group_values`` creates one histogram trace per 1D group.

    ``group_points`` creates one scatter trace per 2D group.
    """
    if not isinstance(peak_lines_payload, dict):
        return figure

    figure = add_grouped_1d_histogram_traces(
        figure=figure,
        peak_lines_payload=peak_lines_payload,
        nbins=nbins,
    )

    figure = add_grouped_2d_scatter_traces(
        figure=figure,
        peak_lines_payload=peak_lines_payload,
        x_log_scale=x_log_scale,
        y_log_scale=y_log_scale,
    )

    return figure


def add_grouped_1d_histogram_traces(
    *,
    figure: go.Figure,
    peak_lines_payload: dict[str, Any],
    nbins: Any,
) -> go.Figure:
    """
    Add one histogram trace per K means 1D group.

    Plotly automatically assigns a different color to each trace unless a color
    is explicitly set elsewhere.
    """
    group_values = peak_lines_payload.get(
        "group_values",
        [],
    )

    group_labels = peak_lines_payload.get(
        "group_labels",
        [],
    )

    if not isinstance(group_values, list):
        return figure

    if not group_values:
        return figure

    resolved_nbins = resolve_histogram_bin_count(
        nbins=nbins,
    )

    visible_group_count = 0

    for group_index, raw_values in enumerate(group_values):
        values = sanitize_numeric_values(
            values=raw_values,
        )

        if values.size == 0:
            continue

        group_label = resolve_group_label(
            group_labels=group_labels,
            group_index=group_index,
        )

        figure.add_trace(
            go.Histogram(
                x=values,
                nbinsx=resolved_nbins,
                name=group_label,
                opacity=0.72,
                bingroup="kmeans_1d_groups",
            )
        )

        visible_group_count += 1

    if visible_group_count == 0:
        return figure

    soften_existing_traces(
        figure=figure,
        softened_types=(
            "histogram",
            "bar",
        ),
        protected_name_prefixes=(
            "K means cluster",
        ),
        opacity=0.22,
    )

    figure.update_layout(
        barmode="overlay",
        showlegend=True,
    )

    logger.debug(
        "Added grouped 1D histogram traces: count=%d",
        visible_group_count,
    )

    return figure


def add_grouped_2d_scatter_traces(
    *,
    figure: go.Figure,
    peak_lines_payload: dict[str, Any],
    x_log_scale: bool,
    y_log_scale: bool,
) -> go.Figure:
    """
    Add one Scattergl trace per K means 2D group.

    Expected payload shape
    ----------------------
    ``group_points`` must be a list of dictionaries:

    ``{"x_values": [...], "y_values": [...]}``

    Plotly automatically assigns a different color to each trace unless a color
    is explicitly set elsewhere.
    """
    group_points = peak_lines_payload.get(
        "group_points",
        [],
    )

    group_labels = peak_lines_payload.get(
        "group_labels",
        [],
    )

    if not isinstance(group_points, list):
        return figure

    if not group_points:
        return figure

    visible_group_count = 0

    for group_index, raw_group_points in enumerate(group_points):
        x_values, y_values = sanitize_group_points(
            group_points=raw_group_points,
            x_log_scale=x_log_scale,
            y_log_scale=y_log_scale,
        )

        if x_values.size == 0:
            continue

        group_label = resolve_group_label(
            group_labels=group_labels,
            group_index=group_index,
        )

        figure.add_trace(
            go.Scattergl(
                x=x_values,
                y=y_values,
                mode="markers",
                name=group_label,
                marker={
                    "size": 4,
                    "opacity": 0.72,
                },
            )
        )

        visible_group_count += 1

    if visible_group_count == 0:
        return figure

    soften_existing_traces(
        figure=figure,
        softened_types=(
            "scatter",
            "scattergl",
        ),
        protected_name_prefixes=(
            "K means cluster",
        ),
        opacity=0.08,
    )

    figure.update_layout(
        showlegend=True,
    )

    logger.debug(
        "Added grouped 2D scatter traces: count=%d",
        visible_group_count,
    )

    return figure


def soften_existing_traces(
    *,
    figure: go.Figure,
    softened_types: tuple[str, ...],
    protected_name_prefixes: tuple[str, ...],
    opacity: float,
) -> None:
    """
    Reduce opacity of base traces after grouped traces are added.
    """
    for trace in figure.data:
        trace_type = str(
            getattr(
                trace,
                "type",
                "",
            )
            or ""
        )

        if trace_type not in softened_types:
            continue

        trace_name = str(
            getattr(
                trace,
                "name",
                "",
            )
            or ""
        ).strip()

        if trace_name.startswith(protected_name_prefixes):
            continue

        try:
            trace.opacity = float(
                opacity,
            )

        except Exception:
            logger.debug(
                "Could not update opacity for trace=%r",
                trace_name,
            )


def sanitize_numeric_values(
    *,
    values: Any,
) -> np.ndarray:
    """
    Convert an arbitrary value container to a finite one dimensional float array.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)

    except (TypeError, ValueError):
        return np.asarray(
            [],
            dtype=float,
        )

    return array[
        np.isfinite(
            array,
        )
    ]


def sanitize_group_points(
    *,
    group_points: Any,
    x_log_scale: bool,
    y_log_scale: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert a grouped 2D point payload to finite x and y arrays.
    """
    if not isinstance(group_points, dict):
        return (
            np.asarray([], dtype=float),
            np.asarray([], dtype=float),
        )

    try:
        x_values = np.asarray(
            group_points.get(
                "x_values",
                [],
            ),
            dtype=float,
        ).reshape(-1)

        y_values = np.asarray(
            group_points.get(
                "y_values",
                [],
            ),
            dtype=float,
        ).reshape(-1)

    except (TypeError, ValueError):
        return (
            np.asarray([], dtype=float),
            np.asarray([], dtype=float),
        )

    common_size = min(
        x_values.size,
        y_values.size,
    )

    x_values = x_values[
        :common_size
    ]

    y_values = y_values[
        :common_size
    ]

    finite_mask = (
        np.isfinite(
            x_values,
        )
        & np.isfinite(
            y_values,
        )
    )

    if x_log_scale:
        finite_mask = finite_mask & (
            x_values > 0.0
        )

    if y_log_scale:
        finite_mask = finite_mask & (
            y_values > 0.0
        )

    return (
        x_values[
            finite_mask
        ],
        y_values[
            finite_mask
        ],
    )


def resolve_group_label(
    *,
    group_labels: Any,
    group_index: int,
) -> str:
    """
    Resolve the label for one grouped trace.
    """
    if isinstance(group_labels, list) and group_index < len(group_labels):
        label = str(
            group_labels[group_index],
        ).strip()

        if label:
            return label

    return f"K means cluster {group_index + 1}"


def resolve_histogram_bin_count(
    *,
    nbins: Any,
) -> int:
    """
    Resolve a safe histogram bin count.
    """
    try:
        resolved_nbins = int(
            nbins,
        )

    except (TypeError, ValueError):
        resolved_nbins = 128

    resolved_nbins = max(
        10,
        resolved_nbins,
    )

    resolved_nbins = min(
        5000,
        resolved_nbins,
    )

    return resolved_nbins