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
        Optional second set of values to overlay as a second histogram (e.g. gated events).
    base_name : str
        Legend name for the main histogram.
    overlay_name : str
        Legend name for the overlay histogram.
    title : Optional[str]
        Optional title for the figure.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    overlay = None
    if overlay_values is not None:
        overlay = np.asarray(overlay_values, dtype=float)
        overlay = overlay[np.isfinite(overlay)]

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=int(nbins),
            name=str(base_name),
            opacity=0.55 if overlay is not None else 1.0,
            bingroup="hist",
        )
    )

    if overlay is not None:
        fig.add_trace(
            go.Histogram(
                x=overlay,
                nbinsx=int(nbins),
                name=str(overlay_name),
                opacity=0.85,
                bingroup="hist",
            )
        )

    for x, label in zip(line_positions, line_labels):
        try:
            xv = float(x)
        except Exception:
            continue
        if not np.isfinite(xv):
            continue

        fig.add_shape(
            type="line",
            x0=xv,
            x1=xv,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line={"width": 2, "dash": "dash"},
        )

        fig.add_annotation(
            x=xv,
            y=1.02,
            xref="x",
            yref="paper",
            text=str(label),
            showarrow=False,
            textangle=-45,
            xanchor="left",
            yanchor="bottom",
            align="left",
            bgcolor="rgba(255,255,255,0.6)",
        )

    fig.update_layout(
        title="" if title is None else str(title),
        xaxis_title=xaxis_title,
        yaxis_title="Count",
        bargap=0.02,
        showlegend=(overlay is not None),
        separators=".,",
        barmode="overlay",
        hovermode="x unified",
        xaxis={"showspikes": True, "spikemode": "across", "spikesnap": "cursor"},
    )

    return fig


def add_vertical_lines(
    *,
    fig: go.Figure,
    line_positions: list[float],
    line_labels: Optional[list[str]] = None,
    line_width: int = 2,
    line_dash: str = "dash",
    annotation_y: float = 1.02,
) -> go.Figure:
    """
    Adds vertical lines (and optional labels) to an existing Plotly figure.

    Notes
    - Uses yref="paper" so the line spans the full plot height.
    - Safe to call repeatedly: it only appends new shapes/annotations.

    Parameters
    ----------
    fig : go.Figure
        Existing figure to add lines to.
    line_positions : list[float]
        X positions of vertical lines to add.
    line_labels : Optional[list[str]]
        Optional labels for each line. If fewer labels than positions, remaining will be empty.
    line_width : int
        Width of the vertical lines.
    line_dash : str
        Dash style for the vertical lines (e.g. "dash", "dot", "solid").
    annotation_y : float
        Y position in paper coordinates for the line labels.

    Returns
    -------
    go.Figure
        The same figure instance with new lines and annotations added.
    """
    if line_labels is None:
        line_labels = []

    # Pad labels to match positions
    if len(line_labels) < len(line_positions):
        line_labels = list(line_labels) + [""] * (len(line_positions) - len(line_labels))

    for x, label in zip(line_positions, line_labels):
        try:
            xv = float(x)
        except Exception:
            continue
        if not np.isfinite(xv):
            continue

        fig.add_shape(
            type="line",
            x0=xv,
            x1=xv,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line={"width": int(line_width), "dash": str(line_dash)},
        )

        label_str = str(label).strip()
        if label_str:
            fig.add_annotation(
                x=xv,
                y=float(annotation_y),
                xref="x",
                yref="paper",
                text=label_str,
                showarrow=False,
                textangle=-45,
                xanchor="left",
                yanchor="bottom",
                align="left",
                bgcolor="rgba(255,255,255,0.6)",
            )

    return fig