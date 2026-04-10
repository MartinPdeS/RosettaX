# -*- coding: utf-8 -*-

from dash import html

class HeaderSection:
    def __init__(self, page) -> None:
        self.page = page


    def get_layout(self) -> html.Div:
        return html.Div(
            [
                html.H1("Apply Calibration", style={"marginBottom": "6px"}),
                html.P(
                    "Select a saved calibration and apply it to a file.",
                    style={"opacity": 0.85, "marginBottom": "0px"},
                ),
            ],
            id=self.page.ids.Header.container,
            style={"paddingTop": "24px"},
        )

    def _register_callbacks(self) -> None:
        pass