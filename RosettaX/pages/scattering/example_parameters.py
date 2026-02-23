from typing import Any

from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc

from RosettaX.pages.scattering.base import BaseSection, SectionContext


class ExampleParametersSection(BaseSection):
    def __init__(self, *, context: SectionContext, debug_mode: bool = False) -> None:
        super().__init__(context=context, debug_mode=debug_mode)
        self.debug_out_id = f"{self.context.ids.page_name}-example-debug-out"

    def layout(self) -> dbc.Card:
        ids = self.context.ids
        debug_container_style = {"display": "block"} if self.debug_mode else {"display": "none"}

        return dbc.Card(
            [
                dbc.CardHeader("2. Set Example Calculation Parameters"),
                dbc.Collapse(
                    dbc.CardBody(
                        html.Div(
                            [
                                self._inline_row(
                                    "Mie Model:",
                                    dcc.RadioItems(
                                        ["Solid Sphere", "Core/Shell Sphere"],
                                        "Solid Sphere",
                                        id=ids.mie_model,
                                        inline=True,
                                        labelClassName="me-3",
                                    ),
                                    margin_top=False,
                                ),
                                self._inline_row(
                                    "Medium Refractive Index:",
                                    dcc.RadioItems(
                                        ["water", "PBS", "other"],
                                        "water",
                                        id=ids.medium_index,
                                        inline=True,
                                        labelClassName="me-3",
                                    ),
                                ),
                                self._inline_row(
                                    "Custom Refractive Index:",
                                    dcc.Input(
                                        id=ids.custom_medium_index,
                                        type="number",
                                        placeholder="Custom Refractive Index",
                                        style={"width": "160px"},
                                    ),
                                ),
                                self._inline_row(
                                    "Particle Core Refractive Index:",
                                    dcc.Input(
                                        id=ids.core_index,
                                        type="number",
                                        placeholder="Particle Core Refractive Index",
                                        value=1.38,
                                        min=1.0,
                                        max=2.5,
                                        step=0.001,
                                        style={"width": "160px"},
                                    ),
                                ),
                                self._inline_row(
                                    "Particle Shell Refractive Index:",
                                    dcc.Input(
                                        id=ids.shell_index,
                                        type="number",
                                        placeholder="Particle Shell Refractive Index",
                                        value=1.48,
                                        min=1.0,
                                        max=2.5,
                                        step=0.001,
                                        style={"width": "160px"},
                                    ),
                                ),
                                self._inline_row(
                                    "Particle Shell Thickness (nm):",
                                    dcc.Input(
                                        id=ids.shell_thickness,
                                        type="number",
                                        placeholder="Particle Shell Thickness (nm)",
                                        value=6,
                                        min=0,
                                        step=1,
                                        style={"width": "120px"},
                                    ),
                                ),
                                html.Button("Calibrate", id=ids.calibrate_example_btn, n_clicks=0, style={"marginTop": "8px"}),
                                html.Div(
                                    [
                                        html.Hr(),
                                        dbc.Alert("Debug outputs (ExampleParametersSection)", color="secondary", is_open=True),
                                        html.Pre(id=self.debug_out_id, style={"whiteSpace": "pre-wrap"}),
                                    ],
                                    style=debug_container_style,
                                ),
                            ]
                        ),
                        style=self.context.scroll_style,
                    ),
                    id=f"collapse-{ids.page_name}-example",
                    is_open=True,
                ),
            ]
        )

    def register_callbacks(self) -> None:
        ids = self.context.ids

        @callback(
            Output(self.debug_out_id, "children"),
            Input(ids.calibrate_example_btn, "n_clicks"),
            State(ids.mie_model, "value"),
            State(ids.medium_index, "value"),
            State(ids.custom_medium_index, "value"),
            State(ids.core_index, "value"),
            State(ids.shell_index, "value"),
            State(ids.shell_thickness, "value"),
            prevent_initial_call=True,
        )
        def debug_example_params(
            n_clicks: int,
            mie_model: Any,
            medium_index: Any,
            custom_medium_index: Any,
            core_index: Any,
            shell_index: Any,
            shell_thickness: Any,
        ):
            if not self.debug_mode:
                return ""

            if not n_clicks:
                return ""

            return (
                f"mie_model: {mie_model}\n"
                f"medium_index: {medium_index}\n"
                f"custom_medium_index: {custom_medium_index}\n"
                f"core_index: {core_index}\n"
                f"shell_index: {shell_index}\n"
                f"shell_thickness: {shell_thickness}\n"
            )

