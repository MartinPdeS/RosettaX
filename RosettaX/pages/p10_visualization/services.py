# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from RosettaX.utils import plottings, styling
from RosettaX.utils.reader import FCSFile
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.peak.core.graphing import apply_stable_2d_axis_ranges
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from RosettaX.workflow.upload import services as upload_services


VISUALIZATION_UPLOAD_DIRECTORY = (
    upload_services.DEFAULT_UPLOAD_DIRECTORY / "visualization"
)

PLOT_TYPE_HISTOGRAM = "histogram"
PLOT_TYPE_SCATTER = "scatter"
VISUALIZATION_FIGURE_HEIGHT_PX = 600
VISUALIZATION_HISTOGRAM_BIN_COUNT = 180
VISUALIZATION_SCATTER_DENSITY_BIN_COUNT = 120


def resolve_runtime_config(
    runtime_config_data: Any = None,
) -> RuntimeConfig:
    """
    Resolve the active runtime configuration for the visualization page.
    """
    if isinstance(runtime_config_data, dict):
        return RuntimeConfig.from_dict(runtime_config_data)

    return RuntimeConfig.from_default_profile()


def normalize_axis_scale(
    value: Any,
    *,
    default: str,
) -> str:
    """
    Normalize one axis scale selection to linear or log.
    """
    value_string = str(value or "").strip().lower()

    if value_string in ("linear", "log"):
        return value_string

    return default


def resolve_visualization_control_defaults(
    runtime_config_data: Any = None,
) -> dict[str, Any]:
    """
    Resolve visualization control defaults from the active runtime profile.
    """
    runtime_config = resolve_runtime_config(runtime_config_data)

    histogram_xscale = normalize_axis_scale(
        runtime_config.get_str(
            "calibration.histogram_xscale",
            default="log",
        ),
        default="log",
    )
    histogram_yscale = normalize_axis_scale(
        runtime_config.get_str(
            "calibration.histogram_yscale",
            default=runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            ),
        ),
        default="log",
    )
    visualization_settings = plottings.resolve_runtime_visualization_settings(
        runtime_config,
    )

    return {
        "max_events": runtime_config.get_int(
            "calibration.max_events_for_analysis",
            default=50_000,
        ),
        "x_log_values": ["enabled"] if histogram_xscale == "log" else [],
        "y_log_values": ["enabled"] if histogram_yscale == "log" else [],
        "colormap_log_values": (
            ["enabled"]
            if runtime_config.get_bool(
                "calibration.peak_graph_colormap_log",
                default=False,
            )
            else []
        ),
        "marker_size": visualization_settings["default_marker_size"],
        "marker_opacity": visualization_settings["default_marker_opacity"],
        "graph_style": {
            "height": runtime_config.get_graph_height(
                default=f"{VISUALIZATION_FIGURE_HEIGHT_PX}px",
            )
        },
        "show_grid": visualization_settings["show_grid"],
        "default_line_width": visualization_settings["default_line_width"],
        "default_font_size": visualization_settings["default_font_size"],
        "default_tick_size": visualization_settings["default_tick_size"],
    }


def build_channel_options(
    column_names: list[str],
) -> list[dict[str, str]]:
    """
    Build dropdown options from FCS parameter names.
    """
    return [
        {
            "label": str(column_name),
            "value": str(column_name),
        }
        for column_name in column_names
        if str(column_name).strip()
    ]


def resolve_default_channel(
    column_names: list[str],
    *,
    current_value: Any = None,
    fallback_index: int = 0,
) -> Optional[str]:
    """
    Resolve a stable channel selection from the available columns.
    """
    normalized_names = [
        str(column_name)
        for column_name in column_names
        if str(column_name).strip()
    ]

    current_value_string = str(current_value or "").strip()

    if current_value_string and current_value_string in normalized_names:
        return current_value_string

    if not normalized_names:
        return None

    resolved_index = min(
        max(int(fallback_index), 0),
        len(normalized_names) - 1,
    )

    return normalized_names[resolved_index]


def build_upload_summary(
    *,
    uploaded_fcs_path: str,
    uploaded_filename: str,
) -> dict[str, Any]:
    """
    Build one serializable uploaded-file summary for the visualization page.
    """
    with FCSFile(uploaded_fcs_path) as fcs_file:
        metadata = fcs_file.get_metadata()

        return {
            "uploaded_fcs_path": str(uploaded_fcs_path),
            "uploaded_filename": str(uploaded_filename),
            "column_names": list(metadata.column_names),
            "number_of_events": metadata.number_of_events,
            "number_of_parameters": metadata.number_of_parameters,
            "datatype": metadata.datatype,
            "mode": metadata.mode,
        }


