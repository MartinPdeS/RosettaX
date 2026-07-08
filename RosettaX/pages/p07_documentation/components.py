# -*- coding: utf-8 -*-

from typing import Optional

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms


def build_documentation_container(
    children: list,
) -> dbc.Container:
    """
    Build the shared page container used by documentation pages.
    """
    return dbc.Container(
        children,
        fluid=True,
        style={
            "paddingLeft": "0px",
            "paddingRight": "0px",
            "paddingTop": "12px",
            "paddingBottom": "40px",
        },
    )


def build_documentation_hero(
    *,
    hero_id: str,
    title: str,
    description: str,
) -> dbc.Card:
    """
    Build the shared hero section for documentation pages.
    """
    card = dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    id=hero_id,
                    style={
                        "fontWeight": "800",
                        "fontSize": "2.45rem",
                        "lineHeight": "1.05",
                        "marginBottom": "10px",
                    },
                ),
                html.Div(
                    description,
                    style={
                        "fontSize": "1.05rem",
                        "opacity": 0.84,
                        "maxWidth": "980px",
                        "marginBottom": "0px",
                    },
                ),
            ],
            style={"padding": "26px"},
        )
    )

    return ui_forms.apply_workflow_section_card_style(
        card=card,
        header_font_weight="750",
        header_font_size="1.02rem",
    )


def build_documentation_card(
    *,
    title: str,
    subtitle: str,
    body: list,
    min_height: Optional[str] = "252px",
) -> dbc.Card:
    """
    Build one shared documentation content card.
    """
    card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(title, style={"fontWeight": "750", "fontSize": "1.02rem"}),
                    html.Div(
                        subtitle,
                        style={
                            "fontSize": "0.86rem",
                            "opacity": 0.76,
                            "marginTop": "3px",
                        },
                    ),
                ]
            ),
            dbc.CardBody(
                body,
                style={"padding": "16px"},
            ),
        ],
        style={
            "height": "100%",
            "minHeight": min_height or "252px",
        },
    )

    return ui_forms.apply_workflow_section_card_style(
        card=card,
        header_font_weight="750",
        header_font_size="1.02rem",
    )


def build_documentation_link_chip(
    *,
    label: str,
    href: str,
) -> html.A:
    """
    Build one compact documentation navigation chip.
    """
    return html.A(
        label,
        href=href,
        style={
            "textDecoration": "none",
            "fontWeight": "600",
            "padding": "8px 11px",
            "borderRadius": "10px",
            "border": "1px solid rgba(13, 110, 253, 0.14)",
            "background": "rgba(13, 110, 253, 0.04)",
            "display": "inline-flex",
            "alignItems": "center",
            "lineHeight": "1.2",
        },
    )


def build_documentation_cta_card(
    *,
    title: str,
    summary: str,
    href: str,
    link_label: str = "Open page",
) -> dbc.Card:
    """
    Build one linked deep-dive card for the documentation hub.
    """
    return build_documentation_card(
        title=title,
        subtitle=summary,
        body=[
            html.A(
                link_label,
                href=href,
                style={
                    "display": "inline-flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "padding": "9px 12px",
                    "borderRadius": "10px",
                    "border": "1px solid rgba(13, 110, 253, 0.18)",
                    "background": "rgba(13, 110, 253, 0.06)",
                    "fontWeight": "700",
                    "textDecoration": "none",
                    "width": "fit-content",
                },
            ),
        ],
        min_height="180px",
    )
