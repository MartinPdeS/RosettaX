# -*- coding: utf-8 -*-

from typing import Any

import numpy as np


def finite_plot_values(
    values: Any,
    *,
    positive_only: bool = False,
) -> np.ndarray:
    """Return finite numeric plot values, optionally restricted to positives."""
    resolved_values = np.asarray(values, dtype=float).reshape(-1)
    resolved_values = resolved_values[np.isfinite(resolved_values)]

    if positive_only:
        resolved_values = resolved_values[resolved_values > 0.0]

    return resolved_values


def build_histogram_arrays(
    values: Any,
    *,
    bin_count: int,
    log_x: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build histogram counts, edges, and centers for a plot."""
    resolved_values = finite_plot_values(values, positive_only=log_x)
    if resolved_values.size == 0:
        message = (
            "No positive signal values available for logarithmic histogram bins."
            if log_x
            else "No finite signal values available to build histogram."
        )
        raise ValueError(message)

    if log_x:
        lower_edge = float(np.min(resolved_values))
        upper_edge = float(np.max(resolved_values))
        if lower_edge == upper_edge:
            upper_edge = lower_edge * 1.01
        edges = np.geomspace(lower_edge, upper_edge, num=int(bin_count) + 1)
        counts, edges = np.histogram(resolved_values, bins=edges)
        centers = np.sqrt(edges[:-1] * edges[1:])
    else:
        counts, edges = np.histogram(resolved_values, bins=int(bin_count))
        centers = 0.5 * (edges[:-1] + edges[1:])

    return (
        np.asarray(counts, dtype=float),
        np.asarray(edges, dtype=float),
        np.asarray(centers, dtype=float),
    )


def smooth_histogram_counts(
    histogram_counts: Any,
    *,
    sigma_points: Any = 2.0,
) -> np.ndarray:
    """Apply Gaussian smoothing in histogram-bin space."""
    counts = np.asarray(histogram_counts, dtype=float).reshape(-1)
    if counts.size < 3:
        return counts

    try:
        resolved_sigma = max(float(sigma_points), 0.0)
    except (TypeError, ValueError):
        resolved_sigma = 2.0

    if resolved_sigma <= 0.0:
        return counts

    radius = max(1, int(np.ceil(3.0 * resolved_sigma)))
    offsets = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * np.square(offsets / resolved_sigma))
    kernel /= np.sum(kernel)

    padded_counts = np.pad(counts, radius, mode="edge")
    return np.convolve(padded_counts, kernel, mode="valid")