def build_empty_figure(
    *,
    message: str,
) -> go.Figure:
    """
    Build an empty placeholder figure with one centered annotation.
    """
    figure = go.Figure()
    figure.update_layout(
        template="plotly_white",
        height=VISUALIZATION_FIGURE_HEIGHT_PX,
        margin={"l": 60, "r": 30, "t": 40, "b": 60},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": str(message),
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "size": 16,
                },
            }
        ],
    )
    return figure


def load_plot_dataframe(
    *,
    uploaded_fcs_path: str,
    x_channel: str,
    y_channel: Optional[str],
    max_events: int,
) -> pd.DataFrame:
    """
    Load one plotting dataframe from the requested FCS columns.
    """
    selected_columns = [
        str(x_channel),
    ]

    y_channel_string = str(y_channel or "").strip()

    if y_channel_string and y_channel_string not in selected_columns:
        selected_columns.append(y_channel_string)

    with FCSFile(uploaded_fcs_path) as fcs_file:
        return fcs_file.dataframe_copy(
            columns=selected_columns,
            dtype=float,
            n=int(max_events),
        )


def filter_dataframe_for_plot(
    dataframe: pd.DataFrame,
    *,
    x_channel: str,
    y_channel: Optional[str],
    log_x: bool,
    log_y: bool,
) -> tuple[pd.DataFrame, int]:
    """
    Filter invalid rows for plotting and return the number of skipped events.
    """
    y_channel_string = str(y_channel or "").strip()

    mask = np.isfinite(
        dataframe[x_channel].to_numpy(dtype=float, copy=False)
    )

    if y_channel_string:
        mask &= np.isfinite(
            dataframe[y_channel_string].to_numpy(dtype=float, copy=False)
        )

    if log_x:
        mask &= dataframe[x_channel].to_numpy(dtype=float, copy=False) > 0.0

    if log_y and y_channel_string:
        mask &= dataframe[y_channel_string].to_numpy(dtype=float, copy=False) > 0.0

    filtered_dataframe = dataframe.loc[mask].copy()
    skipped_events = int(len(dataframe) - len(filtered_dataframe))

    return filtered_dataframe, skipped_events


