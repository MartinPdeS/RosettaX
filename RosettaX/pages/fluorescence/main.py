import dash
from typing import Self

from RosettaX.pages.fluorescence.ids import Ids
from RosettaX.pages.fluorescence import sections

class FluorescencePage:
    def __init__(self) -> None:
        self.ids = Ids()

        self.sections = [
            sections.Upload(page=self),
            sections.Peaks(page=self),
            sections.Calibration(page=self),
            sections.Save(page=self),
        ]

        self.backend = None

    def register_callbacks(self) -> Self:
        for section in self.sections:
            section.register_callbacks()
        return self

    def layout(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.dcc.Store(id=self.ids.Upload.uploaded_fcs_path_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Calibration.calibration_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Scattering.threshold_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Fluorescence.hist_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Fluorescence.source_channel_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Fluorescence.peak_lines_store, storage_type="session"),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections],
            ]
        )


_page = FluorescencePage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/fluorescence",
    name="Fluorescence",
    order=1,
    layout=layout,
)