
import dash
import dash_bootstrap_components as dbc


class ExportSection():

    def _export_get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("3. Export Size Calibration"),
                dbc.Collapse(
                    dbc.CardBody(
                        dash.html.Div(
                            [
                                dash.html.Button("Run Scatter Calibration", id=self.ids.run_calibration_btn, n_clicks=0),
                                dash.dcc.Input(
                                    id=self.ids.export_file_name,
                                    type="text",
                                    placeholder="Enter file name",
                                    style={"width": "200px"},
                                ),
                                dash.html.Button("Save/Export Scatter Calibration", id=self.ids.save_export_btn, n_clicks=0),
                                dash.html.Br(),
                                dash.html.Br(),
                                dash.html.Div("Interpolate (optional):"),
                                dash.dcc.Input(
                                    id=self.ids.interpolate_method,
                                    type="text",
                                    placeholder="Enter interpolation method",
                                    style={"width": "200px"},
                                ),
                                dash.dcc.Input(
                                    id=self.ids.interpolate_au,
                                    type="number",
                                    placeholder="Enter AU value",
                                    style={"width": "200px"},
                                ),
                                dash.dcc.Input(
                                    id=self.ids.interpolate_area,
                                    type="number",
                                    placeholder="Enter area value nm^2",
                                    style={"width": "200px"},
                                ),
                                dash.html.Button("Interpolate Calibration", id=self.ids.interpolate_btn, n_clicks=0),
                                dash.html.Br(),
                                dash.html.Br(),
                                dash.html.Div(id=self.ids.result_out),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "6px",
                                **self.scroll_style,
                            },
                        )
                    ),
                    id=f"collapse-{self.ids.page_name}-export",
                    is_open=True,
                ),
            ]
        )

    def _export_register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.ids.result_out, "children"),
            dash.Input(self.ids.run_calibration_btn, "n_clicks"),
            dash.State(self.ids.export_file_name, "value"),
            prevent_initial_call=True,
        )
        def run_scatter_calibration(n_clicks: int, file_name: str):
            if not n_clicks:
                return dash.no_update, ""

            name = (file_name or "").strip() or "<no file name>"
            return f"Scatter Calibration run {n_clicks} times with file name {name}."
