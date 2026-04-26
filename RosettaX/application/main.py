# -*- coding: utf-8 -*-

import logging
import sys
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Optional

import dash

from RosettaX.application.callbacks import register_application_callbacks
from RosettaX.application.layout import build_application_layout
from RosettaX.application.pages import register_pages
from RosettaX.application.routes import register_server_routes
from RosettaX.pages.sidebar.main import register_sidebar_callbacks
from RosettaX.utils.parser import _parse_args


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

    application = RosettaXApplication(
        host=str(parsed_arguments.host),
        port=int(parsed_arguments.port),
        open_browser=not bool(parsed_arguments.no_browser),
    )
    application.run()