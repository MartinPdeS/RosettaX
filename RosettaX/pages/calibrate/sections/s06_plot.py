# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc, html
import logging

from RosettaX.utils.reader import FCSFile
logger = logging.getLogger(__name__)


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
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("4. Plot a channel"),
                dbc.CardBody(
                    [
                        self._controls_row(),
                        html.Div(style={"height": "10px"}),
                        dcc.Loading(
                            dcc.Graph(id=self.page.ids.Plot.graph, style={"height": "360px"}),
                            type="default",
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Upload an FCS file, then pick a channel to plot.",
                            id=self.page.ids.Plot.status,
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
                            id=self.page.ids.Plot.channel_dropdown,
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
                            id=self.page.ids.Plot.nbins_input,
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
                            id=self.page.ids.Plot.max_events_input,
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
                            id=self.page.ids.Plot.yscale_switch,
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
            dash.Output(self.page.ids.Plot.channel_dropdown, "options"),
            dash.Output(self.page.ids.Plot.channel_dropdown, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Plot.channel_dropdown, "value"),
            prevent_initial_call=False,
        )
        def populate_plot_channels(
            fcs_path: Optional[str],
            current_value: Optional[str],
        ) -> tuple[list[dict[str, str]], Optional[str]]:
            logger.debug(
                "populate_plot_channels called with fcs_path=%r current_value=%r",
                fcs_path,
                current_value,
            )

            if not fcs_path:
                logger.debug("No FCS path provided. Returning empty channel dropdown.")
                return [], None

            try:
                with FCSFile(str(fcs_path), writable=False) as fcs:
                    channel_names = fcs.get_column_names()
            except Exception:
                logger.exception(
                    "Failed to read channel names from fcs_path=%r",
                    fcs_path,
                )
                return [], None

            options = [{"label": name, "value": name} for name in channel_names]

            allowed_values = {str(option["value"]) for option in options}

            if current_value in allowed_values:
                resolved_value = current_value
            else:
                resolved_value = options[0]["value"] if options else None

            logger.debug(
                "Resolved plot channel dropdown with %r options and value=%r",
                len(options),
                resolved_value,
            )

            return options, resolved_value

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