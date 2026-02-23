import dash
from dash import html

from RosettaX.pages.scattering import Sections


class ScatterCalibrationPage:
    def __init__(self) -> None:
        self.ids = Sections.ScatterCalibrationIds()

        self.scroll_style = {"maxHeight": "60vh", "overflowY": "auto"}
        self.row_style = {"display": "flex", "alignItems": "center", "gap": "10px", "marginTop": "8px"}
        self.label_style = {"minWidth": "160px"}

        self.context = Sections.SectionContext(
            ids=self.ids,
            scroll_style=self.scroll_style,
            row_style=self.row_style,
            label_style=self.label_style,
        )

        debug_mode = False

        self.sections: list[Sections.BaseSection] = [
            Sections.FlowDataSection(context=self.context, debug_mode=debug_mode),
            Sections.ExampleParametersSection(context=self.context, debug_mode=debug_mode),
            Sections.ExportSection(context=self.context, debug_mode=debug_mode),
            Sections.GraphSection(context=self.context, debug_mode=debug_mode),
        ]

    def register(self) -> "ScatterCalibrationPage":
        dash.register_page(__name__, path="/scatter_calibration", name="Scatter Calibration")
        self._register_callbacks()
        return self

    def layout(self) -> html.Div:
        return html.Div(
            [
                html.H1("Create and Save A New Scatter Calibration"),
                html.Br(),
                *(section.layout() for section in self.sections),
            ]
        )

    def _register_callbacks(self) -> None:
        for section in self.sections:
            section.register_callbacks()


layout = ScatterCalibrationPage().register().layout()