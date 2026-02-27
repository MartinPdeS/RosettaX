# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.calibrate.ids import Ids


@dataclass(frozen=True)
class ApplyCalibrationResult:
    status: Any = dash.no_update

    def to_tuple(self) -> tuple:
        return (self.status,)


class ApplySection:
    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("3. Apply"),
                dbc.CardBody(
                    [
                        dbc.Button(
                            "Apply",
                            id=Ids.Apply.apply_button,
                            n_clicks=0,
                            color="primary",
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Status will appear here.",
                            id=Ids.Apply.status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(Ids.Apply.status, "children"),
            dash.Input(Ids.Apply.apply_button, "n_clicks"),
            dash.State(Ids.Stores.selected_calibration_path_store, "data"),
            dash.State(Ids.ChannelPicker.dropdown, "value"),
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