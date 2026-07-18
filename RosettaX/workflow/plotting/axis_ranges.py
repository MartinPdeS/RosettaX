# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np
import plotly.graph_objs as go


def compute_stable_axis_range(
    *,
    values: Any,
    log_scale: bool,
) -> Optional[list[float]]:
    """Compute a robust Plotly axis range from finite event data values."""
    value_array = np.asarray(values, dtype=float)
    value_array = value_array[np.isfinite(value_array)]

    if log_scale:
        value_array = value_array[value_array > 0.0]

    if value_array.size < 2:
        return None

    lower_value, upper_value = np.quantile(value_array, [0.001, 0.999])

    if not np.isfinite(lower_value) or not np.isfinite(upper_value):
        return None

    if lower_value == upper_value:
        span = abs(lower_value) * 0.05 or 1.0
        lower_value -= span
        upper_value += span

    if log_scale:
        lower_value = max(lower_value, np.nextafter(0.0, 1.0))
        upper_value = max(upper_value, lower_value * 1.01)
        return [
            float(np.log10(lower_value)),
            float(np.log10(upper_value)),
        ]

    padding = 0.05 * float(upper_value - lower_value)
    return [
        float(lower_value - padding),
        float(upper_value + padding),
    ]


def apply_stable_2d_axis_ranges(
    *,
    figure: go.Figure,
    x_values: Any,
    y_values: Any,
    x_log_scale: bool,
    y_log_scale: bool,
) -> go.Figure:
    """Apply stable data-driven ranges without letting overlays affect them."""
    x_range = compute_stable_axis_range(values=x_values, log_scale=x_log_scale)
    y_range = compute_stable_axis_range(values=y_values, log_scale=y_log_scale)

    if x_range is not None:
        figure.update_xaxes(autorange=False, range=x_range)

    if y_range is not None:
        figure.update_yaxes(autorange=False, range=y_range)

    return figure
