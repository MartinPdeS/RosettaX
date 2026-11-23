
import numpy as np
import plotly.graph_objs as go
from typing import Any

ROSETTA_BASELINE_GATE_COLOR = "#f43f5e"
ROSETTA_PEAK_MARKER_STYLES = {
    "marker": {"symbol": "diamond", "color": "#7c3aed"},
    "non_fluorescent": {"symbol": "circle", "color": "#008c80"},
    "excluded": {"symbol": "x", "color": "#b45309"},
}


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
) -> go.Figure:
    """Add angled labels that start at the top of their scatter guides.

    Parameters
    ----------
    figure : go.Figure
        Scatter figure with its primary x-axis scale configured.
    annotation_entries : list of dict
        Guide positions in detector units, with labels and peak kinds.

    Returns
    -------
    go.Figure
        Updated figure. The browser adjusts label spacing after rendering.
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
        if kind in ("excluded", "guard_cutoff"):
            continue
        is_marker = kind == "marker"
        label = entry["label"]
        color = ROSETTA_PEAK_MARKER_STYLES.get(kind, {}).get("color", "#0f6b3d")

        figure.add_annotation(
            name="rosetta-size-guide",
            x=float(resolved_x_value),
            y=1,
            xref="x",
            yref="paper",
            text=label,
            hovertext=f"{label} fluorescent marker" if is_marker else label,
            textangle=-45,
            xanchor="left",
            yanchor="bottom",
            font={"size": 13, "color": color},
            borderpad=0,
            showarrow=True,
            arrowhead=0,
            arrowcolor=color,
            arrowwidth=1,
            ax=0,
            ay=-4,
        )

    return figure
