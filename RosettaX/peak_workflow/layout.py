# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.peak_script.registry import build_peak_process_options
from RosettaX.utils import styling, graph_config


def build_process_selector(
    *,
    ids: Any,
    default_process_name: str,
) -> dash.html.Div:
    """
    Build the peak process selector.
    """
    return dash.html.Div(
        [
            dash.html.Div(
                "Peak detection process:",
                style={
                    "marginBottom": "6px",
                    "fontWeight": 500,
                },
            ),
            dash.dcc.Dropdown(
                id=ids.process_dropdown,
                options=build_peak_process_options(),
                value=default_process_name,
                clearable=False,
                searchable=False,
                persistence=True,
                persistence_type="session",
                style={
                    "width": "500px",
                    "maxWidth": "100%",
                },
            ),
        ],
        style=styling.CARD,
    )


def build_process_controls(
    *,
    ids: Any,
    processes: list[Any],
) -> dash.html.Div:
    """
    Build all process owned controls.
    """
    return dash.html.Div(
        [
            process.build_controls(
                ids=ids,
            )
            for process in processes
        ]
    )


def build_graph_toggle_switch(
    *,
    ids: Any,
    show_graphs: bool,
) -> dash.html.Div:
    """
    Build graph visibility switch.
    """
    return dash.html.Div(
        [
            dbc.Checklist(
                id=ids.graph_toggle_switch,
                options=[
                    {
                        "label": "Show graph",
                        "value": "enabled",
                    }
                ],
                value=["enabled"] if show_graphs else [],
                switch=True,
                persistence=True,
                persistence_type="session",
            ),
        ],
        style=styling.CARD,
    )


def build_graph_controls_container(
    *,
    ids: Any,
    histogram_scale: str,
    nbins: int,
) -> dash.html.Div:
    """
    Build graph and graph controls.
    """
    return dash.html.Div(
        [
            build_graph(ids=ids),
            dash.html.Br(),
            dash.html.Div(
                [
                    build_yscale_switch(
                        ids=ids,
                        histogram_scale=histogram_scale,
                    ),
                    build_nbins_input(
                        ids=ids,
                        nbins=nbins,
                    ),
                ],
                id=ids.histogram_controls_container,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                    "flexWrap": "wrap",
                },
            ),
        ],
        id=ids.graph_toggle_container,
        style={
            "display": "none",
        },
    )


def build_graph(
    *,
    ids: Any,
) -> dash.dcc.Loading:
    """
    Build the graph component.
    """
    return dash.dcc.Loading(
        dash.dcc.Graph(
            id=ids.graph_hist,
            style=graph_config.PLOTLY_GRAPH_STYLE,
            config=graph_config.PLOTLY_GRAPH_CONFIG,
        ),
        type="default",
    )


def build_yscale_switch(
    *,
    ids: Any,
    histogram_scale: str,
) -> dbc.Checklist:
    """
    Build y scale switch.
    """
    return dbc.Checklist(
        id=ids.yscale_switch,
        options=[
            {
                "label": "Log scale",
                "value": "log",
            }
        ],
        value=["log"] if histogram_scale == "log" else [],
        switch=True,
        style={
            "display": "block",
        },
        persistence=True,
        persistence_type="session",
    )


def build_nbins_input(
    *,
    ids: Any,
    nbins: int,
) -> dash.html.Div:
    """
    Build number of bins input.
    """
    return dash.html.Div(
        [
            dash.html.Div(
                "Number of bins:",
                style={
                    "marginRight": "8px",
                },
            ),
            dash.dcc.Input(
                id=ids.nbins_input,
                type="number",
                min=10,
                step=10,
                value=nbins,
                style={
                    "width": "160px",
                },
                debounce=True,
                persistence=True,
                persistence_type="session",
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
        },
    )