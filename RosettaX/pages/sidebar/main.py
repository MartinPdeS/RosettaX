# -*- coding: utf-8 -*-

import logging
import webbrowser
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote
import os
import platform
import subprocess

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages.settings.utils import list_setting_files, profile_directory
from RosettaX.utils.directories import (
    fluorescence_calibration_directory,
    scattering_calibration_directory,
)

def _open_directory(path: Path) -> None:
    resolved_path = Path(path).resolve()

    logger.debug("Opening directory at path=%r", str(resolved_path))

    if not resolved_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {resolved_path}")

    system_name = platform.system()

    if system_name == "Darwin":
        subprocess.run(["open", str(resolved_path)], check=True)
        return

    if system_name == "Windows":
        os.startfile(str(resolved_path))
        return

    if system_name == "Linux":
        subprocess.run(["xdg-open", str(resolved_path)], check=True)
        return

    raise RuntimeError(f"Unsupported operating system: {system_name}")


logger = logging.getLogger(__name__)


class SidebarIds:
    prefix = "sidebar"

    saved_calibrations_refresh_button = f"{prefix}-saved-calibrations-refresh-button"
    saved_calibrations_open_folder_button = f"{prefix}-saved-calibrations-open-folder-button"
    saved_calibrations_open_folder_status = f"{prefix}-saved-calibrations-open-folder-status"
    saved_calibrations_body_container = f"{prefix}-saved-calibrations-body-container"
    saved_calibrations_refresh_store = f"{prefix}-saved-calibrations-refresh-store"

    saved_profiles_refresh_button = f"{prefix}-saved-profiles-refresh-button"
    saved_profiles_open_folder_button = f"{prefix}-saved-profiles-open-folder-button"
    saved_profiles_open_folder_status = f"{prefix}-saved-profiles-open-folder-status"
    saved_profiles_dropdown = f"{prefix}-saved-profiles-dropdown"
    saved_profiles_load_status = f"{prefix}-saved-profiles-load-status"


