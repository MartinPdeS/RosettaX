import webbrowser
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from RosettaX.pages.fluorescence import service
from RosettaX.pages import styling

class SidebarIds:
    prefix = "sidebar"

    saved_calibrations_refresh_button = f"{prefix}-saved-calibrations-refresh-button"
    saved_calibrations_open_folder_button = f"{prefix}-saved-calibrations-open-folder-button"
    saved_calibrations_open_folder_status = f"{prefix}-saved-calibrations-open-folder-status"
    saved_calibrations_body_container = f"{prefix}-saved-calibrations-body-container"


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
            return self._saved_items(sidebar)

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
                ],
                style=styling.SIDEBAR,
                id=self._id("container"),
            )
        ]

    def _logo_section(self) -> dbc.Col:
        return dbc.Col(
            html.Img(
                src=self.logo_src,
                style=self._logo_style(),
                id=self._id("logo"),
            ),
            width="auto",
        )

    def _logo_style(self) -> dict[str, str]:
        return {
            "display": "block",
            "maxWidth": "100%",
            "height": "auto",
            "maxHeight": f"{self.logo_max_height_px}px",
            "objectFit": "contain",
        }

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
                                        style={"display": "flex", "gap": "8px", "alignItems": "center"},
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
                                    self._saved_items(sidebar),
                                    id=SidebarIds.saved_calibrations_body_container,
                                ),
                                html.Div(
                                    "",
                                    id=SidebarIds.saved_calibrations_open_folder_status,
                                    style={"marginTop": "10px", "opacity": 0.75, "fontSize": "0.9rem"},
                                ),
                            ],
                            style={"maxHeight": "60vh", "overflowY": "auto"},
                        ),
                    ],
                    style={"height": "100%"},
                    id=self._id("saved-calibrations-card"),
                ),
            ],
            id=self._id("saved-calibrations-section"),
        )

    def _saved_items(self, sidebar: dict[str, list[str]]) -> list[html.Div]:
        sidebar = dict(sidebar or {})

        def _normalize_folder_key(folder: str) -> str:
            s = str(folder or "").strip().lower()
            s = s.replace(" ", "_")
            return s

        normalized: dict[str, list[str]] = {}
        for folder, files in sidebar.items():
            key = _normalize_folder_key(folder)
            if key not in normalized:
                normalized[key] = []
            normalized[key].extend([str(f) for f in (files or [])])

        items: list[html.Div] = []
        for folder_key, folder_label in self._folder_display_order:
            files = sorted(set(normalized.get(folder_key, [])))
            items.append(self._saved_folder_section(folder_key=folder_key, folder_label=folder_label, files=files))

        return items

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


sidebar_html = Sidebar().register_callbacks().layout