# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any
import dash
import dash_bootstrap_components as dbc


@dataclass(frozen=True)
class ApplyCalibrationResult:
    status: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (self.status,)


class ApplySection:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("3. Apply"),
                dbc.CardBody(
                    [
                        dbc.Button(
                            "Apply",
                            id=self.page.ids.Apply.apply_button,
                            n_clicks=0,
                            color="primary",
                        ),
                        dash.html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Status will appear here.",
                            id=self.page.ids.Apply.status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )

    def _register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Apply.status, "children"),
            dash.Input(self.page.ids.Apply.apply_button, "n_clicks"),
            dash.State(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.State(self.page.ids.ChannelPicker.dropdown, "value"),
            prevent_initial_call=True,
        )
        def apply_calibration(n_clicks: int, selected_calibration: Any, target_channel: Any) -> tuple:
            if not selected_calibration:
                return ApplyCalibrationResult(status="Select a calibration first.").to_tuple()

            if not target_channel:
                return ApplyCalibrationResult(status="Select a target channel first.").to_tuple()

            return ApplyCalibrationResult(
                status=f"Apply requested using calibration {selected_calibration} to channel {target_channel}."
            ).to_tuple()