# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling


logger = logging.getLogger(__name__)


class Header:
    """
    Scattering calibration page header.

    Responsibilities
    ----------------
    - Explain the purpose of the scattering calibration page.
    - Show the calibration workflow before the user starts.
    - Clarify what each step produces.
    - Keep explanatory UX content separate from upload and processing logic.
    """

    def __init__(
        self,
        page: Any,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.card_color = card_color

        logger.debug(
            "Initialized Scattering Header section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering calibration header layout.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    self._build_title_block(),
                    html.Div(
                        style={
                            "height": "14px",
                        },
                    ),
                    self._build_workflow_steps(),
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

    def register_callbacks(self) -> None:
        """
        Header section has no callbacks.
        """
        return None

    def _build_title_block(self) -> html.Div:
        """
        Build the page title and short explanation.
        """
        return html.Div(
            [
                html.H3(
                    "Scattering calibration",
                    style={
                        "marginBottom": "6px",
                    },
                ),
            ]
        )

    def _build_workflow_steps(self) -> dbc.Row:
        """
        Build the visual step boxes.
        """
        steps = [
            {
                "number": "1",
                "title": "Upload bead FCS",
                "description": (
                    "Load the scattering bead file acquired on the instrument. "
                    "This file becomes the source for detector selection and peak detection."
                ),
            },
            {
                "number": "2",
                "title": "Detect peaks",
                "description": (
                    "Select the scattering detector channel, inspect the event distribution, "
                    "and detect the bead population peaks from the uploaded FCS file."
                ),
            },
            {
                "number": "3",
                "title": "Define Mie model parameters",
                "description": (
                    "Set the optical and particle model parameters, including wavelength, "
                    "medium refractive index, particle refractive index, and particle type."
                ),
            },
            {
                "number": "4",
                "title": "Compute coupling",
                "description": (
                    "Enter the particle diameters and compute the expected scattering "
                    "coupling from the selected Mie model."
                ),
            },
            {
                "number": "5",
                "title": "Create calibration",
                "description": (
                    "Match detected peak positions to the computed coupling values and fit "
                    "the scattering calibration relation."
                ),
            },
            {
                "number": "6",
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
                    self._build_step_card(
                        number=step["number"],
                        title=step["title"],
                        description=step["description"],
                    ),
                    xs=12,
                    md=6,
                    lg=4,
                    xl=2,
                    style={
                        "marginBottom": "10px",
                    },
                )
                for step in steps
            ],
            className="g-2",
        )

    def _build_step_card(
        self,
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
                                self.card_color,
                                0.12,
                            ),
                            "border": (
                                "1px solid "
                                f"{styling.build_rgba(self.card_color, 0.35)}"
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