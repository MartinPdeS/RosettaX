# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling


class CrossCalibrationPage:
    """
    Placeholder page for upcoming cross calibration workflows.
    """

    def __init__(self) -> None:
        self.style = styling.PAGE

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                html.H2("Cross Calibration", style={"marginBottom": "12px"}),
                html.P(
                    "This section is under active development and will host future "
                    "cross-calibration workflows.",
                    style={"marginBottom": "8px"},
                ),
                html.P(
                    "Planned scope: combine fluorescence and scattering calibration "
                    "artifacts into shared cross-calibration models.",
                    style={"opacity": 0.78, "marginBottom": "0"},
                ),
            ],
            fluid=True,
            style=self.style,
        )


_page = CrossCalibrationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/cross-calibration",
    name="Cross Calibration",
    order=3,
    layout=layout,
)
