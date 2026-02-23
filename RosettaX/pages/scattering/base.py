from typing import Any

from dash import html
import dash_bootstrap_components as dbc

from RosettaX.pages.scattering.helper import ScatterCalibrationIds


class SectionContext:
    def __init__(
        self,
        *,
        ids: ScatterCalibrationIds,
        scroll_style: dict[str, Any],
        row_style: dict[str, Any],
        label_style: dict[str, Any],
    ) -> None:
        self.ids = ids
        self.scroll_style = scroll_style
        self.row_style = row_style
        self.label_style = label_style


class BaseSection:
    def __init__(self, *, context: SectionContext, debug_mode: bool = False) -> None:
        self.context = context
        self.debug_mode = bool(debug_mode)

    def layout(self) -> dbc.Card:
        raise NotImplementedError

    def register_callbacks(self) -> None:
        return

    def _inline_row(self, label: str, control, *, margin_top: bool = True) -> html.Div:
        style = dict(self.context.row_style)
        if not margin_top:
            style.pop("marginTop", None)

        return html.Div([html.Div([label], style=self.context.label_style), control], style=style)
