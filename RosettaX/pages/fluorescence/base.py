from typing import Any, Optional

import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.pages.fluorescence.helper import (
    FileStateRefresher,
    FluorescentCalibrationIds,
    FluorescentCalibrationService,
)

class SectionContext:
    def __init__(
        self,
        *,
        ids: FluorescentCalibrationIds,
        service: FluorescentCalibrationService,
        file_state: FileStateRefresher,
        bead_table_columns: list[dict[str, Any]],
        default_bead_rows: list[dict[str, Any]],
        card_body_scroll: dict[str, Any],
        graph_style: dict[str, Any],
    ) -> None:
        self.ids = ids
        self.service = service
        self.file_state = file_state
        self.bead_table_columns = bead_table_columns
        self.default_bead_rows = default_bead_rows
        self.card_body_scroll = card_body_scroll
        self.graph_style = graph_style


class BaseSection:
    def __init__(self, *, context: SectionContext) -> None:
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
