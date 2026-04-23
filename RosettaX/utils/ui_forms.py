# -*- coding: utf-8 -*-

from typing import Any, Optional

from dash import dcc, html


def persistent_input(
    *,
    persistence: bool = True,
    persistence_type: str = "session",
    **kwargs: Any,
) -> dcc.Input:
    """
    Build a Dash input with session persistence enabled by default.

    Parameters
    ----------
    persistence
        Whether the component value should persist across page refreshes
        within the same browser session.
    persistence_type
        Dash persistence backend. Defaults to ``"session"``.
    **kwargs
        Additional keyword arguments forwarded to ``dcc.Input``.

    Returns
    -------
    dcc.Input
        Configured Dash input component.
    """
    return dcc.Input(
        persistence=persistence,
        persistence_type=persistence_type,
        **kwargs,
    )


def persistent_dropdown(
    *,
    persistence: bool = True,
    persistence_type: str = "session",
    **kwargs: Any,
) -> dcc.Dropdown:
    """
    Build a Dash dropdown with session persistence enabled by default.

    Parameters
    ----------
    persistence
        Whether the component value should persist across page refreshes
        within the same browser session.
    persistence_type
        Dash persistence backend. Defaults to ``"session"``.
    **kwargs
        Additional keyword arguments forwarded to ``dcc.Dropdown``.

    Returns
    -------
    dcc.Dropdown
        Configured Dash dropdown component.
    """
    return dcc.Dropdown(
        persistence=persistence,
        persistence_type=persistence_type,
        **kwargs,
    )


def persistent_checklist(
    *,
    persistence: bool = True,
    persistence_type: str = "session",
    **kwargs: Any,
) -> dcc.Checklist:
    """
    Build a Dash checklist with session persistence enabled by default.

    Parameters
    ----------
    persistence
        Whether the component value should persist across page refreshes
        within the same browser session.
    persistence_type
        Dash persistence backend. Defaults to ``"session"``.
    **kwargs
        Additional keyword arguments forwarded to ``dcc.Checklist``.

    Returns
    -------
    dcc.Checklist
        Configured Dash checklist component.
    """
    return dcc.Checklist(
        persistence=persistence,
        persistence_type=persistence_type,
        **kwargs,
    )


def build_labeled_row(
    *,
    label: str,
    component: Any,
    label_width_px: int = 320,
    gap_px: int = 12,
    margin_bottom_px: int = 10,
    align_items: str = "center",
    label_font_weight: str = "500",
    label_margin_bottom: str = "0",
    component_flex: str = "1",
    component_display: Optional[str] = None,
    component_align_items: Optional[str] = None,
    row_style_overrides: Optional[dict[str, Any]] = None,
    label_style_overrides: Optional[dict[str, Any]] = None,
    component_style_overrides: Optional[dict[str, Any]] = None,
) -> html.Div:
    """
    Build a standard two column form row with a fixed width label area.

    This is intended for repeated settings style layouts where the left side
    contains a text label and the right side contains a control component.

    Parameters
    ----------
    label
        Label text shown on the left side.
    component
        Dash component rendered on the right side.
    label_width_px
        Fixed width allocated to the label area.
    gap_px
        Horizontal space between the label and the component.
    margin_bottom_px
        Bottom margin applied to the whole row.
    align_items
        Flex alignment of the row.
    label_font_weight
        CSS font weight used for the label.
    label_margin_bottom
        CSS marginBottom value for the label.
    component_flex
        CSS flex value used for the component wrapper.
    component_display
        Optional CSS display value for the component wrapper.
    component_align_items
        Optional CSS alignItems value for the component wrapper.
    row_style_overrides
        Optional extra CSS merged into the row style.
    label_style_overrides
        Optional extra CSS merged into the label style.
    component_style_overrides
        Optional extra CSS merged into the component wrapper style.

    Returns
    -------
    html.Div
        Row container.
    """
    row_style: dict[str, Any] = {
        "display": "flex",
        "alignItems": align_items,
        "gap": f"{int(gap_px)}px",
        "marginBottom": f"{int(margin_bottom_px)}px",
    }

    label_style: dict[str, Any] = {
        "width": f"{int(label_width_px)}px",
        "minWidth": f"{int(label_width_px)}px",
        "fontWeight": label_font_weight,
        "marginBottom": label_margin_bottom,
    }

    component_style: dict[str, Any] = {
        "flex": component_flex,
    }

    if component_display is not None:
        component_style["display"] = component_display

    if component_align_items is not None:
        component_style["alignItems"] = component_align_items

    if row_style_overrides:
        row_style.update(row_style_overrides)

    if label_style_overrides:
        label_style.update(label_style_overrides)

    if component_style_overrides:
        component_style.update(component_style_overrides)

    return html.Div(
        [
            html.Div(label, style=label_style),
            html.Div(component, style=component_style),
        ],
        style=row_style,
    )


