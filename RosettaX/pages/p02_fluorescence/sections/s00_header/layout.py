# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling, ui_forms


def get_layout(section) -> dbc.Card:
    """
    Build the fluorescence calibration header layout.
    """
    return dbc.Card(
        dbc.CardBody(
            [
                ui_forms.build_section_intro(
                    title="Fluorescence calibration",
                    title_component="H2",
                    description=(
                        "Create a fluorescence calibration from bead FCS data by "
                        "detecting bead populations, entering known MESF references, "
                        "fitting the calibration relation, and saving the result for "
                        "reuse."
                    ),
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            _build_step_card(
                                number=step["number"],
                                title=step["title"],
                                description=step["description"],
                                color_name=step["color_name"],
                            ),
                            xs=12,
                            md=6,
                            xl=True,
                            style={
                                "marginBottom": "10px",
                            },
                        )
                        for step in _build_steps()
                    ],
                    className="g-2",
                ),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        ),
        style={
            **ui_forms.build_workflow_section_card_style(
                color_name=section.card_color,
            ),
            "marginBottom": "16px",
        },
    )


def _build_steps() -> list[dict[str, str]]:
    """
    Build the workflow step metadata.
    """
    return [
        {
            "number": "1",
            "title": "Upload bead FCS",
            "description": (
                "Load the fluorescence bead file acquired on the instrument. "
                "This file becomes the source for detector selection and peak detection."
            ),
            "color_name": styling.get_workflow_section_color(1),
        },
        {
            "number": "2",
            "title": "Detect peaks",
            "description": (
                "Select the fluorescence detector channel, inspect the event distribution, "
                "and detect the bead population peaks from the uploaded FCS file."
            ),
            "color_name": styling.get_workflow_section_color(2),
        },
        {
            "number": "3",
            "title": "Enter MESF values",
            "description": (
                "Enter the known MESF values for the bead populations. These values "
                "define the calibrated fluorescence scale."
            ),
            "color_name": styling.get_workflow_section_color(3),
        },
        {
            "number": "4",
            "title": "Create calibration",
            "description": (
                "Match detected peak positions to the entered MESF values and fit the "
                "fluorescence calibration relation."
            ),
            "color_name": styling.get_workflow_section_color(4),
        },
        {
            "number": "5",
            "title": "Save calibration",
            "description": (
                "Save the fitted calibration so it can be reused later when applying "
                "calibration to experimental FCS files."
            ),
            "color_name": styling.get_workflow_section_color(5),
        },
    ]


def _build_step_card(
    *,
    number: str,
    title: str,
    description: str,
    color_name: str,
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
                            color_name,
                            0.12,
                        ),
                        "border": f"1px solid {styling.build_rgba(color_name, 0.35)}",
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
        style=ui_forms.build_workflow_subpanel_card_style(
            color_name=color_name,
            style_overrides={
                "height": "100%",
            },
        ),
    )
