import dash_bootstrap_components as dbc
from dash import html
from typing import Any

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
    "backgroundColor": "var(--rosettax-control-background)",
    "color": "var(--rosettax-text-color)",
    "border": "1px solid var(--rosettax-border-color)",
    "borderRadius": "8px",
}


def build_plot_number_control(
    *,
    container_id: str | None,
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
                class_name="plot-option-label",
            ),
            dbc.Input(
                id=input_id,
                type="text",
                inputMode=input_mode,
                value=str(value),
                debounce=True,
                persistence=True,
                persistence_type="session",
                style={"width": "100%", "maxWidth": width},
            ),
        ],
        className="plot-option-number",
        style=None if visible else {"display": "none"},
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
    component_id: str | None = None,
    style_overrides: dict[str, Any] | None = None,
) -> html.Div:
    """Build the themed panel that contains plot options."""
    kwargs: dict[str, Any] = {}
    if component_id is not None:
        kwargs["id"] = component_id
    return html.Div(
        children,
        style={**build_plot_control_panel_style(), **(style_overrides or {})},
        **kwargs,
    )


def build_plot_axis_checklist(
    *,
    component_id: str,
    options: list[dict[str, str]],
    value: list[str] | None = None,
) -> dbc.Checklist:
    """Build the stacked log-scale switches."""
    return dbc.Checklist(
        id=component_id,
        options=options,
        value=value if isinstance(value, list) else [],
        inline=False,
        switch=True,
        class_name="plot-option-switches",
        persistence=True,
        persistence_type="session",
    )


class PlotOptions:
    """Build the shared Axes and Display options used below plots."""

    x_log_value = "x_log"
    y_log_value = "y_log"
    color_log_value = "colormap_log"

    @classmethod
    def build_component(
        cls,
        *,
        component_id: str,
        value: list[str] | None = None,
        color_log_enabled: bool = False,
        display_controls: list[Any] | None = None,
    ) -> html.Div:
        """Build standardized Axes and optional Display option groups."""
        axis_options = [
            {"label": "X axis", "value": cls.x_log_value},
            {"label": "Y axis", "value": cls.y_log_value},
        ]
        if color_log_enabled:
            axis_options.append({"label": "Color", "value": cls.color_log_value})

        groups = [
            html.Div(
                [
                    html.Strong("Log scale"),
                    build_plot_axis_checklist(component_id=component_id, options=axis_options, value=value),
                ],
                className="plot-options-group plot-options-scale",
                role="group",
                **{"aria-label": "Log scale"},
            ),
        ]
        if display_controls:
            groups.append(
                html.Div(
                    [html.Strong("Display"), html.Div(display_controls, className="plot-options-fields")],
                    className="plot-options-group plot-options-display",
                    role="group",
                    **{"aria-label": "Display"},
                )
            )
        return html.Div(groups, className="plot-options")
