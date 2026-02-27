import json
import webbrowser
from threading import Timer
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.sidebar.main import sidebar_html
from RosettaX.parser import _parse_args, apply_cli_to_runtime_config


class RosettaXApplication:
    """
    Main Dash application wrapper.

    Adds
    ----
    - Sidebar + page container layout
    - Session stores used across pages
    - Dark mode switch (default is dark) that toggles the Bootstrap theme
    """

    _theme_light = dbc.themes.FLATLY
    _theme_dark = dbc.themes.SLATE

    def __init__(
        self,
        *,
        host: str,
        port: int,
        open_browser: bool,
    ) -> None:
        self.host = str(host)
        self.port = int(port)
        self.open_browser = bool(open_browser)

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[self._theme_dark],
            use_pages=True,
            suppress_callback_exceptions=True,
        )

        self._register_callbacks()
        self._set_layout()

    @staticmethod
    def create_table_from_dict(*, json_path: str) -> list[dict[str, str]]:
        """
        Load a JSON settings file and convert default MESF entries into a table-like list.

        Returns
        -------
        list[dict[str, str]]
            Each row is {"col1": <mesf_value>, "col2": ""}. If loading fails, returns
            a single empty row.
        """
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            table_data: list[dict[str, str]] = []
            for _key, value in (data or {}).items():
                if not isinstance(value, dict):
                    continue
                if value.get("default", True):
                    mesf_values = str(value.get("mesf_values", "")).split(",")
                    for mesf in mesf_values:
                        mesf_clean = str(mesf).strip()
                        if mesf_clean:
                            table_data.append({"col1": mesf_clean, "col2": ""})

            if not table_data:
                table_data = [{"col1": "", "col2": ""}]

            return table_data
        except Exception:
            return [{"col1": "", "col2": ""}]

    def _register_callbacks(self) -> None:
        """
        Register app-level callbacks.

        Includes
        --------
        - Routing container updates
        - Sidebar updates
        - Theme switcher: toggles the Bootstrap theme between dark and light
        """
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname"),
        )
        def _display_page(_pathname: Optional[str]):
            return dash.page_container

        @self.app.callback(
            Output("sidebar-content", "children"),
            Input("url", "pathname"),
            Input("apply-calibration-store", "data"),
        )
        def _update_sidebar(_url: Optional[str], sidebar_data: Any):
            return sidebar_html(sidebar_data)

        @self.app.callback(
            Output("theme-link", "href"),
            Output("theme-store", "data"),
            Input("theme-switch", "value"),
        )
        def _toggle_theme(is_dark: bool):
            """
            Toggle theme based on switch state.

            Parameters
            ----------
            is_dark:
                True means dark theme, False means light theme.

            Returns
            -------
            tuple[str, dict]
                - href for the Bootstrap CSS link
                - a small session store payload describing the theme
            """
            if bool(is_dark):
                return self._theme_dark, {"theme": "dark"}
            return self._theme_light, {"theme": "light"}

    def _set_layout(self) -> None:
        """
        Build the full application layout.

        Notes
        -----
        The theme switch is placed in a small header bar at the top right.
        Default is dark mode.
        """
        main_content = html.Div(
            dash.page_container,
            id="page-content",
            style=styling.CONTENT,
        )

        sidebar_content = html.Div(
            id="sidebar-content",
            style=styling.SIDEBAR,
        )

        mesf_default_table = self.create_table_from_dict(
            json_path="RosettaX/data/settings/saved_mesf_values.json"
        )

        theme_header = html.Div(
            [
                html.Div(
                    [
                        html.Span("Dark mode", style={"marginRight": "10px"}),
                        dbc.Switch(
                            id="theme-switch",
                            value=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                )
            ],
            style={
                "position": "fixed",
                "top": "10px",
                "right": "16px",
                "zIndex": 1100,
                "padding": "6px 10px",
                "borderRadius": "10px",
            },
        )

        self.app.layout = html.Div(
            [
                dcc.Location(id="url"),
                dcc.Store(
                    id="theme-store",
                    data={"theme": "dark"},
                    storage_type="session",
                ),
                dcc.Store(
                    data={"Fluorescent": [], "Scattering": []},
                    id="apply-calibration-store",
                    storage_type="session",
                ),
                dcc.Store(
                    data=mesf_default_table,
                    id="MESF-default_table-store",
                    storage_type="session",
                ),
                html.Link(id="theme-link", rel="stylesheet", href=self._theme_dark),
                theme_header,
                sidebar_content,
                main_content,
            ]
        )

    def run(self) -> None:
        """
        Start the Dash server, optionally opening the browser.
        """
        if self.open_browser:
            Timer(1, self._open_browser).start()

        self.app.run(
            host=self.host,
            port=self.port,
        )

    def _open_browser(self) -> None:
        """
        Open the app URL in a new browser window.
        """
        webbrowser.open_new(f"http://{self.host}:{self.port}")


def main(argv: Optional[list[str]] = None) -> None:
    """
    CLI entrypoint.
    """
    args = _parse_args(argv)
    apply_cli_to_runtime_config(args)

    app = RosettaXApplication(
        host=str(args.host),
        port=int(args.port),
        open_browser=not bool(args.no_browser),
    )

    app.run()


if __name__ == "__main__":
    main()