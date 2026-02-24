from typing import Any, Optional

import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go


class BaseSection:
    def __init__(self, *, context: object) -> None:
        self.context = context

    def layout(self) -> dbc.Card:
        raise NotImplementedError

    def register_callbacks(self) -> None:
        return

    @staticmethod
    def _empty_fig() -> go.Figure:
        fig = go.Figure()
        fig.update_layout(separators=".,")
        return fig

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            v = float(value)
            return v if np.isfinite(v) else None

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            s = s.replace(",", ".")
            try:
                v = float(s)
            except ValueError:
                return None
            return v if np.isfinite(v) else None

        return None

    @staticmethod
    def _as_int(value: Any, default: int, min_value: int, max_value: int) -> int:
        try:
            v = int(value)
        except Exception:
            v = default

        if v < min_value:
            v = min_value
        if v > max_value:
            v = max_value

        return v
