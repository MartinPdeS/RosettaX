# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np
import plotly.graph_objs as go


ROSETTA_SCATTER_LABEL_AXIS_POSITION = 0.90


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
) -> Optional[float]:
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

        figure.add_annotation(
            x=float(resolved_x_value),
            y=float(ROSETTA_SCATTER_LABEL_AXIS_POSITION),
            xref="x",
            yref="paper",
            text=str(entry["label"]),
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            xshift=8,
            font={
                "size": 20,
                "color": "#0f6b3d",
            },
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#1f9d55",
            borderwidth=1,
            borderpad=2,
        )

    return figure
