import dash

from RosettaX.pages.scattering.ids import Ids
from RosettaX.pages.scattering import sections


class ScatterCalibrationPage:
    def __init__(self) -> None:
        self.ids = Ids()

        self.style = {
            "body_scroll": {"maxHeight": "80vh", "overflowY": "auto"},
            "graph": {"width": "100%", "height": "60vh"},
            "row": {"display": "flex", "alignItems": "center", "gap": "10px", "marginTop": "8px"},
            "label": {"minWidth": "160px"},
            "card_body_scroll": {"maxHeight": "60vh", "overflowY": "auto"},
        }

        self.sections = [
            sections.LoadSection(page=self),
            sections.ScatteringSection(page=self),
            sections.ParametersSection(page=self),
            sections.CalibrationSection(page=self),
            sections.SaveSection(page=self),
        ]

    def register_callbacks(self) -> "ScatterCalibrationPage":
        for section in self.sections:
            section.register_callbacks()
        return self

    def layout(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H1("Scattering Calibration"),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections],
            ]
        )


_page = ScatterCalibrationPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/scattering",
    name="Scattering",
    order=2,
    layout=layout,
)