"""Peak graph payload."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from .graph_interaction import (
    unique_finite_preserving_order,
)

if TYPE_CHECKING:
    from .graphing import PeakWorkflowGraphBuilder

logger = logging.getLogger(__name__)


def extract_x_axis_lower_gate_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> float | None:
    """
    Extract the x axis lower gate threshold from the peak line payload.
    """
    return extract_first_finite_float_from_peak_payload(
        builder,
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
        ),
    )


def extract_x_axis_upper_gate_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> float | None:
    """
    Extract the x axis upper gate threshold from the peak line payload.
    """
    return extract_first_finite_float_from_peak_payload(
        builder,
        keys=(
            "x_axis_upper_gate",
            "x_upper_gate",
            "x_upper_gate_threshold",
        ),
    )


def extract_y_axis_lower_gate_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> float | None:
    """
    Extract the y axis lower gate threshold from the peak line payload.
    """
    return extract_first_finite_float_from_peak_payload(
        builder,
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
        ),
    )


def extract_y_axis_upper_gate_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> float | None:
    """
    Extract the y axis upper gate threshold from the peak line payload.
    """
    return extract_first_finite_float_from_peak_payload(
        builder,
        keys=(
            "y_axis_upper_gate",
            "y_upper_gate",
            "y_upper_gate_threshold",
        ),
    )


def extract_first_finite_float_from_peak_payload(
    builder: PeakWorkflowGraphBuilder,
    *,
    keys: tuple[str, ...],
) -> float | None:
    """
    Extract the first finite float value matching one of the provided keys.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return None

    for key in keys:
        value = builder.peak_lines_payload.get(
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


def extract_x_positions_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> list[float]:
    """
    Extract x positions from a peak line payload.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return []

    candidate_values = (
        builder.peak_lines_payload.get(
            "x_positions",
        )
        or builder.peak_lines_payload.get(
            "positions",
        )
        or []
    )

    if not candidate_values and isinstance(
        builder.peak_lines_payload.get(
            "points",
        ),
        list,
    ):
        candidate_values = [
            point.get(
                "x",
            )
            for point in builder.peak_lines_payload["points"]
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


def extract_points_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
) -> list[dict[str, float]]:
    """
    Extract two dimensional points from a peak line payload.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return []

    points = builder.peak_lines_payload.get(
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

    x_positions = (
        builder.peak_lines_payload.get(
            "x_positions",
        )
        or []
    )

    y_positions = (
        builder.peak_lines_payload.get(
            "y_positions",
        )
        or []
    )

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


def extract_labels_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
    *,
    point_count: int,
) -> list[str]:
    """
    Extract peak labels from a peak line payload.
    """
    if isinstance(builder.peak_lines_payload, dict):
        labels = builder.peak_lines_payload.get(
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


def extract_numeric_list_from_peak_lines_payload(
    builder: PeakWorkflowGraphBuilder,
    *,
    key: str,
) -> list[float]:
    """
    Extract one finite unique float list from the peak payload.
    """
    if not isinstance(builder.peak_lines_payload, dict):
        return []

    raw_values = builder.peak_lines_payload.get(
        key,
    )

    if not isinstance(raw_values, list):
        return []

    return unique_finite_preserving_order(
        raw_values,
    )
