# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np


def apply_stable_2d_axis_ranges(
    *,
    figure: Any,
    x_values: Any,
    y_values: Any,
    x_log_scale: bool,
    y_log_scale: bool,
) -> Any:
    """
    Clamp 2D scatter plot ranges using only finite data values.

    Peak markers, clicked annotations, and helper traces must not define the
    displayed range.
    """
    x_range = compute_stable_axis_range(
        values=x_values,
        log_scale=x_log_scale,
    )

    y_range = compute_stable_axis_range(
        values=y_values,
        log_scale=y_log_scale,
    )

    if x_range is not None:
        figure.update_xaxes(
            autorange=False,
            range=x_range,
        )

    if y_range is not None:
        figure.update_yaxes(
            autorange=False,
            range=y_range,
        )

    return figure


def compute_stable_axis_range(
    *,
    values: Any,
    log_scale: bool,
) -> Optional[list[float]]:
    """
    Compute a robust Plotly axis range.

    For log axes, Plotly expects log10 range values.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if log_scale:
        values = values[
            values > 0.0
        ]

    if values.size < 2:
        return None

    lower_value, upper_value = np.quantile(
        values,
        [
            0.001,
            0.999,
        ],
    )

    if not np.isfinite(lower_value) or not np.isfinite(upper_value):
        return None

    if lower_value == upper_value:
        span = abs(lower_value) * 0.05

        if span == 0.0:
            span = 1.0

        lower_value -= span
        upper_value += span

    if log_scale:
        lower_value = max(
            lower_value,
            np.nextafter(0.0, 1.0),
        )

        return [
            float(np.log10(lower_value)),
            float(np.log10(upper_value)),
        ]

    padding = 0.05 * float(upper_value - lower_value)

    return [
        float(lower_value - padding),
        float(upper_value + padding),
    ]