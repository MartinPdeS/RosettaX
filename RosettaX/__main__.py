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
from flask import Response

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


def _resolve_calibration_file_path(folder: str, file_name: str) -> Path:
    """
    Resolve a calibration JSON file path safely within the allowed calibration folders.
    """
    normalized_folder = str(folder).strip().lower()

    if normalized_folder == "fluorescence":
        base_directory = Path(directories.fluorescence_calibration)
    elif normalized_folder == "scattering":
        base_directory = Path(directories.scattering_calibration)
    else:
        raise ValueError(f"Unsupported calibration folder: {folder}")

    resolved_path = (base_directory / file_name).resolve()
    resolved_base_directory = base_directory.resolve()

    if resolved_base_directory not in resolved_path.parents:
        raise ValueError("Invalid calibration file path.")

    return resolved_path


class RosettaXApplication:
    """
    Main Dash application for RosettaX.

    Responsibilities
    ----------------
    - Instantiate the Dash app.
    - Import and register all Dash page modules.
    - Register application-level callbacks.
    - Register Flask routes that should not go through Dash page routing.
    - Build the global layout.
    - Start the server.

    Notes
    -----
    This module only manages application-level behavior and shared state.
    Page-specific logic must remain in the relevant page modules.
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

        self._register_server_routes()
        register_sidebar_callbacks()
        self._register_callbacks()
        self._set_layout()

    def _register_pages(self) -> None:
        """
        Import all Dash page modules after Dash app instantiation.

        The calibration JSON viewer is intentionally not a Dash page anymore.
        It is served through a Flask route so opening a calibration record does not
        disturb the current Dash route or theme state.
        """
        page_modules = [
            "RosettaX.pages.home.main",
            "RosettaX.pages.fluorescence.main",
            "RosettaX.pages.scattering.main",
            "RosettaX.pages.calibrate.main",
            "RosettaX.pages.settings.main",
            "RosettaX.pages.help.main",
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

    def _register_server_routes(self) -> None:
        """
        Register Flask routes that should bypass Dash page routing.
        """
        logger.debug("Registering Flask server routes")

        @self.app.server.route("/calibration-json/<folder>/<path:file_name>")
        def serve_calibration_json(folder: str, file_name: str):
            logger.debug(
                "serve_calibration_json called with folder=%r file_name=%r",
                folder,
                file_name,
            )

            try:
                calibration_file_path = _resolve_calibration_file_path(folder, file_name)
                calibration_record = json.loads(
                    calibration_file_path.read_text(encoding="utf-8")
                )

                formatted_json = json.dumps(
                    calibration_record,
                    indent=4,
                    ensure_ascii=False,
                )

                safe_title = f"{folder} / {file_name}"

                html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{safe_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 24px;
            background: #ffffff;
            color: #111111;
        }}
        h2 {{
            margin: 0 0 8px 0;
        }}
        .subtitle {{
            opacity: 0.72;
            margin-bottom: 18px;
        }}
        pre {{
            white-space: pre-wrap;
            word-break: break-word;
            font-family: Menlo, Monaco, Consolas, monospace;
            font-size: 14px;
            background: #f6f8fa;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            padding: 16px;
            margin: 0;
        }}
    </style>
</head>
<body>
    <h2>Calibration JSON</h2>
    <div class="subtitle">{safe_title}</div>
    <pre>{formatted_json}</pre>
</body>
</html>
"""
                return Response(html_document, mimetype="text/html")

            except Exception as exc:
                logger.exception(
                    "Failed to serve calibration JSON for folder=%r file_name=%r",
                    folder,
                    file_name,
                )

                error_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Could not open calibration</title>
</head>
<body>
    <h2>Could not open calibration</h2>
    <pre>{type(exc).__name__}: {exc}</pre>
</body>
</html>
"""
                return Response(error_document, mimetype="text/html", status=400)

    def _register_callbacks(self) -> None:
        """
        Register application-level Dash callbacks.
        """
        logger.debug("Registering app-level callbacks")

        @self.app.callback(
            Output("theme-link", "href"),
            Output("theme-store", "data"),
            Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_theme_from_runtime_config(runtime_config_data: Any):
            logger.debug(
                "sync_theme_from_runtime_config called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )
            theme_mode = runtime_config.get_theme_mode(default="dark")

            logger.debug(
                "sync_theme_from_runtime_config resolved theme_mode=%r",
                theme_mode,
            )

            if theme_mode == "light":
                return self._theme_light, {"theme": "light"}

            return self._theme_dark, {"theme": "dark"}

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
                logger.debug("No selected profile from sidebar. Leaving runtime config unchanged.")
                return dash.no_update

            try:
                selected_profile_name = str(selected_profile_from_sidebar).strip()

                if not selected_profile_name:
                    logger.debug("Selected profile name is empty after stripping.")
                    return dash.no_update

                runtime_config = RuntimeConfig.from_profile_name(selected_profile_name)

                logger.debug(
                    "Loaded runtime config payload from sidebar profile=%r",
                    selected_profile_name,
                )
                return runtime_config.to_dict()

            except Exception:
                logger.exception(
                    "Failed to load runtime config from sidebar selected_profile=%r",
                    selected_profile_from_sidebar,
                )
                return dash.no_update

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

            if theme_name == "light":
                logger.debug("Using light theme logo")
                return self._logo_light

            logger.debug("Using dark theme logo")
            return self._logo_dark

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

    def _build_stores(self) -> list:
        """
        Build global application stores.

        Only truly global stores should exist here.
        """
        logger.debug("Building application stores")

        runtime_config = RuntimeConfig.from_default_profile()
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
                storage_type="local",
            ),
            dcc.Store(
                id="apply-calibration-store",
                data=0,
                storage_type="session",
            ),
            dcc.Store(
                id="runtime-config-store",
                storage_type="session",
                data=runtime_config_payload,
            ),
        ]

    def _build_theme_link(self) -> html.Link:
        runtime_config = RuntimeConfig.from_default_profile()
        initial_theme_mode = runtime_config.get_theme_mode(default="dark")
        initial_theme_href = (
            self._theme_light if initial_theme_mode == "light" else self._theme_dark
        )

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

        main_content = self._build_main_content()
        sidebar_content = self._build_sidebar_content()
        theme_link = self._build_theme_link()
        stores = self._build_stores()

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
            debug=False,
        )

    def _open_browser(self) -> None:
        application_url = f"http://{self.host}:{self.port}/home"
        logger.debug("Opening browser at application_url=%r", application_url)
        webbrowser.open_new(application_url)


def main(argv: Optional[list[str]] = None) -> None:
    logger.debug("Entering main with argv=%r", argv)

    parsed_arguments = _parse_args(argv)

    application = RosettaXApplication(
        host=str(parsed_arguments.host),
        port=int(parsed_arguments.port),
        open_browser=not bool(parsed_arguments.no_browser),
    )
    application.run()


if __name__ == "__main__":
    main()