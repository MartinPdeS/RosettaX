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

from RosettaX.pages.sidebar.main import SidebarIds, register_sidebar_callbacks, sidebar_html
from RosettaX.utils import directories, styling
from RosettaX.utils.parser import _parse_args
from RosettaX.utils.runtime_config import RuntimeConfig


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

    Design
    ------
    - The active theme is driven by the runtime profile only.
    - There is no UI theme toggle here.
    - The theme stylesheet, theme store, and sidebar logo are all derived from
      the same resolved theme mode.
    """

    _theme_light = dbc.themes.FLATLY
    _theme_dark = dbc.themes.SLATE

    _logo_light = "/assets/logo_light.png"
    _logo_dark = "/assets/logo_dark.png"

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
            external_stylesheets=[],
            use_pages=True,
            pages_folder="",
            suppress_callback_exceptions=True,
        )

        logger.debug("Dash application instantiated")

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
        Build the default MESF table from a runtime config payload.

        Supported schemas
        -----------------
        - Nested schema: calibration.mesf_values
        - Legacy flat schema: mesf_values
        """
        logger.debug("Building MESF default table from runtime config payload")

        try:
            if not isinstance(runtime_config_payload, dict):
                logger.warning(
                    "runtime_config_payload is not a dictionary. Got type=%r",
                    type(runtime_config_payload).__name__,
                )
                return [{"col1": "", "col2": ""}]

            calibration_section = runtime_config_payload.get("calibration", {})
            if isinstance(calibration_section, dict) and "mesf_values" in calibration_section:
                mesf_values = calibration_section.get("mesf_values", [])
            else:
                mesf_values = runtime_config_payload.get("mesf_values", [])

            if isinstance(mesf_values, str):
                mesf_candidates = [item.strip() for item in mesf_values.split(",")]
            elif isinstance(mesf_values, (list, tuple)):
                mesf_candidates = [str(item).strip() for item in mesf_values]
            else:
                mesf_candidates = []

            table_data: list[dict[str, str]] = [
                {"col1": value, "col2": ""}
                for value in mesf_candidates
                if value
            ]

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

    def _resolve_theme_mode_from_payload(self, runtime_config_payload: Any) -> str:
        """
        Resolve theme mode from a runtime payload.

        The runtime config may follow the nested schema:
            app.theme_mode

        Fallback to RuntimeConfig helper if needed.
        """
        if isinstance(runtime_config_payload, dict):
            app_section = runtime_config_payload.get("app", {})
            if isinstance(app_section, dict):
                theme_mode = str(app_section.get("theme_mode", "")).strip().lower()
                if theme_mode in {"light", "dark"}:
                    logger.debug(
                        "Resolved theme mode=%r from runtime payload app section",
                        theme_mode,
                    )
                    return theme_mode

            legacy_theme_mode = str(runtime_config_payload.get("theme_mode", "")).strip().lower()
            if legacy_theme_mode in {"light", "dark"}:
                logger.debug(
                    "Resolved legacy theme mode=%r from runtime payload root",
                    legacy_theme_mode,
                )
                return legacy_theme_mode

        runtime_config = RuntimeConfig()
        theme_mode = runtime_config.get_theme_mode(default="dark")
        logger.debug(
            "Resolved theme mode=%r from RuntimeConfig helper fallback",
            theme_mode,
        )
        return theme_mode if theme_mode in {"light", "dark"} else "dark"

    def _theme_href_from_mode(self, theme_mode: str) -> str:
        resolved_theme_mode = str(theme_mode).strip().lower()
        return self._theme_light if resolved_theme_mode == "light" else self._theme_dark

    def _logo_src_from_mode(self, theme_mode: str) -> str:
        resolved_theme_mode = str(theme_mode).strip().lower()
        return self._logo_light if resolved_theme_mode == "light" else self._logo_dark

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
        def update_sidebar(
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
            Output("theme-store", "data"),
            Output("theme-link", "href"),
            Input(SidebarIds.selected_profile_store, "data"),
            prevent_initial_call=True,
        )
        def load_runtime_config_from_sidebar_profile(
            selected_profile_from_sidebar: Optional[str],
        ):
            logger.debug(
                "load_runtime_config_from_sidebar_profile called with selected_profile_from_sidebar=%r",
                selected_profile_from_sidebar,
            )

            if not selected_profile_from_sidebar:
                logger.debug("No selected profile from sidebar. Leaving stores unchanged.")
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

            try:
                selected_profile_file_name = str(selected_profile_from_sidebar).strip()

                if not selected_profile_file_name:
                    logger.debug("Selected profile file name was empty after stripping.")
                    return (
                        dash.no_update,
                        dash.no_update,
                        dash.no_update,
                        dash.no_update,
                    )

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

                if not isinstance(runtime_config_payload, dict):
                    raise TypeError(
                        f"Profile JSON must contain a dictionary, got {type(runtime_config_payload).__name__}."
                    )

                logger.debug(
                    "Loaded runtime config payload from sidebar profile=%r type=%r",
                    selected_profile_file_name,
                    type(runtime_config_payload).__name__,
                )

                runtime_config = RuntimeConfig()
                runtime_config.Default.load_dict(runtime_config_payload)

                logger.debug(
                    "Updated RuntimeConfig singleton from sidebar profile=%r",
                    selected_profile_file_name,
                )

                mesf_default_table = self.create_mesf_default_table_from_runtime_payload(
                    runtime_config_payload=runtime_config_payload,
                )

                resolved_theme_mode = self._resolve_theme_mode_from_payload(runtime_config_payload)
                resolved_theme_href = self._theme_href_from_mode(resolved_theme_mode)

                logger.debug(
                    "Returning updated runtime config, MESF table, and theme mode=%r",
                    resolved_theme_mode,
                )

                return (
                    runtime_config_payload,
                    mesf_default_table,
                    {"theme": resolved_theme_mode},
                    resolved_theme_href,
                )

            except Exception:
                logger.exception(
                    "Failed to load runtime config from sidebar selected profile=%r",
                    selected_profile_from_sidebar,
                )
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                )

        @self.app.callback(
            Output("sidebar-logo", "src"),
            Input("theme-store", "data"),
        )
        def update_sidebar_logo(theme_store_data: Any):
            logger.debug("Updating sidebar logo with theme_store_data=%r", theme_store_data)

            if isinstance(theme_store_data, dict):
                theme_name = str(theme_store_data.get("theme", "dark")).strip().lower()
            else:
                theme_name = "dark"

            resolved_logo = self._logo_src_from_mode(theme_name)
            logger.debug("Resolved sidebar logo=%r for theme=%r", resolved_logo, theme_name)
            return resolved_logo

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

    def _build_stores(self, *, mesf_default_table: list[dict[str, str]]) -> list:
        logger.debug(
            "Building application stores with %d MESF default rows",
            len(mesf_default_table),
        )

        runtime_config = RuntimeConfig()
        runtime_config_payload = runtime_config.to_dict()
        initial_theme_mode = runtime_config.get_theme_mode(default="dark")

        logger.debug(
            "Runtime config payload prepared for storage with type=%r initial_theme_mode=%r",
            type(runtime_config_payload).__name__,
            initial_theme_mode,
        )

        return [
            dcc.Store(
                id="theme-store",
                data={"theme": initial_theme_mode},
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
                data=runtime_config_payload,
                storage_type="session",
            ),
        ]

    def _build_theme_link(self) -> html.Link:
        runtime_config = RuntimeConfig()
        initial_theme_mode = runtime_config.get_theme_mode(default="dark")
        initial_theme_href = self._theme_href_from_mode(initial_theme_mode)

        logger.debug(
            "Building theme link with initial_theme_mode=%r initial_theme_href=%r",
            initial_theme_mode,
            initial_theme_href,
        )

        return html.Link(
            id="theme-link",
            rel="stylesheet",
            href=initial_theme_href,
        )

    def _set_layout(self) -> None:
        logger.debug("Building application layout")

        mesf_default_table = self.create_mesf_default_table_from_runtime_config()

        main_content = self._build_main_content()
        sidebar_content = self._build_sidebar_content()
        theme_link = self._build_theme_link()
        stores = self._build_stores(mesf_default_table=mesf_default_table)

        self.app.layout = html.Div(
            [
                dcc.Location(id="url"),
                *stores,
                theme_link,
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