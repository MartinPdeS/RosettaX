# -*- coding: utf-8 -*-

import importlib
import json
import logging
import sys
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.sidebar.main import SidebarIds, register_sidebar_callbacks, sidebar_html
from RosettaX.utils.parser import _parse_args
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import directories

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
    force=True,
)

logger = logging.getLogger(__name__)
logging.getLogger("RosettaX").setLevel(logging.DEBUG)


class RosettaXApplication:
    """
    Main Dash application for RosettaX.
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

        logger.debug(
            "Initializing RosettaXApplication with host=%r port=%r open_browser=%r",
            self.host,
            self.port,
            self.open_browser,
        )

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[self._theme_dark],
            use_pages=True,
            pages_folder="",
            suppress_callback_exceptions=True,
        )

        logger.debug("Dash application instantiated with default dark theme")

        self._register_pages()
        logger.debug("Registered Dash pages: %r", list(dash.page_registry.keys()))

        register_sidebar_callbacks()
        self._register_callbacks()
        self._set_layout()

    def _register_pages(self) -> None:
        """
        Import all page modules after Dash app instantiation.
        """
        page_modules = [
            "RosettaX.pages.home.main",
            "RosettaX.pages.settings.main",
            "RosettaX.pages.fluorescence.main",
            "RosettaX.pages.scattering.main",
            "RosettaX.pages.calibrate.main",
            "RosettaX.pages.help.main",
            "RosettaX.pages.calibration_json.main",
        ]

        logger.debug("Registering page modules")

        for module_name in page_modules:
            try:
                logger.debug("Importing page module=%r", module_name)
                importlib.import_module(module_name)
                logger.debug("Successfully imported page module=%r", module_name)
            except Exception:
                logger.exception("Failed to import page module=%r", module_name)
                raise

    @staticmethod
    def create_mesf_default_table_from_runtime_payload(
        *,
        runtime_config_payload: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Build the default MESF table from a runtime config payload dictionary.
        """
        logger.debug("Building MESF default table from runtime config payload")

        try:
            if not isinstance(runtime_config_payload, dict):
                logger.warning(
                    "runtime_config_payload is not a dictionary. Got type=%r",
                    type(runtime_config_payload).__name__,
                )
                return [{"col1": "", "col2": ""}]

            table_data: list[dict[str, str]] = []

            for key, value in runtime_config_payload.items():
                if not isinstance(value, dict):
                    logger.debug(
                        "Skipping non-dictionary runtime config entry: key=%r value=%r",
                        key,
                        value,
                    )
                    continue

                if not value.get("default", True):
                    logger.debug("Skipping non-default entry: key=%r", key)
                    continue

                mesf_values = value.get("mesf_values", "")

                if isinstance(mesf_values, str):
                    mesf_candidates = mesf_values.split(",")
                elif isinstance(mesf_values, (list, tuple)):
                    mesf_candidates = list(mesf_values)
                else:
                    logger.debug(
                        "Skipping entry with unsupported mesf_values type: key=%r type=%r",
                        key,
                        type(mesf_values).__name__,
                    )
                    continue

                for mesf_value in mesf_candidates:
                    mesf_clean = str(mesf_value).strip()
                    if mesf_clean:
                        table_data.append({"col1": mesf_clean, "col2": ""})

            if not table_data:
                logger.warning(
                    "No MESF defaults were found in runtime config payload. Using one blank row."
                )
                return [{"col1": "", "col2": ""}]

            logger.debug(
                "Built %d MESF default rows from runtime config payload",
                len(table_data),
            )
            return table_data

        except Exception:
            logger.exception("Failed to build MESF default table from runtime config payload")
            return [{"col1": "", "col2": ""}]

    @classmethod
    def create_mesf_default_table_from_runtime_config(cls) -> list[dict[str, str]]:
        """
        Build the default MESF table from the RuntimeConfig singleton.
        """
        logger.debug("Building MESF default table from RuntimeConfig singleton")
        return cls.create_mesf_default_table_from_runtime_payload(
            runtime_config_payload=RuntimeConfig().to_dict(),
        )

    def _register_callbacks(self) -> None:
        """
        Register application-level Dash callbacks.
        """
        logger.debug("Registering app-level callbacks")

        @self.app.callback(
            Output("sidebar-content", "children"),
            Input("url", "pathname"),
            Input("apply-calibration-store", "data"),
        )
        def _update_sidebar(
            pathname: Optional[str],
            sidebar_refresh_signal: Any,
        ):
            logger.debug(
                "Refreshing sidebar for pathname=%r sidebar_refresh_signal=%r",
                pathname,
                sidebar_refresh_signal,
            )
            return sidebar_html(None)

        @self.app.callback(
            Output("runtime-config-store", "data", allow_duplicate=True),
            Output("MESF-default_table-store", "data"),
            Input(SidebarIds.selected_profile_store, "data"),
            prevent_initial_call=True,
        )
        def _load_runtime_config_from_sidebar_profile(
            selected_profile_from_sidebar: Optional[str],
        ):
            logger.debug(
                "_load_runtime_config_from_sidebar_profile called with selected_profile_from_sidebar=%r",
                selected_profile_from_sidebar,
            )

            if not selected_profile_from_sidebar:
                logger.debug("No selected profile from sidebar. Leaving stores unchanged.")
                return dash.no_update, dash.no_update

            try:
                selected_profile_file_name = str(selected_profile_from_sidebar).strip()

                if not selected_profile_file_name:
                    logger.debug("Selected profile file name was empty after stripping.")
                    return dash.no_update, dash.no_update

                if not selected_profile_file_name.endswith(".json"):
                    selected_profile_file_name = f"{selected_profile_file_name}.json"

                resolved_profile_path = Path(directories.profiles).resolve() / selected_profile_file_name
                logger.debug(
                    "Resolved sidebar selected profile path=%r",
                    str(resolved_profile_path),
                )

                if not resolved_profile_path.exists():
                    raise FileNotFoundError(f"Profile does not exist: {resolved_profile_path}")

                runtime_config_payload = json.loads(
                    resolved_profile_path.read_text(encoding="utf-8")
                )

                logger.debug(
                    "Loaded runtime config payload from sidebar profile=%r type=%r",
                    selected_profile_file_name,
                    type(runtime_config_payload).__name__,
                )

                mesf_default_table = self.create_mesf_default_table_from_runtime_payload(
                    runtime_config_payload=runtime_config_payload,
                )

                logger.debug(
                    "Returning updated runtime config and MESF table with row_count=%r",
                    len(mesf_default_table),
                )

                return runtime_config_payload, mesf_default_table

            except Exception:
                logger.exception(
                    "Failed to load runtime config from sidebar selected profile=%r",
                    selected_profile_from_sidebar,
                )
                return dash.no_update, dash.no_update

        @self.app.callback(
            Output("theme-link", "href"),
            Output("theme-store", "data"),
            Input("theme-switch", "value"),
        )
        def _toggle_theme(is_dark: bool):
            logger.debug("Theme toggle callback called with is_dark=%r", is_dark)

            if bool(is_dark):
                logger.debug("Applying dark theme")
                return self._theme_dark, {"theme": "dark"}

            logger.debug("Applying light theme")
            return self._theme_light, {"theme": "light"}

    def _build_main_content(self) -> html.Div:
        logger.debug("Building main content container")

        return html.Div(
            dash.page_container,
            id="page-content",
            style=styling.CONTENT,
        )

    def _build_sidebar_content(self) -> html.Div:
        logger.debug("Building sidebar content container")

        return html.Div(
            id="sidebar-content",
            style=styling.SIDEBAR,
        )

    def _build_theme_header(self) -> html.Div:
        logger.debug("Building theme header with default dark mode enabled")

        return html.Div(
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

    def _build_stores(self, *, mesf_default_table: list[dict[str, str]]) -> list:
        logger.debug(
            "Building application stores with %d MESF default rows",
            len(mesf_default_table),
        )

        runtime_config_payload = RuntimeConfig().to_dict()

        logger.debug(
            "Runtime config payload prepared for storage with type=%r",
            type(runtime_config_payload).__name__,
        )

        return [
            dcc.Store(
                id="theme-store",
                data={"theme": "dark"},
                storage_type="session",
            ),
            dcc.Store(
                id="apply-calibration-store",
                data=0,
                storage_type="session",
            ),
            dcc.Store(
                id="MESF-default_table-store",
                data=mesf_default_table,
                storage_type="session",
            ),
            dcc.Store(
                id="runtime-config-store",
                storage_type="session",
                data=runtime_config_payload,
            ),
        ]

    def _build_theme_link(self) -> html.Link:
        logger.debug("Building theme link with default dark theme href")

        return html.Link(
            id="theme-link",
            rel="stylesheet",
            href=self._theme_dark,
        )

    def _set_layout(self) -> None:
        logger.debug("Building application layout")

        mesf_default_table = self.create_mesf_default_table_from_runtime_config()

        main_content = self._build_main_content()
        sidebar_content = self._build_sidebar_content()
        theme_header = self._build_theme_header()
        theme_link = self._build_theme_link()
        stores = self._build_stores(mesf_default_table=mesf_default_table)

        self.app.layout = html.Div(
            [
                dcc.Location(id="url"),
                *stores,
                theme_link,
                theme_header,
                sidebar_content,
                main_content,
            ]
        )

        logger.debug("Application layout built successfully")

    def run(self) -> None:
        logger.debug(
            "Starting Dash server with host=%r port=%r open_browser=%r",
            self.host,
            self.port,
            self.open_browser,
        )

        if self.open_browser:
            logger.debug("Browser auto-open requested. Scheduling browser launch.")
            Timer(1, self._open_browser).start()

        self.app.run(
            host=self.host,
            port=self.port,
            debug=True,
        )

    def _open_browser(self) -> None:
        url = f"http://{self.host}:{self.port}/home"
        logger.debug("Opening browser at url=%r", url)
        webbrowser.open_new(url)


def main(argv: Optional[list[str]] = None) -> None:
    logger.debug("Entering main with argv=%r", argv)

    args = _parse_args(argv)

    runtime_config = RuntimeConfig()
    logger.debug("Loading runtime configuration from default_profile.json")
    runtime_config.load_json("default_profile.json")

    app = RosettaXApplication(
        host=str(args.host),
        port=int(args.port),
        open_browser=not bool(args.no_browser),
    )
    app.run()


if __name__ == "__main__":
    main()