from typing import Optional

from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc

from RosettaX.pages import styling
from RosettaX.pages.scattering.base import BaseSection, SectionContext



class FlowDataSection(BaseSection):
    def __init__(self, *, context: SectionContext, debug_mode: bool = False) -> None:
        super().__init__(context=context, debug_mode=debug_mode)
        self.debug_out_id = f"{self.context.ids.page_name}-flow-debug-out"

    def layout(self) -> dbc.Card:
        ids = self.context.ids

        debug_container_style = {"display": "block"} if self.debug_mode else {"display": "none"}

        return dbc.Card(
            [
                dbc.CardHeader("1. Select Flow Cytometry Data and Parameters"),
                dbc.Collapse(
                    dbc.CardBody(
                        html.Div(
                            [
                                dcc.Upload(
                                    id=ids.upload,
                                    children=html.Div(["Drag and Drop or ", html.A("Select File")]),
                                    style=styling.UPLOAD,
                                    multiple=False,
                                ),
                                self._inline_row(
                                    "Flow Cytometry Name:",
                                    html.Div(id=ids.flow_file_label, style={"flex": "1 1 200px"}),
                                    margin_top=False,
                                ),
                                self._inline_row(
                                    "Flow Cytometry Type:",
                                    dcc.Dropdown(id=ids.flow_type_dropdown, value=None, style={"width": "250px"}),
                                ),
                                self._inline_row(
                                    "Forward Scatter:",
                                    dcc.Dropdown(id=ids.fsc_dropdown, value=None, style={"width": "250px"}),
                                ),
                                self._inline_row(
                                    "Wavelength (nm):",
                                    dcc.Input(
                                        id=ids.fsc_wavelength,
                                        type="number",
                                        value="",
                                        style={"width": "120px"},
                                    ),
                                ),
                                self._inline_row(
                                    "Side Scatter:",
                                    dcc.Dropdown(id=ids.ssc_dropdown, value=None, style={"width": "250px"}),
                                ),
                                self._inline_row(
                                    "Wavelength (nm):",
                                    dcc.Input(
                                        id=ids.ssc_wavelength,
                                        type="number",
                                        value="",
                                        style={"width": "120px"},
                                    ),
                                ),
                                self._inline_row(
                                    "Green fluorescence:",
                                    dcc.Dropdown(
                                        id=ids.green_fluorescence_dropdown,
                                        value=None,
                                        style={"width": "250px"},
                                    ),
                                ),
                                html.Div(
                                    [
                                        html.Br(),
                                        html.Button("Calibrate", id=ids.calibrate_flow_btn, n_clicks=0),
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Hr(),
                                        dbc.Alert("Debug outputs (FlowDataSection)", color="secondary", is_open=True),
                                        html.Pre(id=self.debug_out_id, style={"whiteSpace": "pre-wrap"}),
                                    ],
                                    style=debug_container_style,
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "6px",
                                **self.context.scroll_style,
                            },
                        )
                    ),
                    id=f"collapse-{ids.page_name}-flow",
                    is_open=True,
                ),
            ]
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids

        @callback(
            Output(ids.flow_file_label, "children"),
            Output(self.debug_out_id, "children"),
            Input(ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def show_selected_filename(filename: Optional[str]):
            if not filename:
                return "", ""

            debug_text = ""
            if self.debug_mode:
                debug_text = f"filename: {filename}\n"

            return str(filename), debug_text
