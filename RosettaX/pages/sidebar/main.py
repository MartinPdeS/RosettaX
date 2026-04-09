import webbrowser
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages import styling
from RosettaX.pages.fluorescence import service
from RosettaX.pages.settings.utils import list_setting_files, profile_directory


class SidebarIds:
    prefix = "sidebar"

    saved_calibrations_refresh_button = f"{prefix}-saved-calibrations-refresh-button"
    saved_calibrations_open_folder_button = f"{prefix}-saved-calibrations-open-folder-button"
    saved_calibrations_open_folder_status = f"{prefix}-saved-calibrations-open-folder-status"
    saved_calibrations_body_container = f"{prefix}-saved-calibrations-body-container"

    saved_profiles_refresh_button = f"{prefix}-saved-profiles-refresh-button"
    saved_profiles_open_folder_button = f"{prefix}-saved-profiles-open-folder-button"
    saved_profiles_open_folder_status = f"{prefix}-saved-profiles-open-folder-status"
    saved_profiles_body_container = f"{prefix}-saved-profiles-body-container"


class Sidebar:
    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo.png"
        self.logo_max_height_px = 156

        self.sidebar_width_px = 380

        self._folder_display_order: list[tuple[str, str]] = [
            ("fluorescence", "Fluorescence"),
            ("scattering", "Scattering"),
        ]

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def register_callbacks(self) -> "Sidebar":
        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_body_container, "children"),
            dash.Input(SidebarIds.saved_calibrations_refresh_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def refresh_saved_calibrations_list(n_clicks: int):
            sidebar = service.CalibrationFileStore.list_saved_calibrations()
            return self._saved_calibration_items(sidebar)

        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_calibrations_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_calibration_folder(n_clicks: int) -> str:
            root_dir = Path(service.CalibrationFileStore._root_dir())
            try:
                webbrowser.open(root_dir.as_uri())
                return f"Opened: {root_dir}"
            except Exception as exc:
                return f"Could not open folder: {type(exc).__name__}: {exc}"

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_body_container, "children"),
            dash.Input(SidebarIds.saved_profiles_refresh_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def refresh_saved_profiles_list(n_clicks: int):
            return self._saved_profile_items()

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_profiles_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_profiles_folder(n_clicks: int) -> str:
            root_dir = Path(profile_directory)
            try:
                webbrowser.open(root_dir.as_uri())
                return f"Opened: {root_dir}"
            except Exception as exc:
                return f"Could not open folder: {type(exc).__name__}: {exc}"

        return self

    def layout(self, sidebar: dict[str, list[str]]) -> list[object]:
        return [
            html.Div(
                [
                    self._logo_section(),
                    html.Hr(),
                    self._navigation_section(),
                    html.Hr(),
                    self._saved_calibrations_section(sidebar),
                    html.Hr(),
                    self._saved_profiles_section(),
                ],
                style=styling.SIDEBAR,
                id=self._id("container"),
            )
        ]

    def _logo_section(self) -> dbc.Col:
        logo_style = {
            "display": "block",
            "maxWidth": "100%",
            "height": "auto",
            "maxHeight": f"{self.logo_max_height_px}px",
            "objectFit": "contain",
        }

        return dbc.Col(
            html.Img(
                src=self.logo_src,
                style=logo_style,
                id=self._id("logo"),
            ),
            width="auto",
        )

    def _navigation_section(self) -> html.Div:
        return html.Div(
            [
                html.P("Navigation bar", className="lead"),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            page["name"],
                            href=page["relative_path"],
                            active="exact",
                        )
                        for page in dash.page_registry.values()
                    ],
                    vertical=True,
                    pills=True,
                ),
            ],
            id=self._id("navigation-section"),
        )

    def _saved_calibrations_section(self, sidebar: dict[str, list[str]]) -> html.Div:
        return html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.Div(
                                [
                                    html.Div("Saved Calibrations"),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Open folder",
                                                id=SidebarIds.saved_calibrations_open_folder_button,
                                                n_clicks=0,
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                className="rounded-pill",
                                            ),
                                            dbc.Button(
                                                "Update",
                                                id=SidebarIds.saved_calibrations_refresh_button,
                                                n_clicks=0,
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                className="rounded-pill",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "gap": "8px",
                                            "alignItems": "center",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "space-between",
                                    "gap": "12px",
                                },
                            )
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    self._saved_calibration_items(sidebar),
                                    id=SidebarIds.saved_calibrations_body_container,
                                ),
                                html.Div(
                                    "",
                                    id=SidebarIds.saved_calibrations_open_folder_status,
                                    style={
                                        "marginTop": "10px",
                                        "opacity": 0.75,
                                        "fontSize": "0.9rem",
                                    },
                                ),
                            ],
                            style={"maxHeight": "30vh", "overflowY": "auto"},
                        ),
                    ],
                    style={"height": "100%"},
                    id=self._id("saved-calibrations-card"),
                ),
            ],
            id=self._id("saved-calibrations-section"),
        )

    def _saved_profiles_section(self) -> html.Div:
        return html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.Div(
                                [
                                    html.Div("Saved Profiles"),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Open folder",
                                                id=SidebarIds.saved_profiles_open_folder_button,
                                                n_clicks=0,
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                className="rounded-pill",
                                            ),
                                            dbc.Button(
                                                "Update",
                                                id=SidebarIds.saved_profiles_refresh_button,
                                                n_clicks=0,
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                className="rounded-pill",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "gap": "8px",
                                            "alignItems": "center",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "space-between",
                                    "gap": "12px",
                                },
                            )
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    self._saved_profile_items(),
                                    id=SidebarIds.saved_profiles_body_container,
                                ),
                                html.Div(
                                    "",
                                    id=SidebarIds.saved_profiles_open_folder_status,
                                    style={
                                        "marginTop": "10px",
                                        "opacity": 0.75,
                                        "fontSize": "0.9rem",
                                    },
                                ),
                            ],
                            style={"maxHeight": "30vh", "overflowY": "auto"},
                        ),
                    ],
                    style={"height": "100%"},
                    id=self._id("saved-profiles-card"),
                ),
            ],
            id=self._id("saved-profiles-section"),
        )

    def _saved_calibration_items(self, sidebar: dict[str, list[str]]) -> list[html.Div]:
        sidebar = dict(sidebar or {})

        def _normalize_folder_key(folder: str) -> str:
            normalized_folder = str(folder or "").strip().lower()
            normalized_folder = normalized_folder.replace(" ", "_")
            return normalized_folder

        normalized_sidebar: dict[str, list[str]] = {}
        for folder, files in sidebar.items():
            folder_key = _normalize_folder_key(folder)
            if folder_key not in normalized_sidebar:
                normalized_sidebar[folder_key] = []
            normalized_sidebar[folder_key].extend([str(file) for file in (files or [])])

        items: list[html.Div] = []
        for folder_key, folder_label in self._folder_display_order:
            files = sorted(set(normalized_sidebar.get(folder_key, [])))
            items.append(
                self._saved_folder_section(
                    folder_key=folder_key,
                    folder_label=folder_label,
                    files=files,
                )
            )

        return items

    def _saved_profile_items(self) -> list[object]:
        profiles = sorted(set(list_setting_files()))

        if not profiles:
            return [
                dbc.Alert(
                    "No saved profiles found.",
                    color="secondary",
                    style={"marginBottom": "0px"},
                )
            ]

        return [
            html.Ul([self._saved_profile_item(profile_name) for profile_name in profiles]),
        ]

    def _saved_folder_section(self, *, folder_key: str, folder_label: str, files: list[str]) -> html.Div:
        if files:
            content: list[object] = [
                html.Ul([self._saved_file_item(folder_key, file) for file in files]),
            ]
        else:
            content = [
                dbc.Alert(
                    "No saved calibrations found.",
                    color="secondary",
                    style={"marginBottom": "0px"},
                )
            ]

        return html.Div(
            [
                html.H5(folder_label, style={"marginBottom": "8px"}),
                *content,
                html.Hr(style={"opacity": 0.25}),
            ],
            id=self._id(f"saved-folder-{folder_key}"),
        )

    def _saved_file_item(self, folder: str, file: str) -> html.Li:
        return html.Li(
            dcc.Link(
                file,
                href=f"/apply-calibration/{folder}/{file}",
                id={"type": "apply-calibration", "index": f"{folder}/{file}"},
            )
        )

    def _saved_profile_item(self, profile_name: str) -> html.Li:
        return html.Li(
            dcc.Link(
                profile_name,
                href=f"/default-setting-values?profile={profile_name}.json",
                id={"type": "apply-profile", "index": profile_name},
            )
        )


sidebar_html = Sidebar().register_callbacks().layout