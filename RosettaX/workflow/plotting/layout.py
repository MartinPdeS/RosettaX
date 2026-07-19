# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import html


PLOT_CONTROL_LABEL_STYLE = {
    "marginBottom": "4px",
    "fontSize": "0.85rem",
    "fontWeight": "500",
}

PLOT_CONTROL_PANEL_STYLE = {
    "padding": "10px 12px",
    "display": "flex",
    "alignItems": "center",
    "gap": "16px",
    "flexWrap": "wrap",
    "backgroundColor": "#f4f5f7",
    "border": "1px solid #d9dde3",
    "borderRadius": "8px",
}


def build_plot_number_control(
    *,
    container_id: Optional[str],
    input_id: str,
    label: str,
    value: Any,
    input_mode: str = "decimal",
    width: str = "150px",
    visible: bool = True,
) -> html.Div:
    """Build one consistent spinner-free plotting input."""
    container_kwargs: dict[str, Any] = {}
    if container_id is not None:
        container_kwargs["id"] = container_id

    return html.Div(
        [
            dbc.Label(
                label,
                html_for=input_id,
                style=PLOT_CONTROL_LABEL_STYLE,
            ),
            dbc.Input(
                id=input_id,
                type="text",
                inputMode=input_mode,
                value=str(value),
                debounce=True,
                persistence=True,
                persistence_type="session",
                style={"width": width},
            ),
        ],
        style={
            "display": "flex" if visible else "none",
            "flexDirection": "column",
            "gap": "4px",
            "minWidth": width,
        },
        **container_kwargs,
    )


def build_plot_control_panel_style(*, visible: bool = True) -> dict[str, Any]:
    """Return the shared style for a plotting control panel."""
    return {
        **PLOT_CONTROL_PANEL_STYLE,
        "display": "flex" if visible else "none",
    }


def build_plot_control_panel(
    children: list[Any],
    *,
    component_id: Optional[str] = None,
) -> html.Div:
    """Build the shared grey panel that contains plot options."""
    kwargs: dict[str, Any] = {}
    if component_id is not None:
        kwargs["id"] = component_id
    return html.Div(
        children,
        style=build_plot_control_panel_style(),
        **kwargs,
    )


def build_plot_axis_checklist(
    *,
    component_id: str,
    options: list[dict[str, str]],
    value: Optional[list[str]] = None,
) -> dbc.Checklist:
    """Build a consistent inline log-axis checklist."""
    return dbc.Checklist(
        id=component_id,
        options=options,
        value=value if isinstance(value, list) else [],
        inline=True,
        switch=True,
        persistence=True,
        persistence_type="session",
    )
