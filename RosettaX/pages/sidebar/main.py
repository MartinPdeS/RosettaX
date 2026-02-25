import dash
import dash_bootstrap_components as dbc
from dash import dcc, html


class SidebarIds:
    prefix = "sidebar"
    collapse_button = f"{prefix}-collapse-button"
    collapse_card = f"{prefix}-collapse-card"


class Sidebar:
    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo.png"
        self.logo_max_height_px = 156

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, sidebar: dict[str, list[str]]) -> list[object]:
        return [
            self._logo_section(),
            html.Hr(),
            self._navigation_section(),
            html.Hr(),
            self._saved_calibrations_section(sidebar),
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
                dbc.Nav(self._page_links(), vertical=True, pills=True),
            ],
            id=self._id("navigation-section"),
        )

    def _page_links(self) -> list[dbc.NavLink]:
        return [
            dbc.NavLink(page["name"], href=page["relative_path"], active="exact")
            for page in dash.page_registry.values()
            if page.get("name") != "Apply Calibration"
        ]

    def _saved_calibrations_section(self, sidebar: dict[str, list[str]]) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Apply Saved Calibrations",
                    id=SidebarIds.collapse_button,
                    className="mb-3",
                    color="primary",
                    n_clicks=0,
                    style={"width": "100%"},
                ),
                dbc.Collapse(
                    self._saved_calibrations_card(sidebar),
                    id=SidebarIds.collapse_card,
                    is_open=True,
                ),
            ],
            id=self._id("saved-calibrations-section"),
        )

    def _saved_calibrations_card(self, sidebar: dict[str, list[str]]) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Saved Calibrations"),
                dbc.CardBody(
                    self._saved_items(sidebar),
                    style={"maxHeight": "60vh", "overflowY": "auto"},
                ),
            ],
            style={"height": "100%"},
            id=self._id("saved-calibrations-card"),
        )

    def _saved_items(self, sidebar: dict[str, list[str]]) -> list[html.Div]:
        items: list[html.Div] = []

        for folder, files in (sidebar or {}).items():
            items.append(self._saved_folder_section(folder, files))

        if not items:
            items.append(
                dbc.Alert(
                    "No saved calibrations found.",
                    color="secondary",
                    style={"marginBottom": "0px"},
                )
            )

        return items

    def _saved_folder_section(self, folder: str, files: list[str]) -> html.Div:
        return html.Div(
            [
                html.H5(folder),
                html.Ul([self._saved_file_item(folder, file) for file in files]),
            ],
            id=self._id(f"saved-folder-{folder}"),
        )

    def _saved_file_item(self, folder: str, file: str) -> html.Li:
        return html.Li(
            dcc.Link(
                file,
                href=f"/apply-calibration/{folder}/{file}",
                id={"type": "apply-calibration", "index": f"{folder}/{file}"},
            )
        )


sidebar_html = Sidebar().layout