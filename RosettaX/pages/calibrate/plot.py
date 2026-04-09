# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional, Tuple

import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc, html

from RosettaX.pages.calibrate.ids import Ids
from RosettaX.utils.reader import FCSFile


@dataclass(frozen=True)
class PlotResult:
    """
    Container for the Dash outputs of the plot callback.
    """

    figure: Any = dash.no_update
    status: Any = dash.no_update
    channel_value: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (self.figure, self.status, self.channel_value)


class PlotSection:
    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("4. Plot a channel"),
                dbc.CardBody(
                    [
                        self._controls_row(),
                        html.Div(style={"height": "10px"}),
                        dcc.Loading(
                            dcc.Graph(id=Ids.Plot.graph, style={"height": "360px"}),
                            type="default",
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Upload an FCS file, then pick a channel to plot.",
                            id=Ids.Plot.status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )

    def _controls_row(self) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        html.Div("Channel", style={"marginBottom": "6px"}),
                        dcc.Dropdown(
                            id=Ids.Plot.channel_dropdown,
                            options=[],
                            value=None,
                            placeholder="Select channel to plot",
                            clearable=True,
                            style={"width": "520px"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
                html.Div(
                    [
                        html.Div("Bins", style={"marginBottom": "6px"}),
                        dcc.Input(
                            id=Ids.Plot.nbins_input,
                            type="number",
                            min=10,
                            step=10,
                            value=200,
                            style={"width": "140px"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
                html.Div(
                    [
                        html.Div("Max events", style={"marginBottom": "6px"}),
                        dcc.Input(
                            id=Ids.Plot.max_events_input,
                            type="number",
                            min=1_000,
                            step=10_000,
                            value=200_000,
                            style={"width": "160px"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
                html.Div(
                    [
                        html.Div("Counts scale", style={"marginBottom": "6px"}),
                        dbc.Checklist(
                            id=Ids.Plot.yscale_switch,
                            options=[{"label": "Log", "value": "log"}],
                            value=["log"],
                            switch=True,
                            style={"marginTop": "4px"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
            ],
            style={"display": "flex", "gap": "14px", "alignItems": "flexEnd", "flexWrap": "wrap"},
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(Ids.Plot.channel_dropdown, "options"),
            dash.Input(Ids.Stores.uploaded_fcs_path_store, "data"),
            prevent_initial_call=True,
        )
        def populate_plot_channels(fcs_path: Optional[str]) -> list[dict[str, str]]:
            if not fcs_path:
                return []

            try:
                with FCSFile(str(fcs_path), writable=False) as fcs:
                    names = fcs.get_column_names()
            except Exception:
                return []

            return [{"label": n, "value": n} for n in names]

        @dash.callback(
            dash.Output(Ids.Plot.graph, "figure"),
            dash.Output(Ids.Plot.status, "children"),
            dash.Output(Ids.Plot.channel_dropdown, "value"),
            dash.Input(Ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Input(Ids.Plot.channel_dropdown, "value"),
            dash.Input(Ids.Plot.nbins_input, "value"),
            dash.Input(Ids.Plot.max_events_input, "value"),
            dash.Input(Ids.Plot.yscale_switch, "value"),
            prevent_initial_call=True,
        )
        def update_plot(
            fcs_path: Optional[str],
            channel: Optional[str],
            nbins_value: Any,
            max_events_value: Any,
            yscale_value: Any,
        ) -> tuple:
            if not fcs_path:
                fig = self._empty_figure()
                return PlotResult(
                    figure=fig,
                    status="Upload an FCS file first.",
                    channel_value=None,
                ).to_tuple()

            nbins = self._as_int(nbins_value, default=200, min_value=10, max_value=5000)
            max_events = self._as_int(max_events_value, default=200_000, min_value=1_000, max_value=5_000_000)
            use_log = isinstance(yscale_value, list) and ("log" in yscale_value)

            if not channel:
                fig = self._empty_figure()
                return PlotResult(
                    figure=fig,
                    status="Select a channel to plot.",
                    channel_value=dash.no_update,
                ).to_tuple()

            try:
                with FCSFile(str(fcs_path), writable=False) as fcs:
                    values = fcs.column_copy(str(channel), dtype=float, n=max_events)
            except Exception as exc:
                fig = self._empty_figure()
                return PlotResult(
                    figure=fig,
                    status=f"Could not read channel: {type(exc).__name__}: {exc}",
                    channel_value=dash.no_update,
                ).to_tuple()

            values = np.asarray(values, dtype=float)
            values = values[np.isfinite(values)]
            if values.size == 0:
                fig = self._empty_figure()
                return PlotResult(
                    figure=fig,
                    status="No finite values found for this channel.",
                    channel_value=dash.no_update,
                ).to_tuple()

            fig = self._histogram_figure(values=values, nbins=nbins, channel=str(channel), use_log=use_log)
            return PlotResult(
                figure=fig,
                status=f"Plotted {values.size} values from {channel}.",
                channel_value=dash.no_update,
            ).to_tuple()

    @staticmethod
    def _empty_figure() -> go.Figure:
        fig = go.Figure()
        fig.update_layout(separators=".,")
        return fig

    @staticmethod
    def _histogram_figure(*, values: np.ndarray, nbins: int, channel: str, use_log: bool) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=values, nbinsx=int(nbins), name=channel))
        fig.update_layout(
            xaxis_title=str(channel),
            yaxis_title="Counts",
            separators=".,",
            bargap=0.02,
        )
        fig.update_yaxes(type="log" if use_log else "linear")
        return fig

    @staticmethod
    def _as_int(value: Any, *, default: int, min_value: int, max_value: int) -> int:
        try:
            v = int(value)
        except Exception:
            v = int(default)

        if v < int(min_value):
            v = int(min_value)
        if v > int(max_value):
            v = int(max_value)

        return v