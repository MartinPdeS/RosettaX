import dash

from RosettaX.pages.scattering.ids import Ids
from RosettaX.pages.scattering import sections

class ScatterCalibrationPage(
    sections.LoadSection,
    sections.ParametersSection,
    sections.ExportSection
):
    def __init__(self) -> None:
        self.ids = Ids()

        self.scroll_style = {"maxHeight": "60vh", "overflowY": "auto"}
        self.row_style = {"display": "flex", "alignItems": "center", "gap": "10px", "marginTop": "8px"}
        self.label_style = {"minWidth": "160px"}

        self.card_body_scroll = {"maxHeight": "60vh", "overflowY": "auto"}
        self.graph_style = {"width": "100%", "height": "45vh"}

    def register(self) -> "ScatterCalibrationPage":
        dash.register_page(__name__, path="/scatter_calibration", name="Scattering", order=2)
        self._load_register_callbacks()
        self._parameters_register_callbacks()
        # self._export_register_callbacks()
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
                self._load_get_layout(),
                self._parameters_get_layout(),
                self._export_get_layout(),
            ]
        )


layout = ScatterCalibrationPage().register().layout()