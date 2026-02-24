import dash
from dash import dcc, html

from RosettaX.pages.fluorescence import Sections, service
from RosettaX.pages.fluorescence.ids import Ids
from RosettaX.pages.fluorescence.base import BaseSection
from RosettaX.pages.fluorescence.load import LoadSection
from RosettaX.pages.fluorescence.scattering import ScatteringSection
from RosettaX.pages.fluorescence.fluorescence import FluorescenceSection
from RosettaX.pages.fluorescence.beads import BeadsSection
from RosettaX.pages.fluorescence.output import OutputSection
from RosettaX.pages.fluorescence.save import SaveSection

class FluorescentCalibrationPage(BaseSection, OutputSection, LoadSection, ScatteringSection, FluorescenceSection, BeadsSection, SaveSection):
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
        self.service = service.FluorescentCalibrationService(file_state=self.file_state)
        self.context = Sections.SectionContext(
            ids=self.ids,
            service=self.service,
            file_state=self.file_state,
            bead_table_columns=self.bead_table_columns,
            default_bead_rows=self.default_bead_rows,
            card_body_scroll=self.card_body_scroll,
            graph_style=self.graph_style,
        )

        self.context.backend = None

    def register(self) -> None:
        dash.register_page(__name__, path="/fluorescent_calibration", name="Fluorescent Calibration")
        self._load_register_callbacks()
        self._scattering_register_callbacks()
        self._fluorescence_register_callbacks()
        self._bead_register_callbacks()
        self._output_register_callbacks()
        self._save_register_callbacks()
        return self

    def layout(self) -> html.Div:
        ids = self.ids

        return html.Div(
            [
                dcc.Store(id=ids.uploaded_fcs_path_store, storage_type="session"),
                dcc.Store(id=ids.calibration_store, storage_type="session"),
                dcc.Store(id=ids.scattering_threshold_store, storage_type="session"),
                dcc.Store(id=ids.fluorescence_hist_store, storage_type="memory"),
                dcc.Store(id=ids.fluorescence_source_channel_store, storage_type="memory"),
                dcc.Store(id=self.ids.fluorescence_peak_lines_store, storage_type="data"),
                html.H1("Create and Save A New Fluorescent Calibration"),
                html.Br(),
                self._load_get_layout(),
                self._scattering_get_layout(),
                self._fluorescence_get_layout(),
                self._bead_get_layout(),
                self._output_get_layout(),
                self._save_get_layout(),

                # *(section.layout() for section in self.sections),
            ]
        )

        return self

layout = FluorescentCalibrationPage().register().layout()