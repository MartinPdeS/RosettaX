# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import service, directories

class CalibrationPickerSection:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    dash.html.Div(
                        [
                            dash.html.Div("3. Select calibration"),
                            dbc.Button(
                                "Update",
                                id=self.page.ids.CalibrationPicker.refresh_button,
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
                        dash.html.Div("Saved calibration", style={"marginBottom": "6px"}),
                        dash.dcc.Dropdown(
                            id=self.page.ids.CalibrationPicker.dropdown,
                            options=[],
                            value=None,
                            placeholder="Select calibration",
                            clearable=True,
                        ),
                        dash.html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Click Update to reload saved calibrations.",
                            id=self.page.ids.CalibrationPicker.refresh_status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                        dash.dcc.Store(id=self.page.ids.Stores.selected_calibration_path_store),
                    ]
                ),
            ]
        )

    def _register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.CalibrationPicker.dropdown, "options"),
            dash.Output(self.page.ids.CalibrationPicker.refresh_status, "children"),
            dash.Input(self.page.ids.CalibrationPicker.refresh_button, "n_clicks"),
            prevent_initial_call=False,
        )
        def refresh_calibration_options(n_clicks: int) -> tuple:
            try:
                sidebar = service.list_saved_calibrations_from_directory(
                    folder_name=directories.scattering_calibration_directory,
                )
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
            dash.Output(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.Input(self.page.ids.CalibrationPicker.dropdown, "value"),
            prevent_initial_call=True,
        )
        def store_selected_calibration_path(selected: Optional[str]) -> Any:
            if not selected:
                return None
            return str(selected)