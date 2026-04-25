# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objs as go

from RosettaX.peak_script.registry import get_process_instance
from RosettaX.peak_script.registry import resolve_process_name
from RosettaX.peak_workflow.detectors import clean_optional_string
from RosettaX.peak_workflow.detectors import resolve_detector_channels_for_process
from RosettaX.peak_workflow.detectors import resolve_process_setting_state
from RosettaX.peak_workflow.state import build_empty_peak_lines_payload
from RosettaX.utils import casting
from RosettaX.utils import plottings
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PeakGraphInputs:
    """
    Parsed graph inputs.
    """

    graph_enabled: bool
    nbins: int
    yscale_selection: Any
    max_events: int


@dataclass(frozen=True)
class Context1D:
    """
    Validated context for 1D plotting.
    """

    uploaded_fcs_path: str
    detector_channel: str


@dataclass(frozen=True)
class Context2D:
    """
    Validated context for 2D plotting.
    """

    uploaded_fcs_path: str
    x_channel: str
    y_channel: str


def is_enabled(value: Any) -> bool:
    """
    Return whether a Dash checklist value means enabled.
    """
    return isinstance(value, list) and "enabled" in value


def parse_peak_graph_callback_inputs(
    *,
    graph_toggle_value: Any,
    nbins: Any,
    yscale_selection: Any,
    max_events_for_plots: Any,
    runtime_config_data: Any,
) -> PeakGraphInputs:
    """
    Parse and validate graph callback inputs.
    """
    runtime_config = RuntimeConfig.from_dict(
        runtime_config_data if isinstance(runtime_config_data, dict) else None
    )

    resolved_nbins = casting.as_int(
        nbins,
        default=runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        ),
        min_value=10,
        max_value=10_000,
    )

    resolved_max_events = casting.as_int(
        max_events_for_plots,
        default=runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=10000,
        ),
        min_value=1,
        max_value=5_000_000,
    )

    return PeakGraphInputs(
        graph_enabled=is_enabled(graph_toggle_value),
        nbins=resolved_nbins,
        yscale_selection=yscale_selection,
        max_events=resolved_max_events,
    )


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
    yscale_selection: Any,
    nbins: Any,
    peak_lines_payload: Any,
    max_events_for_plots: Any,
    runtime_config_data: Any,
) -> go.Figure:
    """
    Build the graph for the selected peak process.
    """
    resolved_process_name = resolve_process_name(
        process_name,
    )

    process = get_process_instance(
        process_name=resolved_process_name,
    )

    callback_inputs = parse_peak_graph_callback_inputs(
        graph_toggle_value=graph_toggle_value,
        nbins=nbins,
        yscale_selection=yscale_selection,
        max_events_for_plots=max_events_for_plots,
        runtime_config_data=runtime_config_data,
    )

    if not callback_inputs.graph_enabled:
        return plottings._make_info_figure(
            "Graph is hidden.",
        )

    if process is None:
        return plottings._make_info_figure(
            "No valid peak process selected.",
        )

    detector_channels = resolve_detector_channels_for_process(
        detector_dropdown_ids=detector_dropdown_ids,
        detector_dropdown_values=detector_dropdown_values,
        process_name=resolved_process_name,
    )

    process_settings = resolve_process_setting_state(
        process_setting_ids=process_setting_ids,
        process_setting_values=process_setting_values,
        process_name=resolved_process_name,
    )

    if process.graph_type == "2d_scatter":
        return build_2d_figure(
            uploaded_fcs_path=uploaded_fcs_path,
            x_channel=detector_channels.get("x"),
            y_channel=detector_channels.get("y"),
            max_events=callback_inputs.max_events,
            peak_lines_payload=peak_lines_payload,
            x_log_scale=is_enabled(process_settings.get("x_log_scale")),
            y_log_scale=is_enabled(process_settings.get("y_log_scale")),
        )

    return build_1d_histogram_figure(
        backend=backend,
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channel=detector_channels.get("primary"),
        nbins=callback_inputs.nbins,
        yscale_selection=callback_inputs.yscale_selection,
        max_events=callback_inputs.max_events,
        peak_lines_payload=peak_lines_payload,
    )


