# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence calibration header layout.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                _build_title_block(),
                html.Div(
                    style={
                        "height": "14px",
                    },
                ),
                _build_workflow_steps(section),
                html.Div(
                    style={
                        "height": "12px",
                    },
                ),
            ]
        ),
        style={
            "marginBottom": "16px",
        },
    )


def _build_title_block() -> html.Div:
    """
    Build the page title and short explanation.
    """
    return html.Div(
        [
            html.H3(
                "Fluorescence calibration",
                style={
                    "marginBottom": "6px",
                },
            ),
        ]
    )


def _build_workflow_steps(section) -> dbc.Row:
    """
    Build the visual step boxes.
    """
    steps = [
        {
            "number": "1",
            "title": "Upload bead FCS",
            "description": (
                "Load the fluorescence bead file acquired on the instrument. "
                "This file becomes the source for detector selection and peak detection."
            ),
        },
        {
            "number": "2",
            "title": "Detect peaks",
            "description": (
                "Select the fluorescence detector channel, inspect the event distribution, "
                "and detect the bead population peaks from the uploaded FCS file."
            ),
        },
        {
            "number": "3",
            "title": "Enter MESF values",
            "description": (
                "Enter the known MESF values for the bead populations. These values "
                "define the calibrated fluorescence scale."
            ),
        },
        {
            "number": "4",
            "title": "Create calibration",
            "description": (
                "Match detected peak positions to the entered MESF values and fit the "
                "fluorescence calibration relation."
            ),
        },
        {
            "number": "5",
            "title": "Save calibration",
            "description": (
                "Save the fitted calibration so it can be reused later when applying "
                "calibration to experimental FCS files."
            ),
        },
    ]

    return dbc.Row(
        [
            dbc.Col(
                _build_step_card(
                    section=section,
                    number=step["number"],
                    title=step["title"],
                    description=step["description"],
                ),
                xs=12,
                md=6,
                xl=True,
                style={
                    "marginBottom": "10px",
                },
            )
            for step in steps
        ],
        className="g-2",
    )


def _build_step_card(
    section,
    *,
    number: str,
    title: str,
    description: str,
) -> dbc.Card:
    """
    Build one workflow step card.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    number,
                    style={
                        "width": "28px",
                        "height": "28px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "700",
                        "fontSize": "0.9rem",
                        "backgroundColor": styling.build_rgba(
                            section.card_color,
                            0.12,
                        ),
                        "border": (
                            "1px solid "
                            f"{styling.build_rgba(section.card_color, 0.35)}"
                        ),
                        "marginBottom": "10px",
                    },
                ),
                html.H6(
                    title,
                    style={
                        "marginBottom": "6px",
                    },
                ),
                html.P(
                    description,
                    style={
                        "marginBottom": "0px",
                        "fontSize": "0.86rem",
                        "opacity": 0.78,
                    },
                ),
            ],
            style={
                "height": "100%",
                "padding": "14px",
            },
        ),
        style={
            "height": "100%",
            "borderRadius": "12px",
        },
    )
