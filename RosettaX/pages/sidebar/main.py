import webbrowser
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, no_update

from RosettaX.pages import styling
from RosettaX.pages.settings.utils import list_setting_files, profile_directory
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.directories import (
    fluorescence_calibration_directory,
    scattering_calibration_directory,
)

from .ids import SidebarIds


class Sidebar:
    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo.png"
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
            sidebar_data = self._list_saved_calibrations()
            return self._saved_calibration_items(sidebar_data)

        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_calibrations_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_calibration_folder(n_clicks: int) -> str:
            target_directory = self._calibration_open_directory()
            try:
                webbrowser.open(target_directory.as_uri())
                return f"Opened: {target_directory}"
            except Exception as exc:
                return f"Could not open folder: {type(exc).__name__}: {exc}"

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_dropdown, "options"),
            dash.Input(SidebarIds.saved_profiles_refresh_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def refresh_saved_profiles_list(n_clicks: int):
            return self._saved_profile_dropdown_options()

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

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_load_status, "children"),
            dash.Input(SidebarIds.saved_profiles_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_selected_profile(profile_name: str) -> str:
            if not profile_name:
                return no_update

            try:
                runtime_config = RuntimeConfig()
                runtime_config.load_json(f"{profile_name}.json")
                return f"Loaded profile: {profile_name}.json"
            except Exception as exc:
                return f"Could not load profile: {type(exc).__name__}: {exc}"

        return self

    def layout(self, sidebar: dict[str, list[str]] | None = None) -> list[object]:
        sidebar_data = sidebar if sidebar is not None else self._list_saved_calibrations()

        return [
            html.Div(
                self._build_sidebar_children(sidebar_data),
                style=styling.SIDEBAR,
                id=self._id("container"),
            )
        ]

    def _build_sidebar_children(self, sidebar: dict[str, list[str]]) -> list[object]:
        return [
            self._build_logo_section(),
            html.Hr(),
            self._build_navigation_section(),
            html.Hr(),
            self._build_saved_calibrations_section(sidebar),
            html.Hr(),
            self._build_saved_profiles_section(),
        ]

    def _build_logo_section(self) -> html.Div:
        logo_style = {
            "display": "block",
            "width": "100%",
            "height": "auto",
            "objectFit": "contain",
        }

        return html.Div(
            html.Img(
                src=self.logo_src,
                style=logo_style,
                id=self._id("logo"),
            ),
            style={
                "width": "100%",
            },
            id=self._id("logo-section"),
        )

    def _build_navigation_section(self) -> html.Div:
        return html.Div(
            [
                html.P("Navigation bar", className="lead"),
                self._build_navigation_links(),
            ],
            id=self._id("navigation-section"),
        )

    def _build_navigation_links(self) -> dbc.Nav:
        return dbc.Nav(
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
        )

    def _build_saved_calibrations_section(self, sidebar: dict[str, list[str]]) -> html.Div:
        return html.Div(
            [
                dbc.Card(
                    [
                        self._build_saved_calibrations_header(),
                        self._build_saved_calibrations_body(sidebar),
                    ],
                    style={"height": "100%"},
                    id=self._id("saved-calibrations-card"),
                ),
            ],
            id=self._id("saved-calibrations-section"),
        )

    def _build_saved_calibrations_header(self) -> dbc.CardHeader:
        return dbc.CardHeader(
            self._build_card_header_row(
                title="Saved Calibrations",
                open_button_id=SidebarIds.saved_calibrations_open_folder_button,
                refresh_button_id=SidebarIds.saved_calibrations_refresh_button,
            )
        )

    def _build_saved_calibrations_body(self, sidebar: dict[str, list[str]]) -> dbc.CardBody:
        return dbc.CardBody(
            [
                html.Div(
                    self._saved_calibration_items(sidebar),
                    id=SidebarIds.saved_calibrations_body_container,
                ),
                self._build_status_div(SidebarIds.saved_calibrations_open_folder_status),
            ],
            style={"maxHeight": "30vh", "overflowY": "auto"},
        )

    def _build_saved_profiles_section(self) -> html.Div:
        return html.Div(
            [
                dbc.Card(
                    [
                        self._build_saved_profiles_header(),
                        self._build_saved_profiles_body(),
                    ],
                    style={"height": "100%"},
                    id=self._id("saved-profiles-card"),
                ),
            ],
            id=self._id("saved-profiles-section"),
        )

    def _build_saved_profiles_header(self) -> dbc.CardHeader:
        return dbc.CardHeader(
            self._build_card_header_row(
                title="Saved Profiles",
                open_button_id=SidebarIds.saved_profiles_open_folder_button,
                refresh_button_id=SidebarIds.saved_profiles_refresh_button,
            )
        )

    def _build_saved_profiles_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._saved_profile_dropdown(),
                self._build_status_div(SidebarIds.saved_profiles_load_status),
                self._build_status_div(SidebarIds.saved_profiles_open_folder_status),
            ],
            style={"maxHeight": "30vh", "overflowY": "auto"},
        )

    def _build_card_header_row(
        self,
        *,
        title: str,
        open_button_id: str,
        refresh_button_id: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(title),
                self._build_header_buttons(
                    open_button_id=open_button_id,
                    refresh_button_id=refresh_button_id,
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "gap": "12px",
            },
        )

    def _build_header_buttons(
        self,
        *,
        open_button_id: str,
        refresh_button_id: str,
    ) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Open folder",
                    id=open_button_id,
                    n_clicks=0,
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="rounded-pill",
                ),
                dbc.Button(
                    "Update",
                    id=refresh_button_id,
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
        )

    def _build_status_div(self, component_id: str) -> html.Div:
        return html.Div(
            "",
            id=component_id,
            style={
                "marginTop": "10px",
                "opacity": 0.75,
                "fontSize": "0.9rem",
            },
        )

    def _saved_calibration_items(self, sidebar: dict[str, list[str]]) -> list[html.Div]:
        normalized_sidebar = self._normalize_sidebar_data(sidebar)

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

    def _normalize_sidebar_data(self, sidebar: dict[str, list[str]] | None) -> dict[str, list[str]]:
        sidebar = dict(sidebar or {})
        normalized_sidebar: dict[str, list[str]] = {}

        for folder, files in sidebar.items():
            folder_key = self._normalize_folder_key(folder)
            if folder_key not in normalized_sidebar:
                normalized_sidebar[folder_key] = []
            normalized_sidebar[folder_key].extend([str(file) for file in (files or [])])

        return normalized_sidebar

    @staticmethod
    def _normalize_folder_key(folder: str) -> str:
        normalized_folder = str(folder or "").strip().lower()
        normalized_folder = normalized_folder.replace(" ", "_")
        return normalized_folder

    def _saved_profile_dropdown(self) -> dcc.Dropdown | dbc.Alert:
        options = self._saved_profile_dropdown_options()

        if not options:
            return dbc.Alert(
                "No saved profiles found.",
                color="secondary",
                style={"marginBottom": "0px"},
            )

        return dcc.Dropdown(
            id=SidebarIds.saved_profiles_dropdown,
            options=options,
            placeholder="Select a profile",
            clearable=True,
        )

    def _saved_profile_dropdown_options(self) -> list[dict[str, str]]:
        profiles = sorted(set(list_setting_files()))
        return [{"label": profile_name, "value": profile_name} for profile_name in profiles]

    def _saved_folder_section(
        self,
        *,
        folder_key: str,
        folder_label: str,
        files: list[str],
    ) -> html.Div:
        return html.Div(
            [
                html.H5(folder_label, style={"marginBottom": "8px"}),
                self._build_saved_folder_content(folder_key=folder_key, files=files),
                html.Hr(style={"opacity": 0.25}),
            ],
            id=self._id(f"saved-folder-{folder_key}"),
        )

    def _build_saved_folder_content(self, *, folder_key: str, files: list[str]) -> object:
        if files:
            return html.Ul([self._saved_file_item(folder_key, file_name) for file_name in files])

        return dbc.Alert(
            "No saved calibrations found.",
            color="secondary",
            style={"marginBottom": "0px"},
        )

    def _saved_file_item(self, folder: str, file: str) -> html.Li:
        return html.Li(
            dcc.Link(
                file,
                href=f"/apply-calibration/{folder}/{file}",
                id={"type": "apply-calibration", "index": f"{folder}/{file}"},
            )
        )

    def _list_saved_calibrations(self) -> dict[str, list[str]]:
        return {
            "fluorescence": self._list_json_files_in_directory(fluorescence_calibration_directory),
            "scattering": self._list_json_files_in_directory(scattering_calibration_directory),
        }

    @staticmethod
    def _list_json_files_in_directory(directory: Path | str) -> list[str]:
        directory_path = Path(directory).expanduser()
        directory_path.mkdir(parents=True, exist_ok=True)

        return sorted(
            file_path.name
            for file_path in directory_path.glob("*.json")
            if file_path.is_file()
        )

    def _calibration_open_directory(self) -> Path:
        fluorescence_directory = Path(fluorescence_calibration_directory).expanduser()
        scattering_directory = Path(scattering_calibration_directory).expanduser()

        fluorescence_directory.mkdir(parents=True, exist_ok=True)
        scattering_directory.mkdir(parents=True, exist_ok=True)

        if fluorescence_directory.parent == scattering_directory.parent:
            return fluorescence_directory.parent

        return fluorescence_directory


sidebar_html = Sidebar().register_callbacks().layout