def validate_context_1d(
    *,
    uploaded_fcs_path: Any,
    detector_channel: Any,
) -> Optional[Context1D]:
    """
    Validate context required by 1D plotting.
    """
    uploaded_fcs_path_clean = clean_optional_string(
        uploaded_fcs_path,
    )

    detector_channel_clean = clean_optional_string(
        detector_channel,
    )

    if not uploaded_fcs_path_clean:
        return None

    if not detector_channel_clean:
        return None

    return Context1D(
        uploaded_fcs_path=uploaded_fcs_path_clean,
        detector_channel=detector_channel_clean,
    )


def validate_context_2d(
    *,
    uploaded_fcs_path: Any,
    x_channel: Any,
    y_channel: Any,
) -> Optional[Context2D]:
    """
    Validate context required by 2D plotting.
    """
    uploaded_fcs_path_clean = clean_optional_string(
        uploaded_fcs_path,
    )

    x_channel_clean = clean_optional_string(
        x_channel,
    )

    y_channel_clean = clean_optional_string(
        y_channel,
    )

    if not uploaded_fcs_path_clean:
        return None

    if not x_channel_clean:
        return None

    if not y_channel_clean:
        return None

    return Context2D(
        uploaded_fcs_path=uploaded_fcs_path_clean,
        x_channel=x_channel_clean,
        y_channel=y_channel_clean,
    )


def build_1d_histogram_figure(
    *,
    backend: Any,
    uploaded_fcs_path: Any,
    detector_channel: Any,
    nbins: int,
    yscale_selection: Any,
    max_events: int,
    peak_lines_payload: Any,
) -> go.Figure:
    """
    Build a 1D histogram figure with peak line overlays.
    """
    context = validate_context_1d(
        uploaded_fcs_path=uploaded_fcs_path,
        detector_channel=detector_channel,
    )

    if context is None:
        return plottings._make_info_figure(
            "Upload an FCS file and select a detector first.",
        )

    if backend is None:
        return plottings._make_info_figure(
            "Backend is not initialized. Upload an FCS file again.",
        )

    line_positions, line_labels = parse_1d_peak_lines_payload(
        peak_lines_payload,
    )

    histogram_result = backend.build_histogram(
        detector_column=context.detector_channel,
        n_bins_for_plots=nbins,
        max_events_for_analysis=max_events,
    )

    figure = backend.build_histogram_figure(
        histogram_result=histogram_result,
        detector_column=context.detector_channel,
        use_log_counts=isinstance(yscale_selection, list)
        and ("log" in yscale_selection),
        peak_positions=line_positions,
    )

    figure = plottings.add_vertical_lines(
        fig=figure,
        line_positions=line_positions,
        line_labels=line_labels,
    )

    figure.update_layout(
        separators=".,",
        clickmode="event+select",
    )

    return figure


def build_2d_figure(
    *,
    uploaded_fcs_path: Any,
    x_channel: Any,
    y_channel: Any,
    max_events: int,
    peak_lines_payload: Any,
    x_log_scale: bool = False,
    y_log_scale: bool = False,
) -> go.Figure:
    """
    Build a 2D scatter plot.
    """
    context = validate_context_2d(
        uploaded_fcs_path=uploaded_fcs_path,
        x_channel=x_channel,
        y_channel=y_channel,
    )

    if context is None:
        return plottings._make_info_figure(
            "Upload an FCS file and select X and Y detector channels first.",
        )

    try:
        x_values, y_values = read_2d_channel_values(
            uploaded_fcs_path=context.uploaded_fcs_path,
            x_channel=context.x_channel,
            y_channel=context.y_channel,
            max_events=max_events,
        )

    except Exception as exc:
        logger.exception(
            "Failed to read 2D channel values uploaded_fcs_path=%r x_channel=%r y_channel=%r",
            context.uploaded_fcs_path,
            context.x_channel,
            context.y_channel,
        )

        return plottings._make_info_figure(
            f"{type(exc).__name__}: {exc}",
        )

    if x_log_scale or y_log_scale:
        x_values, y_values = filter_values_for_log_axes(
            x_values=x_values,
            y_values=y_values,
            x_log_scale=x_log_scale,
            y_log_scale=y_log_scale,
        )

    figure = go.Figure()

    figure.add_trace(
        go.Scattergl(
            x=x_values,
            y=y_values,
            mode="markers",
            marker={
                "size": 6,
                "opacity": 0.45,
            },
            name="Events",
            hoverinfo="none",
        )
    )

    add_2d_peak_vertical_lines_to_figure(
        figure=figure,
        peak_lines_payload=peak_lines_payload,
    )

    figure.update_layout(
        xaxis_title=context.x_channel,
        yaxis_title=context.y_channel,
        xaxis={
            "type": "log" if x_log_scale else "linear",
        },
        yaxis={
            "type": "log" if y_log_scale else "linear",
        },
        margin={
            "l": 60,
            "r": 20,
            "t": 20,
            "b": 60,
        },
        clickmode="event+select",
        separators=".,",
    )

    return figure


