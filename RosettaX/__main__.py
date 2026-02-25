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
            external_stylesheets=[dbc.themes.FLATLY],
            use_pages=True,
            suppress_callback_exceptions=True
        )

        self._register_callbacks()
        self._set_layout()

    @staticmethod
    def create_table_from_dict(*, json_path: str) -> list[dict[str, str]]:
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
        @self.app.callback(
            Output("page-content", "children"),
            Input("url", "pathname"),
        )
        def display_page(_pathname: Optional[str]):
            return dash.page_container

        @self.app.callback(
            Output("sidebar-content", "children"),
            Input("url", "pathname"),
            Input("apply-calibration-store", "data"),
        )
        def update_sidebar(_url: Optional[str], sidebar_data: Any):
            return sidebar_html(sidebar_data)

    def _set_layout(self) -> None:
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

        self.app.layout = html.Div(
            [
                dcc.Location(id="url"),
                dcc.Store(
                    data={"Fluorescent": [], "Scatter": []},
                    id="apply-calibration-store",
                    storage_type="session",
                ),
                dcc.Store(
                    data=mesf_default_table,
                    id="MESF-default_table-store",
                    storage_type="session",
                ),
                sidebar_content,
                main_content,
            ]
        )

    def run(self) -> None:
        if self.open_browser:
            Timer(1, self._open_browser).start()

        self.app.run(
            host=self.host,
            port=self.port,
        )

    def _open_browser(self) -> None:
        webbrowser.open_new(f"http://{self.host}:{self.port}")


def main(argv: Optional[list[str]] = None) -> None:
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