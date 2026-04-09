# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages.calibrate.ids import Ids
from RosettaX.pages.fluorescence import service


class CalibrationPickerSection:
    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        [
                            html.Div("3. Select calibration"),
                            dbc.Button(
                                "Update",
                                id=Ids.CalibrationPicker.refresh_button,
                                n_clicks=0,
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="rounded-pill",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                        },
                    )
                ),
                dbc.CardBody(
                    [
                        html.Div("Saved calibration", style={"marginBottom": "6px"}),
                        dcc.Dropdown(
                            id=Ids.CalibrationPicker.dropdown,
                            options=[],
                            value=None,
                            placeholder="Select calibration",
                            clearable=True,
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Click Update to reload saved calibrations.",
                            id=Ids.CalibrationPicker.refresh_status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                        dcc.Store(id=Ids.Stores.selected_calibration_path_store),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(Ids.CalibrationPicker.dropdown, "options"),
            dash.Output(Ids.CalibrationPicker.refresh_status, "children"),
            dash.Input(Ids.CalibrationPicker.refresh_button, "n_clicks"),
            prevent_initial_call=False,
        )
        def refresh_calibration_options(n_clicks: int) -> tuple:
            try:
                sidebar = service.CalibrationFileStore.list_saved_calibrations()
            except Exception as exc:
                return [], f"Could not read saved calibrations: {type(exc).__name__}: {exc}"

            options: list[dict[str, str]] = []
            for folder, files in (sidebar or {}).items():
                for file in files or []:
                    label = f"{folder}/{file}"
                    value = f"{folder}/{file}"
                    options.append({"label": label, "value": value})

            if not options:
                return [], "No saved calibrations found."

            return options, f"Loaded {len(options)} calibration file(s)."

        @dash.callback(
            dash.Output(Ids.Stores.selected_calibration_path_store, "data"),
            dash.Input(Ids.CalibrationPicker.dropdown, "value"),
            prevent_initial_call=True,
        )
        def store_selected_calibration_path(selected: Optional[str]) -> Any:
            if not selected:
                return None
            return str(selected)