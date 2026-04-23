# -*- coding: utf-8 -*-

from typing import Optional

import numpy as np
import plotly.graph_objs as go


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
        overlay_histogram_values = overlay_histogram_values[np.isfinite(overlay_histogram_values)]

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
        bargap=0.02,
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
        font={"size": float(font_size)},
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        separators=".,",
        font={"size": float(font_size)},
    )
    return figure


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

    for trace in fig.data:
        marker = getattr(trace, "marker", None)
        if marker is not None:
            try:
                marker.size = resolved_marker_size
            except Exception:
                pass

        line = getattr(trace, "line", None)
        if line is not None:
            try:
                line.width = resolved_line_width
            except Exception:
                pass

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
            annotation_json["font"] = annotation_font
            updated_annotations.append(annotation_json)

        fig.update_layout(annotations=updated_annotations)

    current_title_text = ""
    if fig.layout.title is not None and getattr(fig.layout.title, "text", None) is not None:
        current_title_text = fig.layout.title.text

    fig.update_layout(
        font={"size": resolved_font_size},
        legend={"font": {"size": resolved_font_size}},
        title={"text": current_title_text, "font": {"size": resolved_font_size}},
    )

    fig.update_xaxes(
        showgrid=bool(show_grid),
        title_font={"size": resolved_font_size},
        tickfont={"size": resolved_tick_size},
    )
    fig.update_yaxes(
        showgrid=bool(show_grid),
        title_font={"size": resolved_font_size},
        tickfont={"size": resolved_tick_size},
    )

    return fig