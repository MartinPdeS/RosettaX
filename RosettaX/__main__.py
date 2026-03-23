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
from RosettaX.pages.runtime_config import get_runtime_config, get_saved_profile


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
            external_stylesheets=[self._theme_light],
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
        
        # @self.app.callback(
        #     Output('current-profile-store', 'data'),
        #     Output('current-profile-data-store', 'data'),
        #     Input('current-profile-store', 'data'),
        #     Input('current-profile-data-store', 'data'),
        # )
        # def set_initial_json_cookie(_pathname: Optional[str], current_profile_data_store: Optional[dict[str, Any]]):
        #     print(_pathname, current_profile_data_store)
        #     if _pathname is None:
        #         json_name = "default_profile.json"
        #     else:
        #         json_name = _pathname
        #     if current_profile_data_store is None:
        #         profile_data = get_saved_profile(json_name)
        #     else:
        #         profile_data = current_profile_data_store
        #     return json_name, profile_data

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

        theme_header = html.Div(
            [
                html.Div(
                    [
                        html.Span("Dark mode", style={"marginRight": "10px"}),
                        dbc.Switch(
                            id="theme-switch",
                            value=False,
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
                    data={"theme": "light"},
                    storage_type="session",
                ),
                dcc.Store(
                    data={"Fluorescent": [], "Scattering": []},
                    id="apply-calibration-store",
                    storage_type="session",
                ),
                dcc.Store(id="current-profile-store", storage_type="local"),
                dcc.Store(id="current-profile-data-store", storage_type="local"),
                html.Link(id="theme-link", rel="stylesheet", href=self._theme_light),
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

    # args = _parse_args(argv)
    # apply_cli_to_runtime_config(args)
    runtime_config = get_runtime_config().load_json("default_profile.json")
    app = RosettaXApplication(
        host="127.0.0.1", # str(args.host),
        port=8050, # int(args.port),
        open_browser= True # not bool(args.no_browser),
    )

    app.run()


if __name__ == "__main__":
    main()