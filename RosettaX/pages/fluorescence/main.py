import dash

from RosettaX.pages.fluorescence.ids import Ids
from RosettaX.pages.fluorescence import sections

class FluorescencePage():
    def __init__(self) -> None:
        self.ids = Ids()

        self.style = {
            "body_scroll": {"maxHeight": "80vh", "overflowY": "auto"},
            "graph": {"width": "100%", "height": "60vh"},
        }

        self.sections = [
            sections.LoadSection(page=self),
            sections.ScatteringSection(page=self),
            sections.PeaksSection(page=self),
            sections.CalibrationSection(page=self),
            sections.SaveSection(page=self)
        ]

        self.backend = None

    def register(self) -> None:
        """
        Register the page with Dash and all callbacks. The page must be registered before the layout can be accessed.

        Returns
        -------
        FluorescentCalibrationPage
            The page instance, returned for chaining purposes.
        """
        dash.register_page(__name__, path="/fluorescent_calibration", name="Fluorescence", order=1)

        for section in self.sections:
            section._register_callbacks()
        return self

    def layout(self) -> dash.html.Div:
        """
        The layout is defined here in the main page file since it composes sections that are defined across multiple files.

        Returns
        -------
        dash.html.Div
            The layout of the fluorescent calibration page, composed of multiple sections.
        """
        return dash.html.Div(
            [
                dash.dcc.Store(id=self.ids.Load.uploaded_fcs_path_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Calibration.calibration_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Scattering.threshold_store, storage_type="session"),
                dash.dcc.Store(id=self.ids.Fluorescence.hist_store, storage_type="memory"),
                dash.dcc.Store(id=self.ids.Fluorescence.source_channel_store, storage_type="memory"),
                dash.dcc.Store(id=self.ids.Fluorescence.peak_lines_store, storage_type="memory"),
                dash.html.H1("Fluorescent Calibration"),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections]
            ]
        )

layout = FluorescencePage().register().layout()