class Sidebar:
    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo.png"
        self.logo_max_height_px = 156

        self.sidebar_width_px = 460

        self._folder_display_order: list[tuple[str, str]] = [
            ("fluorescence", "Fluorescence"),
            ("scattering", "Scattering"),
        ]

        logger.debug(
            "Initialized Sidebar with sidebar_width_px=%r logo_src=%r",
            self.sidebar_width_px,
            self.logo_src,
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering sidebar callbacks")

        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_body_container, "children"),
            dash.Input(SidebarIds.saved_calibrations_refresh_button, "n_clicks"),
            dash.Input(SidebarIds.saved_calibrations_refresh_store, "data"),
            prevent_initial_call=True,
        )
        def refresh_saved_calibrations(
            refresh_button_clicks: Optional[int],
            refresh_signal: Any,
        ):
            logger.debug(
                "refresh_saved_calibrations called with refresh_button_clicks=%r refresh_signal=%r",
                refresh_button_clicks,
                refresh_signal,
            )

            saved_calibrations = self._list_saved_calibrations()

            logger.debug(
                "Loaded saved calibrations from disk with fluorescence=%d scattering=%d",
                len(saved_calibrations.get("fluorescence", [])),
                len(saved_calibrations.get("scattering", [])),
            )
            return self._build_saved_calibrations_body(saved_calibrations)








        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_calibrations_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_saved_calibrations_folder(n_clicks: Optional[int]):
            logger.debug(
                "open_saved_calibrations_folder called with n_clicks=%r",
                n_clicks,
            )
            del n_clicks

            try:
                calibration_root_directory = Path(fluorescence_calibration_directory).resolve().parent
                logger.debug(
                    "Opening calibration root directory=%r",
                    str(calibration_root_directory),
                )
                _open_directory(calibration_root_directory)
                return f"Opened calibration folder: {calibration_root_directory}"
            except Exception as exc:
                logger.exception("Failed to open calibration folder")
                return f"Could not open calibration folder: {type(exc).__name__}: {exc}"





        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_dropdown, "options"),
            dash.Input(SidebarIds.saved_profiles_refresh_button, "n_clicks"),
            prevent_initial_call=False,
        )
        def refresh_saved_profiles(_n_clicks: Optional[int]):
            logger.debug("refresh_saved_profiles called with n_clicks=%r", _n_clicks)

            try:
                setting_files = list_setting_files()
                options = [{"label": file_name, "value": file_name} for file_name in setting_files]
                logger.debug("Loaded %d profile options", len(options))
                return options
            except Exception:
                logger.exception("Failed to refresh saved profiles")
                return []



        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_profiles_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_saved_profiles_folder(n_clicks: Optional[int]):
            logger.debug("open_saved_profiles_folder called with n_clicks=%r", n_clicks)
            del n_clicks

            try:
                resolved_profile_directory = Path(profile_directory).resolve()
                logger.debug("Opening profile directory=%r", str(resolved_profile_directory))
                _open_directory(resolved_profile_directory)
                return f"Opened profile folder: {resolved_profile_directory}"
            except Exception as exc:
                logger.exception("Failed to open profile folder")
                return f"Could not open profile folder: {type(exc).__name__}: {exc}"



    def layout(self, sidebar: Optional[dict[str, list[str]]] = None) -> html.Div:
        logger.debug("Building sidebar layout with sidebar=%r", sidebar)

        if sidebar is None:
            sidebar = self._list_saved_calibrations()

        return html.Div(
            [
                self._build_logo_section(),
                self._build_navigation_section(),
                self._build_saved_calibrations_section(sidebar),
                self._build_saved_profiles_section(),
                dcc.Store(id=SidebarIds.saved_calibrations_refresh_store, data=0),
            ],
            style={
                "width": f"{self.sidebar_width_px}px",
                "height": "100vh",
                "display": "flex",
                "flexDirection": "column",
                "gap": "16px",
                "overflowY": "auto",
                "paddingRight": "8px",
                "boxSizing": "border-box",
            },
        )

    def _list_saved_calibrations(self) -> dict[str, list[str]]:
        logger.debug("Listing saved calibrations from disk")

        saved_calibrations: dict[str, list[str]] = {
            "fluorescence": [],
            "scattering": [],
        }

        folder_to_directory = {
            "fluorescence": Path(fluorescence_calibration_directory),
            "scattering": Path(scattering_calibration_directory),
        }

        for folder_name, directory_path in folder_to_directory.items():
            try:
                directory_path.mkdir(parents=True, exist_ok=True)
                file_names = sorted(
                    [
                        path.name
                        for path in directory_path.glob("*.json")
                        if path.is_file()
                    ],
                    key=str.lower,
                )
                saved_calibrations[folder_name] = file_names

                logger.debug(
                    "Found %d calibration files in folder=%r directory=%r",
                    len(file_names),
                    folder_name,
                    str(directory_path),
                )

            except Exception:
                logger.exception(
                    "Failed to list calibration files for folder=%r directory=%r",
                    folder_name,
                    str(directory_path),
                )
                saved_calibrations[folder_name] = []

        return saved_calibrations

    def _build_logo_section(self) -> html.Div:
        return html.Div(
            [
                html.Img(
                    src=self.logo_src,
                    style={
                        "width": "100%",
                        "height": "auto",
                        "display": "block",
                        "objectFit": "contain",
                        "maxHeight": f"{self.logo_max_height_px}px",
                    },
                )
            ],
            style={"width": "100%"},
        )

    def _build_navigation_section(self) -> html.Div:
        return html.Div(
            [
                dbc.Nav(
                    [
                        dbc.NavLink("Home", href="/home", active="exact"),
                        dbc.NavLink("Help", href="/help", active="exact"),
                        dbc.NavLink("Fluorescence", href="/fluorescence", active="exact"),
                        dbc.NavLink("Scattering", href="/scattering", active="exact"),
                        dbc.NavLink("Apply calibration", href="/calibrate", active="exact"),
                        dbc.NavLink("Settings", href="/settings", active="exact"),
                    ],
                    vertical=True,
                    pills=True,
                )
            ]
        )

    def _build_saved_calibrations_section(
        self,
        saved_calibrations: dict[str, list[str]],
    ) -> dbc.Card:
        logger.debug(
            "Building saved calibrations section with fluorescence=%d scattering=%d",
            len(saved_calibrations.get("fluorescence", [])),
            len(saved_calibrations.get("scattering", [])),
        )

        return dbc.Card(
            [
                dbc.CardHeader("Saved calibrations"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Open folder",
                                    id=SidebarIds.saved_calibrations_open_folder_button,
                                    size="sm",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Refresh",
                                    id=SidebarIds.saved_calibrations_refresh_button,
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "8px",
                                "marginBottom": "10px",
                                "flexWrap": "wrap",
                            },
                        ),
                        html.Div(
                            self._build_saved_calibrations_body(saved_calibrations),
                            id=SidebarIds.saved_calibrations_body_container,
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_calibrations_open_folder_status,
                            style={"opacity": 0.75},
                        ),
                    ]
                ),
            ]
        )

    def _build_saved_calibrations_body(
        self,
        saved_calibrations: dict[str, list[str]],
    ) -> list[html.Div]:
        body_children: list[html.Div] = []

        for folder_key, folder_label in self._folder_display_order:
            file_names = saved_calibrations.get(folder_key, [])

            logger.debug(
                "Rendering folder_key=%r with %d files",
                folder_key,
                len(file_names),
            )

            if file_names:
                file_list = html.Ul(
                    [self._saved_file_item(folder_key, file_name) for file_name in file_names],
                    style={"paddingLeft": "20px", "marginBottom": "0px"},
                )
            else:
                file_list = html.Div(
                    "No calibration found.",
                    style={"opacity": 0.7, "fontStyle": "italic"},
                )

            body_children.append(
                html.Div(
                    [
                        html.Div(
                            folder_label,
                            style={
                                "fontWeight": "600",
                                "marginBottom": "6px",
                            },
                        ),
                        file_list,
                    ],
                    style={"marginBottom": "12px"},
                )
            )

        return body_children

    def _saved_file_item(self, folder: str, file_name: str) -> html.Li:
        logger.debug(
            "Building sidebar item for folder=%r file_name=%r",
            folder,
            file_name,
        )

        selected_calibration_value = f"{folder}/{file_name}"
        apply_href = f"/calibrate?selected_calibration={quote(selected_calibration_value, safe='')}"

        return html.Li(
            html.Div(
                [
                    html.Div(
                        dcc.Link(
                            file_name,
                            href=f"/calibration-json/{folder}/{file_name}",
                            target="_blank",
                            style={
                                "overflowWrap": "anywhere",
                                "wordBreak": "break-word",
                            },
                        ),
                        style={
                            "flex": "1 1 auto",
                            "minWidth": "0",
                        },
                    ),
                    dbc.Button(
                        "Apply",
                        href=apply_href,
                        color="link",
                        size="sm",
                        style={
                            "padding": "0px",
                            "whiteSpace": "nowrap",
                            "textDecoration": "none",
                            "flex": "0 0 auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "gap": "12px",
                    "width": "100%",
                },
            )
        )

    def _build_saved_profiles_section(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Saved profiles"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Open folder",
                                    id=SidebarIds.saved_profiles_open_folder_button,
                                    size="sm",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Refresh",
                                    id=SidebarIds.saved_profiles_refresh_button,
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "8px",
                                "marginBottom": "10px",
                                "flexWrap": "wrap",
                            },
                        ),
                        dcc.Dropdown(
                            id=SidebarIds.saved_profiles_dropdown,
                            options=[],
                            value=None,
                            placeholder="Select a saved profile",
                            clearable=True,
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_profiles_load_status,
                            style={"opacity": 0.75},
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_profiles_open_folder_status,
                            style={"opacity": 0.75},
                        ),
                    ]
                ),
            ]
        )



_sidebar_instance = Sidebar()


def register_sidebar_callbacks() -> None:
    logger.debug("register_sidebar_callbacks called")
    _sidebar_instance.register_callbacks()


def sidebar_html(sidebar: Optional[dict[str, list[str]]]) -> html.Div:
    logger.debug("sidebar_html called with sidebar=%r", sidebar)
    return _sidebar_instance.layout(sidebar)