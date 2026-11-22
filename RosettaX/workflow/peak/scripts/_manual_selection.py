"""Read click positions and selection bounds for manual peak picking."""

import math
from typing import Any


def read_clicked_position(*, payload: Any, axes: tuple[str, ...]) -> dict[str, float] | None:
    """Return the first Plotly click's finite coordinates for every requested axis."""
    points = payload.get("points") if isinstance(payload, dict) else None
    return _read_point(point=points[0], axes=axes) if isinstance(points, list) and points else None


def read_selected_ranges(*, payload: Any, axes: tuple[str, ...]) -> dict[str, tuple[float, float]] | None:
    """Read a Plotly selection rectangle or the bounds of its complete selected points."""
    if not isinstance(payload, dict):
        return None

    ranges = payload.get("range")
    if isinstance(ranges, dict) and all(
        isinstance(ranges.get(axis), (list, tuple)) and len(ranges[axis]) >= 2 for axis in axes
    ):
        try:
            bounds = {axis: (float(ranges[axis][0]), float(ranges[axis][1])) for axis in axes}
        except (TypeError, ValueError, OverflowError):
            return None
        if all(math.isfinite(bound) for pair in bounds.values() for bound in pair):
            return {axis: (min(pair), max(pair)) for axis, pair in bounds.items()}

    points = payload.get("points")
    if not isinstance(points, list):
        return None
    positions = [position for point in points if (position := _read_point(point=point, axes=axes)) is not None]
    if not positions:
        return None
    return {
        axis: (min(position[axis] for position in positions), max(position[axis] for position in positions))
        for axis in axes
    }


def _read_point(*, point: Any, axes: tuple[str, ...]) -> dict[str, float] | None:
    """Read a point only when every requested coordinate is finite."""
    if not isinstance(point, dict):
        return None
    try:
        coordinates = {axis: float(point[axis]) for axis in axes}
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    return coordinates if all(math.isfinite(value) for value in coordinates.values()) else None
