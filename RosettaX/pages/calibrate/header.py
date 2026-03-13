# -*- coding: utf-8 -*-

from dash import html

from RosettaX.pages.calibrate.ids import Ids


class HeaderSection:
    def get_layout(self) -> html.Div:
        return html.Div(
            [
                html.H1("Apply Calibration", style={"marginBottom": "6px"}),
                html.P(
                    "Select a saved calibration and apply it to a file.",
                    style={"opacity": 0.85, "marginBottom": "0px"},
                ),
            ],
            id=Ids.Header.container,
            style={"paddingTop": "24px"},
        )