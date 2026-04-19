# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.directories import (
    fluorescence_calibration_directory,
    scattering_calibration_directory,
)


logger = logging.getLogger(__name__)


class CalibrationPickerSection:
    def __init__(self, page) -> None:
        self.page = page

        self._folder_definitions: list[tuple[str, str, Path]] = [
            ("fluorescence", "Fluorescence", Path(fluorescence_calibration_directory)),
            ("scattering", "Scattering", Path(scattering_calibration_directory)),
        ]

        logger.debug(
            "Initialized CalibrationPickerSection for page=%s",
            self.page.__class__.__name__,
        )

    def get_layout(self) -> dbc.Card:
        logger.debug("Building CalibrationPickerSection layout")

        return dbc.Card(
            [
                dbc.CardHeader("1. Select calibration"),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Select(
                                        id=self.page.ids.CalibrationPicker.dropdown,
                                        options=[],
                                        value=None,
                                    ),
                                    width=True,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Refresh",
                                        id=self.page.ids.CalibrationPicker.refresh_button,
                                        color="secondary",
                                        outline=True,
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="g-2",
                            align="center",
                        ),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering CalibrationPickerSection callbacks")

        @dash.callback(
            dash.Output(self.page.ids.CalibrationPicker.dropdown, "options"),
            dash.Output(self.page.ids.CalibrationPicker.dropdown, "value"),
            dash.Output(self.page.ids.Stores.selected_calibration_path_store, "data"),
            dash.Input(self.page.ids.CalibrationPicker.refresh_button, "n_clicks"),
            dash.Input(self.page.ids.Page.location, "search"),
            dash.State(self.page.ids.CalibrationPicker.dropdown, "value"),
            prevent_initial_call=False,
        )
        def refresh_calibration_picker(
            refresh_button_clicks: Optional[int],
            search: Optional[str],
            current_dropdown_value: Any,
        ) -> tuple[list[dict[str, str]], Optional[str], Optional[str]]:
            logger.debug(
                "refresh_calibration_picker called with refresh_button_clicks=%r search=%r current_dropdown_value=%r",
                refresh_button_clicks,
                search,
                current_dropdown_value,
            )

            dropdown_options = self._build_dropdown_options()
            allowed_values = {
                str(option["value"])
                for option in dropdown_options
                if isinstance(option, dict) and "value" in option
            }

            logger.debug(
                "Built %d calibration dropdown options",
                len(dropdown_options),
            )

            selected_calibration_from_url = self._extract_selected_calibration_from_search(search)

            if (
                selected_calibration_from_url is not None
                and selected_calibration_from_url in allowed_values
            ):
                resolved_dropdown_value = selected_calibration_from_url
                logger.debug(
                    "Using URL-selected calibration=%r",
                    resolved_dropdown_value,
                )

            elif (
                current_dropdown_value is not None
                and str(current_dropdown_value) in allowed_values
            ):
                resolved_dropdown_value = str(current_dropdown_value)
                logger.debug(
                    "Keeping current dropdown selection=%r",
                    resolved_dropdown_value,
                )

            elif dropdown_options:
                resolved_dropdown_value = str(dropdown_options[0]["value"])
                logger.debug(
                    "Using first available calibration=%r",
                    resolved_dropdown_value,
                )

            else:
                resolved_dropdown_value = None
                logger.debug("No calibration files found, dropdown will remain empty")

            return (
                dropdown_options,
                resolved_dropdown_value,
                resolved_dropdown_value,
            )

    def _build_dropdown_options(self) -> list[dict[str, str]]:
        logger.debug("Building calibration dropdown options from disk")

        dropdown_options: list[dict[str, str]] = []

        for folder_key, folder_label, folder_path in self._folder_definitions:
            try:
                folder_path.mkdir(parents=True, exist_ok=True)

                calibration_file_paths = sorted(
                    [
                        path
                        for path in folder_path.glob("*.json")
                        if path.is_file()
                    ],
                    key=lambda path: path.name.lower(),
                )

                logger.debug(
                    "Found %d calibration files in folder_key=%r folder_path=%r",
                    len(calibration_file_paths),
                    folder_key,
                    str(folder_path),
                )

                for calibration_file_path in calibration_file_paths:
                    dropdown_options.append(
                        {
                            "label": f"{folder_label} | {calibration_file_path.name}",
                            "value": f"{folder_key}/{calibration_file_path.name}",
                        }
                    )

            except Exception:
                logger.exception(
                    "Failed while building dropdown options for folder_key=%r folder_path=%r",
                    folder_key,
                    str(folder_path),
                )

        logger.debug(
            "Returning %d total calibration dropdown options",
            len(dropdown_options),
        )
        return dropdown_options

    @staticmethod
    def _extract_selected_calibration_from_search(search: Optional[str]) -> Optional[str]:
        logger.debug(
            "Extracting selected_calibration from search=%r",
            search,
        )

        if not search:
            return None

        parsed_query = parse_qs(search.lstrip("?"))
        selected_calibration_values = parsed_query.get("selected_calibration", [])

        if not selected_calibration_values:
            return None

        selected_calibration = str(selected_calibration_values[0]).strip()

        if not selected_calibration:
            return None

        logger.debug(
            "Extracted selected_calibration=%r from URL query string",
            selected_calibration,
        )
        return selected_calibration