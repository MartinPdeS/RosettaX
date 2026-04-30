# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.utils import styling


def copy_style(
    style: Any,
) -> dict[str, Any]:
    """
    Return a mutable copy of a style dictionary.
    """
    if isinstance(style, dict):
        return dict(style)

    return {}


def merge_style(
    *styles: Any,
) -> dict[str, Any]:
    """
    Merge style dictionaries while ignoring non dictionary values.
    """
    merged_style: dict[str, Any] = {}

    for style in styles:
        if isinstance(style, dict):
            merged_style.update(style)

    return merged_style


def normalize_children(
    children: Any,
) -> list[Any]:
    """
    Normalize Dash children into a list.
    """
    if children is None:
        return []

    if isinstance(children, list):
        return children

    if isinstance(children, tuple):
        return list(children)

    return [children]


def resolve_color_name(
    *,
    color_name: Optional[str] = None,
    accent_rgba: Optional[str] = None,
) -> str:
    """
    Resolve the color name used by the shared styling helpers.

    The accent_rgba argument is kept for backward compatibility. When provided,
    it is interpreted as a raw RGB triplet.
    """
    if color_name is not None:
        return color_name

    if accent_rgba is not None:
        return accent_rgba

    return "blue"


def build_rgba_from_color_name(
    *,
    color_name: Optional[str] = None,
    accent_rgba: Optional[str] = None,
    opacity: float,
) -> str:
    """
    Build an rgba CSS value from a named color or a raw RGB triplet.
    """
    if accent_rgba is not None and color_name is None:
        return f"rgba({accent_rgba}, {opacity})"

    return styling.build_rgba(
        color_name or "blue",
        opacity,
    )


def persistent_input(
    *,
    persistence: bool = True,
    persistence_type: str = "session",
    **kwargs: Any,
) -> dcc.Input:
    """
    Build a Dash input with session persistence enabled by default.
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
    """
    return dcc.Checklist(
        persistence=persistence,
        persistence_type=persistence_type,
        **kwargs,
    )


def build_info_badge(
    *,
    tooltip_target_id: str,
    text: str = "i",
    style_overrides: Optional[dict[str, Any]] = None,
) -> html.Span:
    """
    Build a compact reusable hover help badge.
    """
    return html.Span(
        text,
        id=tooltip_target_id,
        style=merge_style(
            styling.WORKFLOW_SECTION["info_badge"],
            {
                "userSelect": "none",
            },
            style_overrides,
        ),
    )


def build_title_with_info(
    *,
    title: str,
    tooltip_target_id: str,
    tooltip_id: str,
    tooltip_text: str,
    placement: str = "right",
    title_style_overrides: Optional[dict[str, Any]] = None,
    badge_style_overrides: Optional[dict[str, Any]] = None,
) -> html.Div:
    """
    Build a compact title with a hover help tooltip.
    """
    return html.Div(
        [
            html.Span(title),
            build_info_badge(
                tooltip_target_id=tooltip_target_id,
                style_overrides=badge_style_overrides,
            ),
            dbc.Tooltip(
                tooltip_text,
                id=tooltip_id,
                target=tooltip_target_id,
                placement=placement,
            ),
        ],
        style=merge_style(
            styling.WORKFLOW_SECTION["title_with_info"],
            title_style_overrides,
        ),
    )


def build_card_header_with_info(
    *,
    title: str,
    tooltip_target_id: str,
    tooltip_id: str,
    tooltip_text: str,
    subtitle: Optional[str] = None,
    placement: str = "right",
    color_name: str = "blue",
    header_style_overrides: Optional[dict[str, Any]] = None,
    title_style_overrides: Optional[dict[str, Any]] = None,
    subtitle_style_overrides: Optional[dict[str, Any]] = None,
) -> dbc.CardHeader:
    """
    Build a workflow card header with title, tooltip, and optional subtitle.
    """
    children: list[Any] = [
        build_title_with_info(
            title=title,
            tooltip_target_id=tooltip_target_id,
            tooltip_id=tooltip_id,
            tooltip_text=tooltip_text,
            placement=placement,
            title_style_overrides=title_style_overrides,
        )
    ]

    if subtitle:
        children.append(
            html.Div(
                subtitle,
                style=build_workflow_section_subtitle_style(
                    style_overrides=subtitle_style_overrides,
                ),
            )
        )

    return dbc.CardHeader(
        children,
        style=build_workflow_section_header_style(
            color_name=color_name,
            style_overrides=header_style_overrides,
        ),
    )