def build_visualization_figure(
    *,
    dataframe: pd.DataFrame,
    plot_type: str,
    x_channel: str,
    y_channel: Optional[str],
    log_x: bool,
    log_y: bool,
    colormap_log_scale: bool = False,
    marker_size: float = 5.0,
    marker_opacity: float = 0.72,
    runtime_config_data: Any = None,
) -> go.Figure:
    """
    Build one visualization figure from an FCS dataframe.
    """
    figure = go.Figure()
    y_channel_string = str(y_channel or "").strip()
    visualization_defaults = resolve_visualization_control_defaults(
        runtime_config_data,
    )

    if plot_type == PLOT_TYPE_HISTOGRAM:
        histogram_values = dataframe[x_channel].to_numpy(dtype=float, copy=False)
        histogram_values = histogram_values[np.isfinite(histogram_values)]

        if log_x:
            histogram_values = histogram_values[histogram_values > 0.0]

        if histogram_values.size == 0:
            return build_empty_figure(
                message="No plottable events remain for the selected histogram axis.",
            )

        histogram_min = float(np.min(histogram_values))
        histogram_max = float(np.max(histogram_values))

        if np.isclose(histogram_min, histogram_max):
            if log_x:
                histogram_min /= 1.1
                histogram_max *= 1.1
            else:
                histogram_min -= 0.5
                histogram_max += 0.5

        if log_x:
            bin_edges = np.logspace(
                np.log10(histogram_min),
                np.log10(histogram_max),
                VISUALIZATION_HISTOGRAM_BIN_COUNT + 1,
            )
        else:
            bin_edges = np.linspace(
                histogram_min,
                histogram_max,
                VISUALIZATION_HISTOGRAM_BIN_COUNT + 1,
            )

        histogram_counts, _ = np.histogram(
            histogram_values,
            bins=bin_edges,
        )
        bin_widths = np.diff(bin_edges)
        bin_centers = bin_edges[:-1] + (bin_widths / 2.0)

        figure.add_trace(
            go.Bar(
                x=bin_centers,
                y=histogram_counts,
                width=bin_widths,
                name=x_channel,
                marker={
                    "color": "#355070",
                    "line": {
                        "color": "#1b263b",
                        "width": 0.35,
                    },
                },
                opacity=0.92,
                hovertemplate="%{y} event(s)<extra></extra>",
            )
        )
        figure.update_yaxes(
            title_text="Count",
        )
    elif y_channel_string:
        x_values = dataframe[x_channel].to_numpy(dtype=float, copy=False)
        y_values = dataframe[y_channel_string].to_numpy(dtype=float, copy=False)
        resolved_marker_size = clamp_marker_size(marker_size)
        resolved_marker_opacity = clamp_marker_opacity(marker_opacity)
        density_values = compute_2d_density_values(
            x_values=x_values,
            y_values=y_values,
            x_log_scale=log_x,
            y_log_scale=log_y,
            colormap_log_scale=colormap_log_scale,
            number_of_bins=VISUALIZATION_SCATTER_DENSITY_BIN_COUNT,
        )

        figure.add_trace(
            go.Scattergl(
                x=dataframe[x_channel],
                y=dataframe[y_channel_string],
                mode="markers",
                marker={
                    "size": resolved_marker_size,
                    "opacity": resolved_marker_opacity,
                    "color": density_values,
                    "colorscale": "Turbo",
                    "showscale": False,
                },
                name="Events",
                customdata=density_values,
                hovertemplate=(
                    f"{x_channel}=%{{x:.6g}}<br>"
                    f"{y_channel_string}=%{{y:.6g}}<br>"
                    "density=%{customdata:.6g}"
                    "<extra></extra>"
                ),
            )
        )
        Scatter2DGraph.apply_formatting(
            figure=figure,
            title="Visualization scatter",
            x_axis_title=f"{x_channel} [a.u.]",
            y_axis_title=f"{y_channel_string} [a.u.]",
            x_axis_type="log" if log_x else "linear",
            y_axis_type="log" if log_y else "linear",
            show_grid=bool(visualization_defaults["show_grid"]),
            hovermode="closest",
            uirevision="visualization_scatter_2d",
        )
        for trace in figure.data:
            if getattr(trace, "type", "") in ("scatter", "scattergl") and hasattr(trace, "marker"):
                trace.marker.size = resolved_marker_size
                trace.marker.opacity = resolved_marker_opacity
        figure = apply_stable_2d_axis_ranges(
            figure=figure,
            x_values=x_values,
            y_values=y_values,
            x_log_scale=log_x,
            y_log_scale=log_y,
        )
        figure.update_layout(
            showlegend=False,
            height=VISUALIZATION_FIGURE_HEIGHT_PX,
        )
    else:
        return build_empty_figure(
            message="Select a Y channel for 2D plots.",
        )

    if plot_type == PLOT_TYPE_HISTOGRAM:
        figure.update_layout(
            template="plotly_white",
            height=VISUALIZATION_FIGURE_HEIGHT_PX,
            margin={"l": 70, "r": 30, "t": 40, "b": 70},
            bargap=0.0,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1.0,
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        figure.update_xaxes(
            title_text=x_channel,
            type="log" if log_x else "linear",
            showgrid=bool(visualization_defaults["show_grid"]),
            zeroline=False,
        )

    plottings.apply_default_visual_style(
        figure,
        marker_size=float(resolved_marker_size) if plot_type == PLOT_TYPE_SCATTER and y_channel_string else float(visualization_defaults["marker_size"]),
        line_width=float(visualization_defaults["default_line_width"]),
        font_size=float(visualization_defaults["default_font_size"]),
        tick_size=float(visualization_defaults["default_tick_size"]),
        show_grid=bool(visualization_defaults["show_grid"]),
    )

    if plot_type == PLOT_TYPE_SCATTER and y_channel_string:
        for trace in figure.data:
            if getattr(trace, "type", "") in ("scatter", "scattergl") and hasattr(trace, "marker"):
                trace.marker.size = resolved_marker_size
                trace.marker.opacity = resolved_marker_opacity

    return figure


def compute_2d_density_values(
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

        valid_density_values = compute_2d_density_values(
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


def build_plot_status_text(
    *,
    plotted_events: int,
    skipped_events: int,
) -> str:
    """
    Build one concise plot status summary.
    """
    if skipped_events <= 0:
        return f"Showing {plotted_events} event(s)."

    return (
        f"Showing {plotted_events} event(s). "
        f"Skipped {skipped_events} non-finite or non-positive event(s) for the selected axes."
    )


def clamp_max_events(
    value: Any,
    *,
    default: int = 50_000,
    minimum: int = 100,
    maximum: int = 2_000_000,
) -> int:
    """
    Clamp one requested plot event count to a safe integer range.
    """
    try:
        resolved_value = int(value)
    except Exception:
        return int(default)

    return max(
        int(minimum),
        min(
            int(maximum),
            resolved_value,
        ),
    )


def clamp_marker_size(
    value: Any,
    *,
    default: float = 7.0,
    minimum: float = 1.0,
    maximum: float = 24.0,
) -> float:
    """
    Clamp one requested scatter marker size to a safe range.
    """
    try:
        resolved_value = float(value)
    except Exception:
        return float(default)

    return max(
        float(minimum),
        min(
            float(maximum),
            resolved_value,
        ),
    )


def clamp_marker_opacity(
    value: Any,
    *,
    default: float = 1.0,
    minimum: float = 0.05,
    maximum: float = 1.0,
) -> float:
    """
    Clamp one requested scatter marker opacity to a safe range.
    """
    try:
        resolved_value = float(value)
    except Exception:
        return float(default)

    return max(
        float(minimum),
        min(
            float(maximum),
            resolved_value,
        ),
    )
