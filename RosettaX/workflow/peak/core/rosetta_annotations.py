
import numpy as np
import plotly.graph_objs as go
from typing import Any

ROSETTA_SCATTER_LABEL_AXIS_POSITION = 0.90
ROSETTA_PEAK_MARKER_STYLES = {
    "marker": {"symbol": "diamond", "color": "#7c3aed"},
    "non_fluorescent": {"symbol": "circle", "color": "#008c80"},
}


def include_rosetta_peak_markers_in_view(*, figure: go.Figure, peak_lines_payload: Any) -> None:
    """Keep detected peak centers inside the initial axis ranges with padding."""
    if not isinstance(peak_lines_payload, dict):
        return
    points = peak_lines_payload.get("points")
    if not isinstance(points, list):
        return
    for axis_name, coordinate in (("xaxis", "x"), ("yaxis", "y")):
        axis = getattr(figure.layout, axis_name)
        if not axis.range or len(axis.range) != 2:
            continue
        lower, upper = map(float, axis.range)
        if upper <= lower:
            continue
        values = []
        for point in points:
            if not isinstance(point, dict) or point.get("kind") not in ROSETTA_PEAK_MARKER_STYLES:
                continue
            try:
                value = float(point[coordinate])
            except (KeyError, TypeError, ValueError):
                continue
            if not np.isfinite(value) or (axis.type == "log" and value <= 0):
                continue
            values.append(float(np.log10(value)) if axis.type == "log" else value)
        if values:
            padding = (upper - lower) * 0.04
            axis.range = [min(lower, min(values) - padding), max(upper, max(values) + padding)]


def extract_rosetta_scatter_guide_annotations(
    *,
    peak_lines_payload: Any,
) -> list[dict[str, Any]]:
    """
    Extract Rosetta scatter guide annotation entries from a payload.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    raw_entries = peak_lines_payload.get(
        "scatter_guide_annotations",
    )

    if not isinstance(raw_entries, list):
        return []

    resolved_entries: list[dict[str, Any]] = []

    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue

        try:
            x_value = float(raw_entry.get("x"))
        except (TypeError, ValueError):
            continue

        if not np.isfinite(x_value):
            continue

        label = str(raw_entry.get("label") or "").strip()

        if not label:
            continue

        resolved_entries.append(
            {
                "x": float(x_value),
                "label": label,
                "kind": str(raw_entry.get("kind") or ""),
            }
        )

    return resolved_entries


def x_axis_is_log(
    *,
    figure: go.Figure,
) -> bool:
    """
    Return whether the primary x-axis of a figure uses a logarithmic scale.
    """
    x_axis_type = getattr(
        figure.layout.xaxis,
        "type",
        None,
    )

    return str(x_axis_type or "").strip().lower() == "log"


def resolve_annotation_x_value(
    *,
    x_value: float,
    x_axis_is_log_scale: bool,
) -> float | None:
    """
    Resolve one annotation x value for the current x-axis scale.
    """
    if not x_axis_is_log_scale:
        return float(x_value)

    if x_value <= 0.0:
        return None

    return float(np.log10(x_value))


def add_rosetta_scatter_guide_annotations(
    *,
    figure: go.Figure,
    annotation_entries: list[dict[str, Any]],
    baseline_gate: float | None = None,
) -> go.Figure:
    """
    Add Rosetta size labels beside scatter guide lines.
    """
    x_axis_is_log_scale = x_axis_is_log(
        figure=figure,
    )

    for entry in annotation_entries:
        resolved_x_value = resolve_annotation_x_value(
            x_value=float(entry["x"]),
            x_axis_is_log_scale=x_axis_is_log_scale,
        )

        if resolved_x_value is None:
            continue

        kind = entry.get("kind")
        is_marker = kind == "marker"
        is_non_fluorescent = kind == "non_fluorescent"
        gate_is_log = str(figure.layout.yaxis.type or "").lower() == "log"
        use_gate = is_non_fluorescent and baseline_gate is not None and (not gate_is_log or baseline_gate > 0)
        gate_y = float(np.log10(baseline_gate)) if use_gate and gate_is_log else baseline_gate
        color = "#7c3aed" if is_marker else ("#008c80" if is_non_fluorescent else "#0f6b3d")

        x_range = figure.layout.xaxis.range
        x_anchor = "center" if kind else "left"
        if kind and x_range and len(x_range) == 2:
            x_span = float(x_range[1]) - float(x_range[0])
            if x_span > 0 and resolved_x_value > float(x_range[1]) - 0.06 * x_span:
                x_anchor = "right"
            elif x_span > 0 and resolved_x_value < float(x_range[0]) + 0.06 * x_span:
                x_anchor = "left"

        figure.add_annotation(
            x=float(resolved_x_value),
            y=gate_y if use_gate else (1.01 if is_marker else float(ROSETTA_SCATTER_LABEL_AXIS_POSITION)),
            xref="x",
            yref="y" if use_gate else "paper",
            text=f'{entry["label"]} marker' if is_marker else str(entry["label"]),
            showarrow=False,
            xanchor=x_anchor,
            yanchor="bottom" if use_gate or is_marker else "middle",
            xshift=0 if kind else 8,
            yshift=8 if use_gate else 0,
            font={
                "size": 17 if kind else 20,
                "color": color,
            },
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=color,
            borderwidth=1,
            borderpad=2,
        )

    return figure
