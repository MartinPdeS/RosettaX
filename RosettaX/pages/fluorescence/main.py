import dash
from dash import dcc, html

from RosettaX.pages.fluorescence import service
from RosettaX.pages.fluorescence.ids import Ids
from RosettaX.pages.fluorescence.load import LoadSection
from RosettaX.pages.fluorescence.scattering import ScatteringSection
from RosettaX.pages.fluorescence.peaks import PeaksSection
from RosettaX.pages.fluorescence.save import SaveSection
from RosettaX.pages.fluorescence.calibration import CalibrationSection

class FluorescentCalibrationPage(LoadSection, ScatteringSection, PeaksSection, SaveSection, CalibrationSection):
    def __init__(self) -> None:
        self.ids = Ids()

        self.bead_table_columns = [
            {"name": "Intensity (MESF)", "id": "col1", "editable": True},
            {"name": "Intensity (a.u.)", "id": "col2", "editable": True},
        ]
        self.default_bead_rows = [{"col1": "", "col2": ""} for _ in range(3)]

        self.card_body_scroll = {"maxHeight": "60vh", "overflowY": "auto"}
        self.graph_style = {"width": "100%", "height": "45vh"}

        self.scatter_keywords = [
            "scatter",
            "fsc",
            "ssc",
            "sals",
            "lals",
            "mals",
            "405ls",
            "488ls",
            "638ls",
            "fs-a",
            "fs-h",
            "ss-a",
            "ss-h",
        ]

        self.non_valid_keywords = ["time", "width", "diameter", "cross section"]

        self.file_state = service.FileStateRefresher(
            scatter_keywords=self.scatter_keywords,
            non_valid_keywords=self.non_valid_keywords,
        )

        self.backend = None

    def register(self) -> None:
        """
        Register the page with Dash and all callbacks. The page must be registered before the layout can be accessed.

        Returns
        -------
        FluorescentCalibrationPage
            The page instance, returned for chaining purposes.
        """
        dash.register_page(__name__, path="/fluorescent_calibration", name="Fluorescence")
        self._load_register_callbacks()
        self._scattering_register_callbacks()
        self._fluorescence_register_callbacks()
        self._calibration_register_callbacks()
        self._save_register_callbacks()
        return self

    def layout(self) -> html.Div:
        """
        The layout is defined here in the main page file since it composes sections that are defined across multiple files.

        Returns
        -------
        html.Div
            The layout of the fluorescent calibration page, composed of multiple sections.
        """
        return html.Div(
            [
                dcc.Store(id=self.ids.Load.uploaded_fcs_path_store, storage_type="session"),
                dcc.Store(id=self.ids.Calibration.calibration_store, storage_type="session"),
                dcc.Store(id=self.ids.Scattering.threshold_store, storage_type="session"),
                dcc.Store(id=self.ids.Fluorescence.hist_store, storage_type="memory"),
                dcc.Store(id=self.ids.Fluorescence.source_channel_store, storage_type="memory"),
                dcc.Store(id=self.ids.Fluorescence.peak_lines_store, storage_type="data"),
                html.H1("Fluorescent Calibration"),
                html.Br(),
                self._load_get_layout(),
                self._scattering_get_layout(),
                self._fluorescence_get_layout(),
                self._calibration_get_layout(),
                self._save_get_layout(),
            ]
        )

        return self

layout = FluorescentCalibrationPage().register().layout()