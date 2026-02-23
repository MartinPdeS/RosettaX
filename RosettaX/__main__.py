import argparse
import json
import webbrowser
from threading import Timer
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.sidebar import sidebar_html
from RosettaX.pages.runtime_config import get_ui_flags


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="RosettaX")

    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser tab on startup.",
    )

    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-debug", dest="debug", action="store_false")
    parser.set_defaults(debug=None)

    # Visibility toggles
    parser.add_argument("--show_scattering_controls", action="store_true", default=None)
    parser.add_argument("--hide_scattering_controls", dest="show_scattering_controls", action="store_false")

    parser.add_argument("--show_threshold_controls", action="store_true", default=None)
    parser.add_argument("--hide_threshold_controls", dest="show_threshold_controls", action="store_false")

    parser.add_argument("--show_fluorescence", action="store_true", default=None)
    parser.add_argument("--hide_fluorescence", dest="show_fluorescence", action="store_false")

    parser.add_argument("--show_beads", action="store_true", default=None)
    parser.add_argument("--hide_beads", dest="show_beads", action="store_false")

    parser.add_argument("--show_output", action="store_true", default=None)
    parser.add_argument("--hide_output", dest="show_output", action="store_false")

    parser.add_argument("--show_save", action="store_true", default=None)
    parser.add_argument("--hide_save", dest="show_save", action="store_false")

    # Per section debug
    parser.add_argument("--debug_scattering", action="store_true", default=None)
    parser.add_argument("--no_debug_scattering", dest="debug_scattering", action="store_false")

    parser.add_argument("--debug_fluorescence", action="store_true", default=None)
    parser.add_argument("--no_debug_fluorescence", dest="debug_fluorescence", action="store_false")

    return parser.parse_args(argv)


def apply_cli_to_ui_flags(args: argparse.Namespace) -> None:
    ui_flags = get_ui_flags()

    if args.debug is not None:
        ui_flags.debug = bool(args.debug)
        ui_flags.mark_explicit("debug")

    def _set(field_name: str, value: object | None) -> None:
        if value is None:
            return
        setattr(ui_flags, field_name, bool(value))
        ui_flags.mark_explicit(field_name)

    _set("fluorescence_show_scattering_controls", args.show_scattering_controls)
    _set("fluorescence_show_threshold_controls", args.show_threshold_controls)
    _set("fluorescence_show_fluorescence_controls", args.show_fluorescence)
    _set("fluorescence_show_beads_controls", args.show_beads)
    _set("fluorescence_show_output_controls", args.show_output)
    _set("fluorescence_show_save_controls", args.show_save)

    _set("fluorescence_debug_scattering", args.debug_scattering)
    _set("fluorescence_debug_fluorescence", args.debug_fluorescence)

    ui_flags.apply_policy()


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
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            use_pages=True,
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
    apply_cli_to_ui_flags(args)

    app = RosettaXApplication(
        host=str(args.host),
        port=int(args.port),
        open_browser=not bool(args.no_browser),
    )

    app.run()


if __name__ == "__main__":
    main()