# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def build_graph_toggle_control(
    *,
    switch_id: str,
    label: str = "Show graph",
    value: Optional[list[str]] = None,
) -> dbc.Checklist:
    """
    Build the shared graph visibility toggle.
    """
    return dbc.Checklist(
        id=switch_id,
        options=[
            {
                "label": label,
                "value": "enabled",
            }
        ],
        value=value if value is not None else ["enabled"],
        switch=True,
        inline=True,
        persistence=True,
        persistence_type="session",
    )


def build_log_scale_control(
    *,
    switch_id: str,
    label: str,
    value: Optional[list[str]] = None,
) -> dbc.Checklist:
    """
    Build a shared log scale toggle.
    """
    return dbc.Checklist(
        id=switch_id,
        options=[
            {
                "label": label,
                "value": "log",
            }
        ],
        value=value if value is not None else [],
        switch=True,
        inline=True,
        persistence=True,
        persistence_type="session",
    )


def build_number_of_bins_control(
    *,
    container_id: str,
    input_id: str,
    value: int = 100,
    minimum: int = 1,
    maximum: int = 10_000,
    step: int = 1,
    label: str = "Bins",
) -> html.Div:
    """
    Build the shared histogram bin count control.

    The wrapper has its own ID so it can be hidden for scatter plots.
    """
    return html.Div(
        id=container_id,
        children=[
            dbc.Label(
                label,
                html_for=input_id,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dbc.Input(
                id=input_id,
                type="number",
                value=value,
                min=minimum,
                max=maximum,
                step=step,
                size="sm",
                style={
                    "width": "110px",
                },
                persistence=True,
                persistence_type="session",
            ),
        ],
    )


def build_histogram_controls(
    *,
    container_id: str,
    nbins_control_container_id: str,
    nbins_input_id: str,
    xscale_switch_id: str,
    yscale_switch_id: str,
    number_of_bins: int = 100,
    xscale: str = "linear",
    yscale: str = "log",
) -> html.Div:
    """
    Build the shared graph scale and histogram controls.

    The bin control is wrapped separately so visibility callbacks can hide it
    for two dimensional scatter plots while keeping log x and log y visible.
    """
    return html.Div(
        id=container_id,
        children=[
            build_number_of_bins_control(
                container_id=nbins_control_container_id,
                input_id=nbins_input_id,
                value=number_of_bins,
            ),
            build_log_scale_control(
                switch_id=xscale_switch_id,
                label="Log x",
                value=["log"] if xscale == "log" else [],
            ),
            build_log_scale_control(
                switch_id=yscale_switch_id,
                label="Log y",
                value=["log"] if yscale == "log" else [],
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "16px",
            "flexWrap": "wrap",
        },
    )


def build_graph_container(
    *,
    container_id: str,
    graph_id: str,
) -> html.Div:
    """
    Build the shared graph container.
    """
    return html.Div(
        id=container_id,
        children=[
            dcc.Graph(
                id=graph_id,
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
                style={
                    "height": "520px",
                    "width": "100%",
                },
            )
        ],
        style={
            "display": "block",
        },
    )


def build_detector_dropdown_control(
    *,
    dropdown_id: Any,
    label: str,
    value: Any = None,
    placeholder: str = "Select detector",
) -> html.Div:
    """
    Build a detector dropdown used by a peak process.
    """
    return html.Div(
        [
            dbc.Label(
                label,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dcc.Dropdown(
                id=dropdown_id,
                options=[],
                value=value,
                placeholder=placeholder,
                clearable=True,
                persistence=True,
                persistence_type="session",
            ),
        ],
        style={
            "minWidth": "220px",
            "flex": "1 1 220px",
        },
    )


def build_integer_setting_control(
    *,
    input_id: Any,
    label: str,
    value: int,
    minimum: int = 1,
    maximum: int = 50,
    step: int = 1,
) -> html.Div:
    """
    Build an integer process setting input.
    """
    return html.Div(
        [
            dbc.Label(
                label,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dbc.Input(
                id=input_id,
                type="number",
                value=value,
                min=minimum,
                max=maximum,
                step=step,
                size="sm",
                persistence=True,
                persistence_type="session",
            ),
        ],
        style={
            "width": "130px",
        },
    )


def build_float_setting_control(
    *,
    input_id: Any,
    label: str,
    value: float,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    step: float = 0.01,
) -> html.Div:
    """
    Build a floating point process setting input.
    """
    input_kwargs: dict[str, Any] = {
        "id": input_id,
        "type": "number",
        "value": value,
        "step": step,
        "size": "sm",
        "persistence": True,
        "persistence_type": "session",
    }

    if minimum is not None:
        input_kwargs["min"] = minimum

    if maximum is not None:
        input_kwargs["max"] = maximum

    return html.Div(
        [
            dbc.Label(
                label,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dbc.Input(
                **input_kwargs,
            ),
        ],
        style={
            "width": "130px",
        },
    )


def build_text_setting_control(
    *,
    input_id: Any,
    label: str,
    value: str = "",
    placeholder: str = "",
) -> html.Div:
    """
    Build a text process setting input.
    """
    return html.Div(
        [
            dbc.Label(
                label,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dbc.Input(
                id=input_id,
                type="text",
                value=value,
                placeholder=placeholder,
                size="sm",
                persistence=True,
                persistence_type="session",
            ),
        ],
        style={
            "minWidth": "180px",
        },
    )


def build_select_setting_control(
    *,
    dropdown_id: Any,
    label: str,
    options: list[dict[str, Any]],
    value: Any = None,
    placeholder: str = "Select value",
) -> html.Div:
    """
    Build a dropdown process setting input.
    """
    return html.Div(
        [
            dbc.Label(
                label,
                style={
                    "marginBottom": "4px",
                    "fontSize": "0.85rem",
                },
            ),
            dcc.Dropdown(
                id=dropdown_id,
                options=options,
                value=value,
                placeholder=placeholder,
                clearable=True,
                persistence=True,
                persistence_type="session",
            ),
        ],
        style={
            "minWidth": "180px",
        },
    )


def build_process_action_buttons(
    *,
    ids: Any,
    process_name: str,
    supports_automatic_action: bool,
    supports_clear: bool,
    run_label: str = "Run",
    clear_label: str = "Clear",
) -> list[Any]:
    """
    Build action buttons for a peak process.
    """
    buttons: list[Any] = []

    if supports_automatic_action:
        buttons.append(
            dbc.Button(
                run_label,
                id=ids.process_action_button(
                    process_name=process_name,
                    action_name="run",
                ),
                n_clicks=0,
                size="sm",
                color="primary",
            )
        )

    if supports_clear:
        buttons.append(
            dbc.Button(
                clear_label,
                id=ids.process_action_button(
                    process_name=process_name,
                    action_name="clear",
                ),
                n_clicks=0,
                size="sm",
                color="secondary",
                outline=True,
            )
        )

    return buttons