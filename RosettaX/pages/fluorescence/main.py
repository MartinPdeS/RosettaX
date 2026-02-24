import dash
from dash import dcc, html

from RosettaX.pages.fluorescence import Sections, helper
from RosettaX.pages.fluorescence.ids import Ids

class FluorescentCalibrationPage:
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

        self.file_state = helper.FileStateRefresher(
            scatter_keywords=self.scatter_keywords,
            non_valid_keywords=self.non_valid_keywords,
        )
        self.service = helper.FluorescentCalibrationService(file_state=self.file_state)
        self.context = Sections.SectionContext(
            ids=self.ids,
            service=self.service,
            file_state=self.file_state,
            bead_table_columns=self.bead_table_columns,
            default_bead_rows=self.default_bead_rows,
            card_body_scroll=self.card_body_scroll,
            graph_style=self.graph_style,
        )

        self.sections: list[Sections.BaseSection] = [
            Sections.LoadSection(context=self.context),
            Sections.ScatteringSection(context=self.context),
            Sections.FluorescenceSection(context=self.context),
            Sections.BeadsSection(context=self.context),
            Sections.OutputSection(context=self.context),
            Sections.SaveSection(context=self.context),
        ]

    def register(self) -> None:
        dash.register_page(__name__, path="/fluorescent_calibration", name="Fluorescent Calibration")
        self._register_callbacks()

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
                html.H1("Create and Save A New Fluorescent Calibration"),
                html.Br(),
                *(section.layout() for section in self.sections),
            ]
        )

        return self

    def _register_callbacks(self) -> None:
        for section in self.sections:
            section.register_callbacks()



# layout = FluorescentCalibrationPage().register().layout()
_page = FluorescentCalibrationPage().register()

def layout():
    return _page.layout()