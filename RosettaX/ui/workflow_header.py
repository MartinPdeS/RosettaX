"""Shared headers used by multi-step RosettaX workflow pages."""

from dataclasses import dataclass
from typing import Any, Sequence

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling, ui_forms


@dataclass(frozen=True)
class WorkflowStep:
    """Description of one step shown in a workflow page header."""

    number: str
    title: str
    description: str
    color_name: str


def build_workflow_page_header(
    *,
    title: str,
    description: str,
    steps: Sequence[WorkflowStep],
    card_color: str | None = None,
    alert: Any | None = None,
    column_kwargs: dict[str, Any] | None = None,
    style_overrides: dict[str, Any] | None = None,
) -> dbc.Card:
    """Build the standard explanatory header for a workflow page."""
    resolved_column_kwargs = {
        "xs": 12,
        "md": 6,
        "lg": 4,
        "style": {"marginBottom": "10px"},
    }
    if column_kwargs:
        resolved_column_kwargs.update(column_kwargs)

    children: list[Any] = [
        ui_forms.build_section_intro(
            title=title,
            title_component="H2",
            description=description,
        ),
    ]
    if alert is not None:
        children.append(alert)

    children.append(
        dbc.Row(
            [
                dbc.Col(
                    _build_step_card(step),
                    **resolved_column_kwargs,
                )
                for step in steps
            ],
            className="g-2",
        )
    )

    return dbc.Card(
        dbc.CardBody(
            children,
            style=ui_forms.build_workflow_section_body_style(),
        ),
        style=styling.merge_style(
            ui_forms.build_workflow_section_card_style(
                color_name=card_color or styling.get_workflow_page_header_color(),
            ),
            {"marginBottom": "16px"},
            style_overrides,
        ),
    )


def _build_step_card(step: WorkflowStep) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    step.number,
                    style={
                        "width": "28px",
                        "height": "28px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "700",
                        "fontSize": "0.9rem",
                        "backgroundColor": styling.build_rgba(step.color_name, 0.12),
                        "border": f"1px solid {styling.build_rgba(step.color_name, 0.35)}",
                        "marginBottom": "10px",
                    },
                ),
                html.H6(step.title, style={"marginBottom": "6px"}),
                html.P(
                    step.description,
                    style={
                        "marginBottom": "0px",
                        "fontSize": "0.86rem",
                        "opacity": 0.78,
                    },
                ),
            ],
            style={"height": "100%", "padding": "14px"},
        ),
        style=ui_forms.build_workflow_subpanel_card_style(
            color_name=step.color_name,
            style_overrides={"height": "100%"},
        ),
    )