def build_workflow_section_card_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    border_radius_px: int = 15,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard outer workflow section card style.
    """
    return merge_style(
        {
            "borderRadius": f"{border_radius_px}px",
            "borderLeft": (
                "5px solid "
                f"{build_rgba_from_color_name(color_name=color_name, accent_rgba=accent_rgba, opacity=0.75)}"
            ),
            "boxShadow": "0 0.35rem 0.9rem rgba(0, 0, 0, 0.08)",
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_section_header_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    border_radius_px: int = 15,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard outer workflow section header style.
    """
    return merge_style(
        {
            "background": build_rgba_from_color_name(
                color_name=color_name,
                accent_rgba=accent_rgba,
                opacity=0.10,
            ),
            "borderBottom": (
                "1px solid "
                f"{build_rgba_from_color_name(color_name=color_name, accent_rgba=accent_rgba, opacity=0.20)}"
            ),
            "padding": "13px 18px",
            "borderTopLeftRadius": f"{border_radius_px}px",
            "borderTopRightRadius": f"{border_radius_px}px",
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_section_body_style(
    *,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard outer workflow section body style.
    """
    return merge_style(
        {
            "padding": "18px",
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_section_subtitle_style(
    *,
    font_size: str = "0.86rem",
    opacity: float = 0.76,
    margin_top_px: int = 3,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard subtitle style used under workflow section headers.
    """
    return merge_style(
        {
            "fontSize": font_size,
            "opacity": opacity,
            "marginTop": f"{int(margin_top_px)}px",
        },
        style_overrides,
    )


def build_workflow_panel_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    background: Optional[str] = None,
    border_radius_px: int = 12,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a standard inner workflow panel card style.
    """
    base_style: dict[str, Any] = {
        "borderRadius": f"{border_radius_px}px",
        "border": (
            "1px solid "
            f"{build_rgba_from_color_name(color_name=color_name, accent_rgba=accent_rgba, opacity=0.16)}"
        ),
        "overflow": "visible",
    }

    if background is not None:
        base_style["background"] = background

    return merge_style(
        base_style,
        style_overrides,
    )


def build_workflow_panel_body_style(
    *,
    padding: str = "16px",
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a standard inner workflow panel body style.
    """
    return merge_style(
        {
            "padding": padding,
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_subpanel_card_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    border_radius_px: int = 12,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a nested graph or form panel card style.
    """
    return build_workflow_panel_style(
        color_name=color_name,
        accent_rgba=accent_rgba,
        border_radius_px=border_radius_px,
        style_overrides=style_overrides,
    )


def build_workflow_subpanel_header_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    border_radius_px: int = 12,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a nested graph or form panel header style.
    """
    return merge_style(
        {
            "background": build_rgba_from_color_name(
                color_name=color_name,
                accent_rgba=accent_rgba,
                opacity=0.06,
            ),
            "borderBottom": (
                "1px solid "
                f"{build_rgba_from_color_name(color_name=color_name, accent_rgba=accent_rgba, opacity=0.16)}"
            ),
            "padding": "12px 16px",
            "borderTopLeftRadius": f"{border_radius_px}px",
            "borderTopRightRadius": f"{border_radius_px}px",
            "overflow": "visible",
        },
        style_overrides,
    )


def build_compact_control_panel_style(
    *,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a compact control strip style for toggles or graph controls.
    """
    return merge_style(
        styling.WORKFLOW_SECTION["compact_control_box"],
        {
            "overflow": "visible",
        },
        style_overrides,
    )


def build_metric_box_style(
    *,
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a compact metric display box style.
    """
    return merge_style(
        {
            "padding": "8px 10px",
            "border": "1px solid rgba(128, 128, 128, 0.25)",
            "borderRadius": "8px",
            "background": "rgba(128, 128, 128, 0.08)",
        },
        style_overrides,
    )


def apply_workflow_section_card_style(
    card: Any,
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    header_background: Optional[str] = None,
    header_border: Optional[str] = None,
    left_border: Optional[str] = None,
    border_radius_px: int = 15,
    header_font_weight: str = "750",
    header_font_size: str = "1.02rem",
) -> Any:
    """
    Apply the shared RosettaX workflow section card styling to an existing card.

    This is used when a reusable layout object already returns a dbc.Card.
    """
    card_style = build_workflow_section_card_style(
        color_name=color_name,
        accent_rgba=accent_rgba,
        border_radius_px=border_radius_px,
    )

    if left_border is not None:
        card_style["borderLeft"] = left_border

    card.style = merge_style(
        copy_style(getattr(card, "style", None)),
        card_style,
    )

    header_style_overrides = {
        "fontWeight": header_font_weight,
        "fontSize": header_font_size,
    }

    if header_background is not None:
        header_style_overrides["background"] = header_background

    if header_border is not None:
        header_style_overrides["borderBottom"] = header_border

    for child in normalize_children(getattr(card, "children", None)):
        if isinstance(child, dbc.CardHeader):
            child.style = merge_style(
                copy_style(getattr(child, "style", None)),
                build_workflow_section_header_style(
                    color_name=color_name,
                    accent_rgba=accent_rgba,
                    border_radius_px=border_radius_px,
                    style_overrides=header_style_overrides,
                ),
            )

        if isinstance(child, dbc.CardBody):
            child.style = merge_style(
                copy_style(getattr(child, "style", None)),
                build_workflow_section_body_style(),
            )

    return card


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
    """
    row_style = merge_style(
        {
            "display": "flex",
            "alignItems": align_items,
            "gap": f"{int(gap_px)}px",
            "marginBottom": f"{int(margin_bottom_px)}px",
            "overflow": "visible",
        },
        row_style_overrides,
    )

    label_style = merge_style(
        {
            "width": f"{int(label_width_px)}px",
            "minWidth": f"{int(label_width_px)}px",
            "fontWeight": label_font_weight,
            "marginBottom": label_margin_bottom,
        },
        label_style_overrides,
    )

    component_style = {
        "flex": component_flex,
        "overflow": "visible",
    }

    if component_display is not None:
        component_style["display"] = component_display

    if component_align_items is not None:
        component_style["alignItems"] = component_align_items

    component_style = merge_style(
        component_style,
        component_style_overrides,
    )

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
    """
    row_style: dict[str, Any] = {
        "display": "flex",
        "alignItems": align_items,
        "width": row_width,
        "overflow": "visible",
    }

    if margin_top:
        row_style["marginTop"] = f"{int(margin_top_px)}px"

    row_style = merge_style(
        row_style,
        row_style_overrides,
    )

    label_style = merge_style(
        {
            "width": f"{int(label_width_px)}px",
            "minWidth": f"{int(label_width_px)}px",
            "fontWeight": label_font_weight,
        },
        label_style_overrides,
    )

    control_wrapper_style = merge_style(
        {
            "flex": "1",
            "display": "flex",
            "alignItems": align_items,
            "overflow": "visible",
        },
        control_wrapper_style_overrides,
    )

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
    """
    heading_factory = {
        "H2": html.H2,
        "H4": html.H4,
        "H5": html.H5,
        "H6": html.H6,
    }.get(
        str(title_component).upper(),
        html.H5,
    )

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

    children: list[Any] = [
        heading_factory(
            title,
            style=merge_style(
                default_title_style,
                title_style_overrides,
            ),
        )
    ]

    if description:
        children.append(
            html.P(
                description,
                style=merge_style(
                    {
                        "marginBottom": f"{int(description_margin_bottom_px)}px",
                        "opacity": description_opacity,
                    },
                    description_style_overrides,
                ),
            )
        )

    return html.Div(
        children,
        style=copy_style(container_style),
    )