def filter_values_for_log_axes(
    *,
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_log_scale: bool,
    y_log_scale: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove non positive values for log axes.
    """
    valid_mask = np.ones_like(
        x_values,
        dtype=bool,
    )

    if x_log_scale:
        valid_mask &= x_values > 0.0

    if y_log_scale:
        valid_mask &= y_values > 0.0

    return x_values[valid_mask], y_values[valid_mask]


def read_2d_channel_values(
    *,
    uploaded_fcs_path: str,
    x_channel: str,
    y_channel: str,
    max_events: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Read two FCS channels as NumPy arrays.
    """
    with FCSFile(uploaded_fcs_path) as fcs_file:
        x_values = np.asarray(
            fcs_file.column_copy(
                x_channel,
                dtype=float,
                n=max_events,
            ),
            dtype=float,
        ).reshape(-1)

        y_values = np.asarray(
            fcs_file.column_copy(
                y_channel,
                dtype=float,
                n=max_events,
            ),
            dtype=float,
        ).reshape(-1)

    event_count = min(
        x_values.size,
        y_values.size,
    )

    x_values = x_values[:event_count]
    y_values = y_values[:event_count]

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)

    return x_values[finite_mask], y_values[finite_mask]


def add_2d_peak_vertical_lines_to_figure(
    *,
    figure: go.Figure,
    peak_lines_payload: Any,
) -> None:
    """
    Add vertical lines for picked 2D peaks.
    """
    points, labels = parse_2d_peak_lines_payload(
        peak_lines_payload,
    )

    if not points:
        return

    for index, point in enumerate(points):
        label = (
            labels[index]
            if index < len(labels)
            else f"Peak {index + 1}"
        )

        figure.add_vline(
            x=float(point["x"]),
            line_width=2,
            line_dash="dash",
            annotation_text=label,
            annotation_position="top",
        )


def parse_1d_peak_lines_payload(
    peak_lines_payload: Any,
) -> tuple[list[float], list[str]]:
    """
    Parse 1D peak line positions and labels.
    """
    if not isinstance(peak_lines_payload, dict):
        return [], []

    line_positions: list[float] = []
    line_labels: list[str] = []

    for value in peak_lines_payload.get("positions") or []:
        try:
            line_positions.append(
                float(value),
            )

        except Exception:
            logger.debug(
                "Ignoring non numeric 1D peak line position value=%r",
                value,
            )

    for value in peak_lines_payload.get("labels") or []:
        line_labels.append(
            str(value),
        )

    if len(line_labels) < len(line_positions):
        line_labels = [
            *line_labels,
            *[
                f"Peak {index + 1}"
                for index in range(len(line_labels), len(line_positions))
            ],
        ]

    if len(line_labels) > len(line_positions):
        line_labels = line_labels[: len(line_positions)]

    return line_positions, line_labels


def parse_2d_peak_lines_payload(
    peak_lines_payload: Any,
) -> tuple[list[dict[str, float]], list[str]]:
    """
    Parse 2D peak points and labels.
    """
    if not isinstance(peak_lines_payload, dict):
        return [], []

    raw_points = peak_lines_payload.get("points")
    points: list[dict[str, float]] = []

    if isinstance(raw_points, list):
        for raw_point in raw_points:
            if not isinstance(raw_point, dict):
                continue

            try:
                points.append(
                    {
                        "x": float(raw_point["x"]),
                        "y": float(raw_point["y"]),
                    }
                )

            except Exception:
                logger.debug(
                    "Ignoring invalid 2D point=%r",
                    raw_point,
                )

    labels = [
        str(value)
        for value in (peak_lines_payload.get("labels") or [])
    ]

    if len(labels) < len(points):
        labels = [
            *labels,
            *[
                f"Peak {index + 1}"
                for index in range(len(labels), len(points))
            ],
        ]

    if len(labels) > len(points):
        labels = labels[: len(points)]

    return points, labels