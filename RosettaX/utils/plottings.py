# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import plotly.graph_objs as go

from RosettaX.utils.io import load_signal
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import styling
from RosettaX.workflow.plotting.models import AxisOptions, HistogramOptions
from RosettaX.workflow.plotting.transforms import (
    build_histogram_arrays,
    finite_plot_values,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HistogramResult:
    """
    Immutable container for a 1D histogram computed from detector signal data.

    Attributes
    ----------
    values : np.ndarray
        Raw signal values used to build the histogram.
    counts : np.ndarray
        Event counts in each bin.
    edges : np.ndarray
        Bin edge positions (length = ``len(counts) + 1``).
    centers : np.ndarray
        Bin centre positions (length = ``len(counts)``).
    """

    values: np.ndarray
    counts: np.ndarray
    edges: np.ndarray
    centers: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise all arrays to plain Python lists for JSON storage.

        Returns
        -------
        dict[str, Any]
            Dictionary with keys ``values``, ``counts``, ``edges``, and
            ``centers``, each containing a Python list of floats.
        """
        return {
            "values": self.values.tolist(),
            "counts": self.counts.tolist(),
            "edges": self.edges.tolist(),
            "centers": self.centers.tolist(),
        }


def build_histogram(
    fcs_file_path: str,
    detector_column: str,
    n_bins_for_plots: int,
    max_events_for_analysis: Optional[int] = None,
    use_log_x_bins: bool = False,
    options: Optional[HistogramOptions] = None,
) -> HistogramResult:
    """
    Build a 1D histogram from a detector signal in an FCS file.

    Parameters
    ----------
    fcs_file_path : str
        Absolute or relative path to the FCS file.
    detector_column : str
        Name of the detector column to read.
    n_bins_for_plots : int
        Number of bins to use for the histogram.
    max_events_for_analysis : Optional[int]
        If provided, only the first *max_events_for_analysis* events are used.
    use_log_x_bins : bool
        If ``True``, bins are equally spaced in log10(x) (geometric edges).
        Non-positive values are excluded because log bins require x > 0.

    Returns
    -------
    HistogramResult
        Histogram data including raw values, counts, edges, and bin centres.

    Raises
    ------
    ValueError
        If no finite signal values are available after loading.
    """
    resolved_detector_column = str(detector_column).strip()
    resolved_options = options or HistogramOptions(
        bin_count=int(n_bins_for_plots),
        max_events=max_events_for_analysis,
        axes=AxisOptions(x_log=bool(use_log_x_bins)),
    )
    n_bins_for_plots = resolved_options.bin_count
    max_events_for_analysis = resolved_options.max_events
    use_log_x_bins = resolved_options.axes.x_log

    logger.debug(
        "build_histogram called with detector_column=%r n_bins_for_plots=%r max_events_for_analysis=%r use_log_x_bins=%r",
        resolved_detector_column,
        n_bins_for_plots,
        max_events_for_analysis,
        use_log_x_bins,
    )

    values = load_signal(
        fcs_file_path=fcs_file_path,
        detector_column=resolved_detector_column,
        max_events_for_analysis=max_events_for_analysis,
        require_positive_values=False,
    )

    if values.size == 0:
        raise ValueError("No signal values available to build histogram.")

    values_for_histogram = finite_plot_values(
        values,
        positive_only=resolved_options.axes.x_log,
    )
    counts, edges, centers = build_histogram_arrays(
        values_for_histogram,
        bin_count=resolved_options.bin_count,
        log_x=resolved_options.axes.x_log,
    )

    histogram_result = HistogramResult(
        values=np.asarray(values_for_histogram, dtype=float),
        counts=np.asarray(counts, dtype=float),
        edges=np.asarray(edges, dtype=float),
        centers=np.asarray(centers, dtype=float),
    )

    logger.debug(
        "build_histogram returning detector_column=%r n_values=%r n_bins=%r nonzero_bins=%r",
        resolved_detector_column,
        histogram_result.values.size,
        histogram_result.counts.size,
        int(np.count_nonzero(histogram_result.counts)),
    )

    return histogram_result


def build_histogram_figure(
    detector_column: str,
    histogram_result: HistogramResult,
    use_log_counts: bool = False,
    peak_positions: Optional[np.ndarray] = None,
) -> go.Figure:
    """
    Build a Plotly bar chart figure from a pre-computed histogram.

    Parameters
    ----------
    detector_column : str
        Detector column name used to label the x axis.
    histogram_result : HistogramResult
        Pre-computed histogram data (bin centres and counts).
    use_log_counts : bool
        If ``True``, the y axis is rendered on a logarithmic scale.
    peak_positions : Optional[np.ndarray]
        Optional array of peak x positions.  Each position is drawn as a
        vertical dashed line on the figure.

    Returns
    -------
    go.Figure
        Plotly figure with a bar trace and optional vertical peak lines.
    """
    resolved_detector_column = str(detector_column).strip()

    logger.debug(
        "build_histogram_figure called with detector_column=%r use_log_counts=%r peak_count=%r",
        resolved_detector_column,
        use_log_counts,
        0 if peak_positions is None else len(np.asarray(peak_positions).reshape(-1)),
    )

    figure = go.Figure()

    step_x = np.repeat(
        histogram_result.edges,
        2,
    )[1:-1]
    step_y = np.repeat(
        histogram_result.counts,
        2,
    )

    figure.add_trace(
        go.Scatter(
            x=step_x,
            y=step_y,
            mode="lines",
            fill="tozeroy",
            name="signal",
            line={
                "shape": "linear",
            },
        )
    )

    for peak_position in np.asarray(
        peak_positions if peak_positions is not None else [],
        dtype=float,
    ):
        figure.add_vline(
            x=float(peak_position),
            line_width=2,
            line_dash="dash",
        )

    figure.update_layout(
        xaxis_title=f"{resolved_detector_column} [a.u.]",
        yaxis_title="Count",
        hovermode="closest",
        separators=".,",
        bargap=0.0,
    )
    figure.update_yaxes(type="log" if bool(use_log_counts) else "linear")

    return figure


def make_histogram_with_lines(
    *,
    values: np.ndarray,
    nbins: int,
    xaxis_title: str,
    line_positions: list[float],
    line_labels: list[str],
    overlay_values: Optional[np.ndarray] = None,
    base_name: str = "all events",
    overlay_name: str = "gated events",
    title: Optional[str] = None,
    line_width: float = 2.0,
    line_dash: str = "dash",
    font_size: float = 14.0,
    tick_size: float = 12.0,
) -> go.Figure:
    """
    Build a histogram figure with optional vertical lines.

    Parameters
    ----------
    values : np.ndarray
        Array of values to plot in the histogram.
    nbins : int
        Number of bins for the histogram.
    xaxis_title : str
        Label for the x axis.
    line_positions : list[float]
        X positions for vertical lines to indicate peaks or thresholds.
    line_labels : list[str]
        Labels corresponding to each vertical line.
    overlay_values : Optional[np.ndarray]
        Optional second set of values to overlay as a second histogram.
    base_name : str
        Legend name for the main histogram.
    overlay_name : str
        Legend name for the overlay histogram.
    title : Optional[str]
        Optional title for the figure.
    line_width : float
        Width of the vertical guide lines.
    line_dash : str
        Dash style of the vertical guide lines.
    font_size : float
        Font size used for titles, legend, annotations, and general labels.
    tick_size : float
        Font size used for axis tick labels.

    Returns
    -------
    go.Figure
        Histogram figure with optional overlaid histogram and vertical guide lines.
    """
    histogram_values = np.asarray(values, dtype=float)
    histogram_values = histogram_values[np.isfinite(histogram_values)]

    overlay_histogram_values = None
    if overlay_values is not None:
        overlay_histogram_values = np.asarray(overlay_values, dtype=float)
        overlay_histogram_values = overlay_histogram_values[
            np.isfinite(overlay_histogram_values)
        ]

    figure = go.Figure()

    figure.add_trace(
        go.Histogram(
            x=histogram_values,
            nbinsx=int(nbins),
            name=str(base_name),
            opacity=0.55 if overlay_histogram_values is not None else 1.0,
            bingroup="hist",
        )
    )

    if overlay_histogram_values is not None:
        figure.add_trace(
            go.Histogram(
                x=overlay_histogram_values,
                nbinsx=int(nbins),
                name=str(overlay_name),
                opacity=0.85,
                bingroup="hist",
            )
        )

    add_vertical_lines(
        fig=figure,
        line_positions=line_positions,
        line_labels=line_labels,
        line_width=float(line_width),
        line_dash=str(line_dash),
        font_size=float(font_size),
    )

    figure.update_layout(
        title={
            "text": "" if title is None else str(title),
            "font": {"size": float(font_size)},
        },
        xaxis_title=xaxis_title,
        yaxis_title="Count",
        bargap=0.0,
        showlegend=(overlay_histogram_values is not None),
        separators=".,",
        barmode="overlay",
        hovermode="x unified",
        font={"size": float(font_size)},
        legend={"font": {"size": float(font_size)}},
        xaxis={
            "showspikes": True,
            "spikemode": "across",
            "spikesnap": "cursor",
            "title": {"font": {"size": float(font_size)}},
            "tickfont": {"size": float(tick_size)},
        },
        yaxis={
            "title": {"font": {"size": float(font_size)}},
            "tickfont": {"size": float(tick_size)},
        },
    )

    return figure


def add_vertical_lines(
    *,
    fig: go.Figure,
    line_positions: list[float],
    line_labels: Optional[list[str]] = None,
    line_width: float = 2.0,
    line_dash: str = "dash",
    annotation_y: float = 1.02,
    font_size: float = 14.0,
) -> go.Figure:
    """
    Add vertical lines and optional labels to an existing Plotly figure.

    Notes
    -----
    Uses yref="paper" so each line spans the full plot height.
    Safe to call repeatedly because it only appends shapes and annotations.

    Parameters
    ----------
    fig : go.Figure
        Existing figure to modify.
    line_positions : list[float]
        X positions of vertical lines to add.
    line_labels : Optional[list[str]]
        Optional labels for each line. If fewer labels than positions,
        remaining labels are treated as empty.
    line_width : float
        Width of the vertical lines.
    line_dash : str
        Dash style for the vertical lines.
    annotation_y : float
        Y position in paper coordinates for the line labels.
    font_size : float
        Font size used for the line annotations.

    Returns
    -------
    go.Figure
        The same figure instance with new lines and annotations added.
    """
    resolved_line_labels = list(line_labels) if line_labels is not None else []

    if len(resolved_line_labels) < len(line_positions):
        resolved_line_labels = resolved_line_labels + [""] * (
            len(line_positions) - len(resolved_line_labels)
        )

    for x_position, line_label in zip(line_positions, resolved_line_labels):
        try:
            x_position_value = float(x_position)
        except Exception:
            continue

        if not np.isfinite(x_position_value):
            continue

        fig.add_shape(
            type="line",
            x0=x_position_value,
            x1=x_position_value,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line={"width": float(line_width), "dash": str(line_dash)},
        )

        line_label_text = str(line_label).strip()
        if line_label_text:
            fig.add_annotation(
                x=x_position_value,
                y=float(annotation_y),
                xref="x",
                yref="paper",
                text=line_label_text,
                showarrow=False,
                textangle=-45,
                xanchor="left",
                yanchor="bottom",
                align="left",
                bgcolor="rgba(255,255,255,0.6)",
                font={"size": float(font_size)},
            )

    return fig


def _make_info_figure(
    message: str,
    *,
    font_size: float = 14.0,
) -> go.Figure:
    """
    Build a simple informational figure containing only a centered message.
    """
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "family": styling.CHART_STYLE["font_family"],
            "size": float(font_size),
        },
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        separators=".,",
        font={
            "family": styling.CHART_STYLE["font_family"],
            "size": float(font_size),
        },
    )
    return figure


def resolve_runtime_visualization_settings(
    runtime_config: RuntimeConfig,
) -> dict[str, float | bool | str]:
    """
    Resolve shared visualization settings from a runtime profile.
    """
    return {
        "default_marker_size": runtime_config.get_float(
            "visualization.default_marker_size",
            default=8.0,
        ),
        "default_marker_opacity": runtime_config.get_float(
            "visualization.default_marker_opacity",
            default=0.72,
        ),
        "default_line_width": runtime_config.get_float(
            "visualization.default_line_width",
            default=2.0,
        ),
        "default_font_size": runtime_config.get_float(
            "visualization.default_font_size",
            default=14.0,
        ),
        "default_tick_size": runtime_config.get_float(
            "visualization.default_tick_size",
            default=12.0,
        ),
        "show_grid": runtime_config.get_bool(
            "visualization.show_grid_by_default",
            default=True,
        ),
        "legend_vertical_anchor": runtime_config.get_str(
            "visualization.legend_vertical_anchor",
            default="bottom",
        ),
        "annotation_text_position": runtime_config.get_str(
            "visualization.annotation_text_position",
            default="top center",
        ),
    }


def apply_calibration_chart_style(
    fig: go.Figure,
    *,
    marker_size: float,
    marker_opacity: float,
    line_width: float,
    font_size: float,
    tick_size: float,
    show_grid: bool,
    legend_vertical_anchor: str,
    annotation_text_position: str,
    margin: dict[str, float | int],
    clear_title_text: bool = False,
) -> go.Figure:
    """
    Apply a consistent style for fluorescence/scattering calibration charts.
    """
    resolved_legend_vertical_anchor = str(legend_vertical_anchor).strip().lower()
    if resolved_legend_vertical_anchor not in {"top", "bottom"}:
        resolved_legend_vertical_anchor = "bottom"

    resolved_annotation_text_position = str(annotation_text_position).strip().lower()
    valid_annotation_positions = {
        "top left",
        "top center",
        "top right",
        "middle left",
        "middle center",
        "middle right",
        "bottom left",
        "bottom center",
        "bottom right",
    }
    if resolved_annotation_text_position not in valid_annotation_positions:
        resolved_annotation_text_position = "top center"

    legend_y = 0.98 if resolved_legend_vertical_anchor == "top" else 0.02
    marker_line_width = max(0.8, float(line_width) * 0.35)

    layout_kwargs: dict[str, Any] = {
        "autosize": True,
        "height": None,
        "margin": dict(margin),
        "font": {
            "family": styling.CHART_STYLE["font_family"],
            "size": float(font_size),
        },
        "legend": {
            "x": styling.CHART_STYLE["legend"]["x"],
            "y": legend_y,
            "xanchor": styling.CHART_STYLE["legend"]["xanchor"],
            "yanchor": resolved_legend_vertical_anchor,
            "bgcolor": styling.CHART_STYLE["legend"]["bgcolor"],
            "bordercolor": styling.CHART_STYLE["legend"]["bordercolor"],
            "borderwidth": styling.CHART_STYLE["legend"]["borderwidth"],
            "font": {
                "size": float(tick_size),
            },
        },
    }

    if clear_title_text:
        layout_kwargs["title"] = {"text": ""}

    fig.update_layout(**layout_kwargs)

    fig.update_xaxes(
        automargin=False,
        title_standoff=10,
        showgrid=bool(show_grid),
        gridcolor=styling.CHART_STYLE["grid_color"],
        gridwidth=styling.CHART_STYLE["grid_width"],
        zeroline=False,
        title_font={"size": float(font_size)},
        tickfont={"size": float(tick_size)},
    )
    fig.update_yaxes(
        automargin=False,
        title_standoff=10,
        showgrid=bool(show_grid),
        gridcolor=styling.CHART_STYLE["grid_color"],
        gridwidth=styling.CHART_STYLE["grid_width"],
        zeroline=False,
        title_font={"size": float(font_size)},
        tickfont={"size": float(tick_size)},
    )

    for trace in fig.data:
        marker = getattr(trace, "marker", None)
        if marker is not None:
            try:
                marker.size = float(marker_size)
                marker.opacity = float(marker_opacity)
                marker.symbol = styling.CHART_STYLE["marker_symbol"]
                marker.line = {
                    "width": marker_line_width,
                    "color": styling.CHART_STYLE["marker_line_color"],
                }
            except (AttributeError, TypeError, ValueError):
                logger.debug(
                    "Could not apply marker defaults to trace_type=%s",
                    type(trace).__name__,
                    exc_info=True,
                )

        line = getattr(trace, "line", None)
        if line is not None:
            try:
                line.width = float(line_width)
            except (AttributeError, TypeError, ValueError):
                logger.debug(
                    "Could not apply line defaults to trace_type=%s",
                    type(trace).__name__,
                    exc_info=True,
                )

        if hasattr(trace, "textposition") and getattr(trace, "text", None) is not None:
            try:
                trace.textposition = resolved_annotation_text_position
            except (AttributeError, TypeError, ValueError):
                logger.debug(
                    "Could not apply textposition to trace_type=%s",
                    type(trace).__name__,
                    exc_info=True,
                )

    if fig.layout.annotations:
        updated_annotations = []
        for annotation in fig.layout.annotations:
            annotation_json = annotation.to_plotly_json()
            annotation_font = dict(annotation_json.get("font", {}))
            annotation_font["size"] = float(font_size)
            annotation_font["family"] = styling.CHART_STYLE["font_family"]
            annotation_json["font"] = annotation_font
            annotation_json.setdefault(
                "bgcolor",
                styling.CHART_STYLE["annotation"]["bgcolor"],
            )
            annotation_json.setdefault(
                "bordercolor",
                styling.CHART_STYLE["annotation"]["bordercolor"],
            )
            annotation_json.setdefault(
                "borderwidth",
                styling.CHART_STYLE["annotation"]["borderwidth"],
            )
            annotation_json.setdefault(
                "borderpad",
                styling.CHART_STYLE["annotation"]["borderpad"],
            )
            updated_annotations.append(annotation_json)
        fig.update_layout(annotations=updated_annotations)

    return fig


def apply_default_visual_style(
    fig: go.Figure,
    *,
    marker_size: float = 8.0,
    line_width: float = 2.0,
    font_size: float = 14.0,
    tick_size: float = 12.0,
    show_grid: bool = True,
) -> go.Figure:
    """
    Apply a default visual style to traces, axes, layout shapes, and annotations.

    Parameters
    ----------
    fig : go.Figure
        Figure to style.
    marker_size : float
        Default marker size for traces exposing markers.
    line_width : float
        Default line width for traces and vertical line shapes.
    font_size : float
        Font size for titles, legend, annotations, and general labels.
    tick_size : float
        Font size for axis tick labels.
    show_grid : bool
        Whether axis grids should be shown.

    Returns
    -------
    go.Figure
        The same figure instance after styling.
    """
    resolved_marker_size = float(marker_size)
    resolved_line_width = float(line_width)
    resolved_font_size = float(font_size)
    resolved_tick_size = float(tick_size)
    marker_line_width = max(0.8, resolved_line_width * 0.35)

    for trace in fig.data:
        marker = getattr(trace, "marker", None)
        if marker is not None:
            try:
                marker.size = resolved_marker_size
                marker.symbol = styling.CHART_STYLE["marker_symbol"]
                marker.line = {
                    "width": marker_line_width,
                    "color": styling.CHART_STYLE["marker_line_color"],
                }
            except (AttributeError, TypeError, ValueError):
                logger.debug(
                    "Could not apply marker size to trace_type=%s",
                    type(trace).__name__,
                    exc_info=True,
                )

        line = getattr(trace, "line", None)
        if line is not None:
            try:
                line.width = resolved_line_width
            except (AttributeError, TypeError, ValueError):
                logger.debug(
                    "Could not apply line width to trace_type=%s",
                    type(trace).__name__,
                    exc_info=True,
                )

    if fig.layout.shapes:
        updated_shapes = []
        for shape in fig.layout.shapes:
            shape_json = shape.to_plotly_json()
            shape_line = dict(shape_json.get("line", {}))
            shape_line["width"] = resolved_line_width
            shape_json["line"] = shape_line
            updated_shapes.append(shape_json)

        fig.update_layout(shapes=updated_shapes)

    if fig.layout.annotations:
        updated_annotations = []
        for annotation in fig.layout.annotations:
            annotation_json = annotation.to_plotly_json()
            annotation_font = dict(annotation_json.get("font", {}))
            annotation_font["size"] = resolved_font_size
            annotation_font["family"] = styling.CHART_STYLE["font_family"]
            annotation_json["font"] = annotation_font
            annotation_json.setdefault(
                "bgcolor",
                styling.CHART_STYLE["annotation"]["bgcolor"],
            )
            annotation_json.setdefault(
                "bordercolor",
                styling.CHART_STYLE["annotation"]["bordercolor"],
            )
            annotation_json.setdefault(
                "borderwidth",
                styling.CHART_STYLE["annotation"]["borderwidth"],
            )
            annotation_json.setdefault(
                "borderpad",
                styling.CHART_STYLE["annotation"]["borderpad"],
            )
            updated_annotations.append(annotation_json)

        fig.update_layout(annotations=updated_annotations)

    current_title_text = ""
    if (
        fig.layout.title is not None
        and getattr(fig.layout.title, "text", None) is not None
    ):
        current_title_text = fig.layout.title.text

    fig.update_layout(
        font={
            "size": resolved_font_size,
            "family": styling.CHART_STYLE["font_family"],
        },
        legend={
            **styling.CHART_STYLE["legend"],
            "font": {"size": resolved_font_size},
        },
        title={"text": current_title_text, "font": {"size": resolved_font_size}},
    )

    fig.update_xaxes(
        showgrid=bool(show_grid),
        gridcolor=styling.CHART_STYLE["grid_color"],
        gridwidth=styling.CHART_STYLE["grid_width"],
        zeroline=False,
        title_font={"size": resolved_font_size},
        tickfont={"size": resolved_tick_size},
    )
    fig.update_yaxes(
        showgrid=bool(show_grid),
        gridcolor=styling.CHART_STYLE["grid_color"],
        gridwidth=styling.CHART_STYLE["grid_width"],
        zeroline=False,
        title_font={"size": resolved_font_size},
        tickfont={"size": resolved_tick_size},
    )

    return fig
