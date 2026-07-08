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
                        "Convert arbitrary units of fluorescence intensity into standard units (ABC, ERF, or MESF)."
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
            "title": "Upload bead FCS file",
            "description": (
                "Load the FSC file of fluorescent reference beads. This FCS file becomes the source for parameter selection and detection of fluorescence peaks."
            ),
            "color_name": styling.get_workflow_section_color(1),
        },
        {
            "number": "2",
            "title": "Detect fluorescence peaks",
            "description": (
                "Select the parameter to calibrate, inspect the event distribution, and detect the fluorescence bead populations from the uploaded FCS file."
            ),
            "color_name": styling.get_workflow_section_color(2),
        },
        {
            "number": "3",
            "title": "Add standard units to calibration table",
            "description": (
                "Add standard units (ABC, ERF, MESF) to the calibration table. The provided values define the calibrated fluorescence scale."
            ),
            "color_name": styling.get_workflow_section_color(3),
        },
        {
            "number": "4",
            "title": "Create calibration",
            "description": (
                "Relate arbitrary units of fluorescence intensity to standard units by fitting the calibration table data."
            ),
            "color_name": styling.get_workflow_section_color(4),
        },
        {
            "number": "5",
            "title": "Save calibration",
            "description": (
                "Save the calibration for later reuse when applying it to uncalibrated FCS files."
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
