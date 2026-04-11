import dash

from RosettaX.pages.scattering.ids import Ids
from RosettaX.pages.scattering import sections

class ScatterCalibrationPage():
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
            sections.SaveSection(page=self)
        ]

    def register(self) -> "ScatterCalibrationPage":
        dash.register_page(__name__, path="/scatter_calibration", name="Scattering", order=2)

        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dash.html.Div:
        """
        The layout is defined here in the main page file since it composes sections that are defined across multiple files.

        Returns
        -------
        dash.html.Div
            The layout of the scatter calibration page, composed of multiple sections.
        """
        return dash.html.Div(
            [
                dash.html.H1("Scattering Calibration"),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections],
            ]
        )


layout = ScatterCalibrationPage().register().layout()