# -*- coding: utf-8 -*-

import logging
import sys
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Optional

import dash

from .callbacks import register_application_callbacks
from .layout import build_application_layout
from .pages import register_pages
from .routes import register_server_routes
from RosettaX.pages.p00_sidebar.main import register_sidebar_callbacks
from RosettaX.utils.parser import _parse_args

logger = logging.getLogger(__name__)


def configure_logging(*, debug: bool, log_level: str) -> int:
    """
    Configure application logging and return the resolved log level.
    """
    normalized_log_level_name = str(log_level or "INFO").strip().upper() or "INFO"
    resolved_log_level = getattr(logging, normalized_log_level_name, logging.INFO)

    if debug:
        resolved_log_level = logging.DEBUG

    logging.basicConfig(
        level=resolved_log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("RosettaX").setLevel(resolved_log_level)

    return resolved_log_level


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
    This class only manages application-level behavior and shared state.
    Page-specific logic must remain in the relevant page modules.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        open_browser: bool,
        debug: bool,
    ) -> None:
        self.host = str(host)
        self.port = int(port)
        self.open_browser = bool(open_browser)
        self.debug = bool(debug)

        logger.debug(
            "Initializing RosettaXApplication with host=%r port=%r open_browser=%r debug=%r",
            self.host,
            self.port,
            self.open_browser,
            self.debug,
        )

        assets_folder = Path(__file__).resolve().parents[1] / "assets"

        logger.debug("Using Dash assets folder=%r", str(assets_folder))

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[],
            assets_folder=str(assets_folder),
            assets_url_path="/assets",
            use_pages=True,
            pages_folder="",
            suppress_callback_exceptions=True,
        )

        logger.debug("Dash application instantiated")

        register_pages()
        logger.debug("Registered Dash pages: %r", list(dash.page_registry.keys()))

        register_server_routes(self.app)
        register_sidebar_callbacks()
        register_application_callbacks(self.app)

        self.app.layout = build_application_layout()

    def run(self) -> None:
        """
        Start the Dash development server.
        """
        logger.debug(
            "Starting Dash server with host=%r port=%r open_browser=%r debug=%r",
            self.host,
            self.port,
            self.open_browser,
            self.debug,
        )

        if self.open_browser:
            logger.debug("Browser auto-open requested. Scheduling browser launch.")
            Timer(1, self._open_browser).start()

        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
        )

    def _open_browser(self) -> None:
        """
        Open the application in the default browser.
        """
        application_url = f"http://{self.host}:{self.port}/home"

        logger.debug("Opening browser at application_url=%r", application_url)

        webbrowser.open_new(application_url)


def main(argv: Optional[list[str]] = None) -> None:
    """
    Parse command line arguments and start the RosettaX application.
    """
    logger.debug("Entering main with argv=%r", argv)

    parsed_arguments = _parse_args(argv)
    debug_mode = bool(getattr(parsed_arguments, "debug", False))
    configure_logging(
        debug=debug_mode,
        log_level=str(getattr(parsed_arguments, "log_level", "INFO")),
    )

    application = RosettaXApplication(
        host=str(parsed_arguments.host),
        port=int(parsed_arguments.port),
        open_browser=not bool(parsed_arguments.no_browser),
        debug=debug_mode,
    )
    application.run()
