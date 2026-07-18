"""Shared workflow section-card composition."""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling, ui_forms


def build_workflow_section_card(
    *,
    section_number: int,
    title: str,
    subtitle: str | None,
    body_children: list[Any],
    tooltip_text: str | None = None,
    tooltip_target_id: Any | None = None,
    tooltip_id: Any | None = None,
    color_name: str | None = None,
    style_overrides: dict[str, Any] | None = None,
) -> dbc.Card:
    """Build a standard workflow section card with an optional info tooltip."""
    resolved_color = color_name or styling.get_workflow_section_color(section_number)

    if tooltip_text is not None:
        if tooltip_target_id is None or tooltip_id is None:
            raise ValueError(
                "tooltip_target_id and tooltip_id are required with tooltip_text"
            )
        header = ui_forms.build_card_header_with_info(
            title=f"{section_number}. {title}",
            tooltip_target_id=tooltip_target_id,
            tooltip_id=tooltip_id,
            tooltip_text=tooltip_text,
            subtitle=subtitle,
            color_name=resolved_color,
        )
    else:
        header_children = [
            html.Div(
                f"{section_number}. {title}",
                style={"fontWeight": 750, "marginBottom": "0px"},
            )
        ]
        if subtitle:
            header_children.append(
                html.Div(
                    subtitle,
                    style=ui_forms.build_workflow_section_subtitle_style(),
                )
            )
        header = dbc.CardHeader(
            header_children,
            style=ui_forms.build_workflow_subpanel_header_style(
                color_name=resolved_color,
            ),
        )

    return dbc.Card(
        [
            header,
            dbc.CardBody(
                body_children,
                style=ui_forms.build_workflow_section_body_style(),
            ),
        ],
        style=styling.merge_style(
            ui_forms.build_workflow_section_card_style(color_name=resolved_color),
            style_overrides,
        ),
    )
