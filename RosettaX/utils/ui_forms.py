# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.utils import styling
from RosettaX.utils.upload_limits import format_upload_size, get_max_upload_bytes


def _token_px_to_int(token_value: str, fallback: int) -> int:
    """
    Convert a px token value into an integer fallback-safe value.
    """
    value = str(token_value).strip()
    if value.endswith("px"):
        value = value[:-2]
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


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


def build_upload_widget(
    *,
    upload_id: Any,
    prompt_text: str,
    accepted_file_extensions: str,
    multiple: bool,
    max_size_bytes: Optional[int] = None,
) -> dcc.Upload:
    """Build the standard RosettaX file upload control and information text."""
    resolved_max_size = (
        get_max_upload_bytes() if max_size_bytes is None else int(max_size_bytes)
    )
    selection_text = "Multiple files allowed" if multiple else "One file"

    return dcc.Upload(
        id=upload_id,
        children=html.Div(
            [
                html.Div(
                    prompt_text,
                    style={
                        "fontWeight": "650",
                        "textDecoration": "none",
                    },
                ),
                html.Div(
                    (
                        f"{selection_text} · Accepted: {accepted_file_extensions} · "
                        f"Maximum file size: {format_upload_size(resolved_max_size)}"
                    ),
                    style={
                        "fontSize": "0.82rem",
                        "marginTop": "4px",
                        "opacity": 0.72,
                    },
                ),
            ]
        ),
        style=styling.merge_style(
            styling.UPLOAD,
            {
                "lineHeight": "1.35",
                "padding": "14px 16px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        ),
        max_size=resolved_max_size,
        multiple=multiple,
        accept=accepted_file_extensions,
    )


def build_upload_status(
    *,
    status_id: Any,
    initial_text: Any,
    color: str = "secondary",
    class_name: str = "mb-0 mt-3",
) -> dbc.Alert:
    """Build the standard status message shown below an upload control."""
    return dbc.Alert(
        initial_text,
        id=status_id,
        color=color,
        is_open=True,
        className=class_name,
        style={"borderRadius": styling.get_radius_token("sm", "8px")},
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
        style=styling.merge_style(
            styling.WORKFLOW_SECTION["info_badge"],
            {
                "userSelect": "none",
            },
            style_overrides,
        ),
    )


def _merge_tooltip_text(*parts: Optional[str]) -> str:
    """
    Combine related help text into one compact tooltip string.
    """
    return " ".join(part.strip() for part in parts if part and part.strip())


def build_title_with_info(
    *,
    title: str,
    tooltip_target_id: str,
    tooltip_id: str,
    tooltip_text: str,
    subtitle: Optional[str] = None,
    placement: str = "right",
    title_style_overrides: Optional[dict[str, Any]] = None,
    badge_style_overrides: Optional[dict[str, Any]] = None,
) -> html.Div:
    """
    Build a compact title with a hover help tooltip.
    """
    tooltip_content = _merge_tooltip_text(tooltip_text, subtitle)
    return html.Div(
        [
            html.Span(title),
            build_info_badge(
                tooltip_target_id=tooltip_target_id,
                style_overrides=badge_style_overrides,
            ),
            dbc.Tooltip(
                tooltip_content,
                id=tooltip_id,
                target=tooltip_target_id,
                placement=placement,
            ),
        ],
        style=styling.merge_style(
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
            subtitle=subtitle,
            placement=placement,
            title_style_overrides=title_style_overrides,
        )
    ]

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
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("lg"), 15),
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard outer workflow section card style.
    """
    return styling.merge_style(
        {
            "borderRadius": f"{border_radius_px}px",
            "borderLeft": (
                "5px solid "
                f"{build_rgba_from_color_name(color_name=color_name, accent_rgba=accent_rgba, opacity=0.75)}"
            ),
            "boxShadow": styling.get_shadow_token("soft"),
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_section_header_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("lg"), 15),
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard outer workflow section header style.
    """
    return styling.merge_style(
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
            "padding": f"{styling.get_spacing_token('sm')} {styling.get_spacing_token('lg')}",
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
    return styling.merge_style(
        {
            "padding": styling.get_spacing_token("lg"),
            "overflow": "visible",
        },
        style_overrides,
    )


def build_workflow_section_subtitle_style(
    *,
    font_size: str = styling.get_typography_token("subtitle_size", "0.86rem"),
    opacity: float = 0.76,
    margin_top_px: int = _token_px_to_int(styling.get_spacing_token("xs"), 8),
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build the standard subtitle style used under workflow section headers.
    """
    return styling.merge_style(
        {
            "fontSize": font_size,
            "opacity": opacity,
            "marginTop": f"{int(margin_top_px)}px",
            "fontWeight": styling.get_typography_token("subtitle_weight", "500"),
        },
        style_overrides,
    )


def build_workflow_panel_style(
    *,
    color_name: str = "blue",
    accent_rgba: Optional[str] = None,
    background: Optional[str] = None,
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("md"), 12),
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

    return styling.merge_style(
        base_style,
        style_overrides,
    )


def build_workflow_panel_body_style(
    *,
    padding: str = styling.get_spacing_token("md", "16px"),
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a standard inner workflow panel body style.
    """
    return styling.merge_style(
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
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("md"), 12),
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
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("md"), 12),
    style_overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Build a nested graph or form panel header style.
    """
    return styling.merge_style(
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
            "padding": f"{styling.get_spacing_token('sm')} {styling.get_spacing_token('md')}",
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
    return styling.merge_style(
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
    return styling.merge_style(
        {
            "padding": f"{styling.get_spacing_token('xs')} {styling.get_spacing_token('sm')}",
            "border": styling.get_border_token("strong"),
            "borderRadius": styling.get_radius_token("sm"),
            "background": "rgba(128, 128, 128, 0.08)",
            "fontSize": styling.get_typography_token("body_size", "0.95rem"),
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
    border_radius_px: int = _token_px_to_int(styling.get_radius_token("lg"), 15),
    header_font_weight: str = styling.get_typography_token("section_title_weight", "750"),
    header_font_size: str = styling.get_typography_token("section_title_size", "1.02rem"),
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

    card.style = styling.merge_style(
        styling.copy_style(getattr(card, "style", None)),
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
            child.style = styling.merge_style(
                styling.copy_style(getattr(child, "style", None)),
                build_workflow_section_header_style(
                    color_name=color_name,
                    accent_rgba=accent_rgba,
                    border_radius_px=border_radius_px,
                    style_overrides=header_style_overrides,
                ),
            )

        if isinstance(child, dbc.CardBody):
            child.style = styling.merge_style(
                styling.copy_style(getattr(child, "style", None)),
                build_workflow_section_body_style(),
            )

    return card


def build_labeled_row(
    *,
    label: str,
    component: Any,
    label_width_px: int = 320,
    gap_px: int = _token_px_to_int(styling.get_spacing_token("sm"), 12),
    margin_bottom_px: int = _token_px_to_int(styling.get_spacing_token("sm"), 12),
    align_items: str = "center",
    label_font_weight: str = styling.get_typography_token("label_weight", "500"),
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
    row_style = styling.merge_style(
        {
            "display": "flex",
            "alignItems": align_items,
            "gap": f"{int(gap_px)}px",
            "marginBottom": f"{int(margin_bottom_px)}px",
            "overflow": "visible",
            "fontSize": styling.get_typography_token("body_size", "0.95rem"),
        },
        row_style_overrides,
    )

    label_style = styling.merge_style(
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

    component_style = styling.merge_style(
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
    margin_top_px: int = _token_px_to_int(styling.get_spacing_token("sm"), 12),
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

    row_style = styling.merge_style(
        row_style,
        row_style_overrides,
    )

    label_style = styling.merge_style(
        {
            "width": f"{int(label_width_px)}px",
            "minWidth": f"{int(label_width_px)}px",
            "fontWeight": label_font_weight,
            "fontSize": styling.get_typography_token("body_size", "0.95rem"),
        },
        label_style_overrides,
    )

    control_wrapper_style = styling.merge_style(
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
    description_margin_bottom_px: int = _token_px_to_int(styling.get_spacing_token("sm"), 12),
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
        "marginBottom": styling.get_spacing_token("xs"),
    }

    if str(title_component).upper() == "H2":
        default_title_style.update(
            {
                "fontSize": styling.get_typography_token("heading_h2_size", "2rem"),
                "fontWeight": "600",
                "lineHeight": "1.2",
            }
        )

    elif str(title_component).upper() == "H4":
        default_title_style.update(
            {
                "fontSize": styling.get_typography_token("heading_h4_size", "1.25rem"),
                "fontWeight": "600",
                "lineHeight": "1.25",
            }
        )

    elif str(title_component).upper() == "H5":
        default_title_style.update(
            {
                "fontWeight": "600",
                "lineHeight": "1.3",
                "fontSize": styling.get_typography_token("heading_h5_size", "1.02rem"),
            }
        )

    children: list[Any] = [
        heading_factory(
            title,
            style=styling.merge_style(
                default_title_style,
                title_style_overrides,
            ),
        )
    ]

    if description:
        children.append(
            html.P(
                description,
                style=styling.merge_style(
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
        style=styling.copy_style(container_style),
    )