def build_inline_row(
    *,
    label: str,
    control: Any,
    label_width_px: int = 260,
    margin_top: bool = True,
    margin_top_px: int = 10,
    row_width: str = "100%",
    align_items: str = "center",
    label_font_weight: int | str = 500,
    label_style_overrides: Optional[dict[str, Any]] = None,
    control_wrapper_style_overrides: Optional[dict[str, Any]] = None,
    row_style_overrides: Optional[dict[str, Any]] = None,
) -> html.Div:
    """
    Build a common inline row used in parameter panels.

    This helper mirrors the pattern often used in RosettaX pages where a label
    sits on the left and the control is wrapped in a flexible container on the
    right.

    Parameters
    ----------
    label
        Label text shown on the left side.
    control
        Dash component or component tree rendered on the right side.
    label_width_px
        Fixed width allocated to the label area.
    margin_top
        Whether the row should include top margin.
    margin_top_px
        Amount of top margin when ``margin_top`` is enabled.
    row_width
        CSS width of the row.
    align_items
        Flex alignment of the row.
    label_font_weight
        CSS font weight of the label.
    label_style_overrides
        Optional extra CSS merged into the label style.
    control_wrapper_style_overrides
        Optional extra CSS merged into the control wrapper style.
    row_style_overrides
        Optional extra CSS merged into the row style.

    Returns
    -------
    html.Div
        Row container.
    """
    row_style: dict[str, Any] = {
        "display": "flex",
        "alignItems": align_items,
        "width": row_width,
    }

    if margin_top:
        row_style["marginTop"] = f"{int(margin_top_px)}px"

    label_style: dict[str, Any] = {
        "width": f"{int(label_width_px)}px",
        "minWidth": f"{int(label_width_px)}px",
        "fontWeight": label_font_weight,
    }

    control_wrapper_style: dict[str, Any] = {
        "flex": "1",
        "display": "flex",
        "alignItems": align_items,
    }

    if row_style_overrides:
        row_style.update(row_style_overrides)

    if label_style_overrides:
        label_style.update(label_style_overrides)

    if control_wrapper_style_overrides:
        control_wrapper_style.update(control_wrapper_style_overrides)

    return html.Div(
        [
            html.Div(label, style=label_style),
            html.Div(control, style=control_wrapper_style),
        ],
        style=row_style,
    )


def build_section_intro(
    *,
    title: str,
    description: Optional[str] = None,
    title_component: str = "H5",
    title_style_overrides: Optional[dict[str, Any]] = None,
    description_opacity: float = 0.85,
    description_margin_bottom_px: int = 10,
    description_style_overrides: Optional[dict[str, Any]] = None,
    container_style: Optional[dict[str, Any]] = None,
) -> html.Div:
    """
    Build a small section intro block with a title and optional description.

    Parameters
    ----------
    title
        Section title.
    description
        Optional explanatory text shown below the title.
    title_component
        HTML heading component name. Supported values are ``"H4"``, ``"H5"``,
        and ``"H6"``. Any other value falls back to ``html.H5``.
    description_opacity
        CSS opacity used for the description paragraph.
    description_margin_bottom_px
        Bottom margin applied to the description paragraph.
    container_style
        Optional container style overrides.

    Returns
    -------
    html.Div
        Section intro block.
    """
    heading_factory = {
        "H4": html.H4,
        "H5": html.H5,
        "H6": html.H6,
    }.get(str(title_component).upper(), html.H5)

    default_title_style = {
        "marginBottom": "8px",
    }

    if str(title_component).upper() == "H2":
        default_title_style.update(
            {
                "fontSize": "2rem",
                "fontWeight": "600",
                "lineHeight": "1.2",
            }
        )

    elif str(title_component).upper() == "H4":
        default_title_style.update(
            {
                "fontWeight": "600",
                "lineHeight": "1.25",
            }
        )

    elif str(title_component).upper() == "H5":
        default_title_style.update(
            {
                "fontWeight": "600",
                "lineHeight": "1.3",
            }
        )

    if title_style_overrides:
        default_title_style.update(title_style_overrides)

    description_style = {
        "marginBottom": f"{int(description_margin_bottom_px)}px",
        "opacity": description_opacity,
    }

    if description_style_overrides:
        description_style.update(description_style_overrides)

    children: list[Any] = [heading_factory(title, style=default_title_style)]

    if description:
        children.append(
            html.P(
                description,
                style=description_style,
            )
        )

    return html.Div(
        children,
        style=container_style or {},
    )