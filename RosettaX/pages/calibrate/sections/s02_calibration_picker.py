# -*- coding: utf-8 -*-

from typing import Any, Optional
from pathlib import Path
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import directories

logger = logging.getLogger(__name__)


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
                            persistence=True,
                            persistence_type="session",
                        ),
                        dash.html.Div(style={"height": "10px"}),
                        dash.dcc.Store(
                            id=self.page.ids.Stores.selected_calibration_path_store,
                            storage_type="session",
                        ),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.CalibrationPicker.dropdown, "options"),
            dash.Input(self.page.ids.CalibrationPicker.refresh_button, "n_clicks"),
            prevent_initial_call=False,
        )
        def refresh_calibration_options(n_clicks: int) -> list[dict[str, str]]:
            del n_clicks

            logger.debug("Refreshing calibration dropdown options.")

            try:
                options = self._build_calibration_dropdown_options()
            except Exception:
                logger.exception("Could not build calibration dropdown options.")
                return []

            logger.debug("Loaded %d calibration option(s).", len(options))
            return options

        @dash.callback(
            dash.Output(self.page.ids.CalibrationPicker.dropdown, "value"),
            dash.Input(self.page.ids.CalibrationPicker.dropdown, "options"),
            dash.State(self.page.ids.Stores.selected_calibration_path_store, "data"),
            prevent_initial_call=False,
        )
        def restore_selected_calibration(
            options: list[dict[str, str]],
            stored_selected_path: Optional[str],
        ) -> Any:
            logger.debug(
                "restore_selected_calibration called with stored_selected_path=%r",
                stored_selected_path,
            )

            if not options:
                logger.debug("No options available. Returning None.")
                return None

            allowed_values = {str(option["value"]) for option in options}

            if stored_selected_path in allowed_values:
                logger.debug(
                    "Restoring stored calibration selection: %r",
                    stored_selected_path,
                )
                return stored_selected_path

            logger.debug("Stored calibration not available anymore. Falling back to first option.")
            return options[0]["value"]

        @dash.callback(
            dash.Output(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.Input(self.page.ids.CalibrationPicker.dropdown, "value"),
            prevent_initial_call=False,
        )
        def store_selected_calibration_path(selected: Optional[str]) -> Any:
            logger.debug(
                "store_selected_calibration_path called with selected=%r",
                selected,
            )

            if not selected:
                logger.debug("No calibration selected. Returning None.")
                return None

            selected_path = str(selected)
            logger.debug("Persisting selected calibration path=%r", selected_path)
            return selected_path

    def _build_calibration_dropdown_options(self) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []

        for folder_name, folder_path in [
            ("fluorescence", directories.fluorescence_calibration_directory),
            ("scattering", directories.scattering_calibration_directory),
        ]:
            for file_name in self._list_json_files_in_directory(folder_path):
                relative_value = f"{folder_name}/{file_name}"
                options.append(
                    {
                        "label": relative_value,
                        "value": relative_value,
                    }
                )

        options.sort(key=lambda item: item["label"].lower())
        return options

    @staticmethod
    def _list_json_files_in_directory(directory: Path | str) -> list[str]:
        directory_path = Path(directory).expanduser()
        directory_path.mkdir(parents=True, exist_ok=True)

        return sorted(
            file_path.name
            for file_path in directory_path.glob("*.json")
            if file_path.is_file()
        )