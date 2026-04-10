
import dash
import dash_bootstrap_components as dbc


class CalibrationSection():

    def __init__(self, page) -> None:
        self.page = page

    def _get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("3. Calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        dash.html.Div(
                            [
                                dash.html.Button("Run Scatter Calibration", id=self.page.ids.Export.run_calibration_btn, n_clicks=0),
                                dash.dcc.Input(
                                    id=self.page.ids.Export.file_name,
                                    type="text",
                                    placeholder="Enter file name",
                                    style={"width": "200px"},
                                ),
                                dash.html.Button("Save/Export Scatter Calibration", id=self.page.ids.Export.save_export_btn, n_clicks=0),
                                dash.html.Br(),
                                dash.html.Br(),
                                dash.html.Div("Interpolate (optional):"),
                                dash.dcc.Input(
                                    id=self.page.ids.Export.interpolate_method,
                                    type="text",
                                    placeholder="Enter interpolation method",
                                    style={"width": "200px"},
                                ),
                                dash.dcc.Input(
                                    id=self.page.ids.Export.interpolate_au,
                                    type="number",
                                    placeholder="Enter AU value",
                                    style={"width": "200px"},
                                ),
                                dash.dcc.Input(
                                    id=self.page.ids.Export.interpolate_area,
                                    type="number",
                                    placeholder="Enter area value nm^2",
                                    style={"width": "200px"},
                                ),
                                dash.html.Button("Interpolate Calibration", id=self.page.ids.Export.interpolate_btn, n_clicks=0),
                                dash.html.Br(),
                                dash.html.Br(),
                                dash.html.Div(id=self.page.ids.Export.result_out),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "6px",
                                **self.page.style["body_scroll"],
                            },
                        )
                    ),
                    id=self.page.ids.Export.collapse,
                    is_open=True,
                ),
            ]
        )

    def _register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Export.result_out, "children"),
            dash.Input(self.page.ids.Export.run_calibration_btn, "n_clicks"),
            dash.State(self.page.ids.Export.file_name, "value"),
            prevent_initial_call=True,
        )
        def run_scatter_calibration(n_clicks: int, file_name: str):
            if not n_clicks:
                return dash.no_update, ""

            name = (file_name or "").strip() or "<no file name>"
            return f"Scatter Calibration run {n_clicks} times with file name {name}."
