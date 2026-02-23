import dash
from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc

from RosettaX.pages.scattering.base import BaseSection, SectionContext


class ExportSection(BaseSection):
    def __init__(self, *, context: SectionContext, debug_mode: bool = False) -> None:
        super().__init__(context=context, debug_mode=debug_mode)
        self.debug_out_id = f"{self.context.ids.page_name}-export-debug-out"

    def layout(self) -> dbc.Card:
        ids = self.context.ids
        debug_container_style = {"display": "block"} if self.debug_mode else {"display": "none"}

        return dbc.Card(
            [
                dbc.CardHeader("3. Export Size Calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        html.Div(
                            [
                                html.Button("Run Scatter Calibration", id=ids.run_calibration_btn, n_clicks=0),
                                dcc.Input(
                                    id=ids.export_file_name,
                                    type="text",
                                    placeholder="Enter file name",
                                    style={"width": "200px"},
                                ),
                                html.Button("Save/Export Scatter Calibration", id=ids.save_export_btn, n_clicks=0),
                                html.Br(),
                                html.Br(),
                                html.Div("Interpolate (optional):"),
                                dcc.Input(
                                    id=ids.interpolate_method,
                                    type="text",
                                    placeholder="Enter interpolation method",
                                    style={"width": "200px"},
                                ),
                                dcc.Input(
                                    id=ids.interpolate_au,
                                    type="number",
                                    placeholder="Enter AU value",
                                    style={"width": "200px"},
                                ),
                                dcc.Input(
                                    id=ids.interpolate_area,
                                    type="number",
                                    placeholder="Enter area value nm^2",
                                    style={"width": "200px"},
                                ),
                                html.Button("Interpolate Calibration", id=ids.interpolate_btn, n_clicks=0),
                                html.Br(),
                                html.Br(),
                                html.Div(id=ids.result_out),
                                html.Div(
                                    [
                                        html.Hr(),
                                        dbc.Alert("Debug outputs (ExportSection)", color="secondary", is_open=True),
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
                    id=f"collapse-{ids.page_name}-export",
                    is_open=True,
                ),
            ]
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids

        @callback(
            Output(ids.result_out, "children"),
            Output(self.debug_out_id, "children"),
            Input(ids.run_calibration_btn, "n_clicks"),
            State(ids.export_file_name, "value"),
            prevent_initial_call=True,
        )
        def run_scatter_calibration(n_clicks: int, file_name: str):
            if not n_clicks:
                return dash.no_update, ""

            name = (file_name or "").strip() or "<no file name>"
            msg = f"Scatter Calibration run {n_clicks} times with file name {name}."

            debug_text = ""
            if self.debug_mode:
                debug_text = f"run_clicks: {n_clicks}\nexport_file_name: {name}\n"

            return msg, debug_text
