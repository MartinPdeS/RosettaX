# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
from dash import Dash
from dash import Input
from dash import Output

from RosettaX.application.layout import THEME_DARK
from RosettaX.application.layout import THEME_LIGHT
from RosettaX.pages.sidebar.main import SidebarIds
from RosettaX.pages.sidebar.main import sidebar_html
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


LOGO_LIGHT = "/assets/logo_light.png"
LOGO_DARK = "/assets/logo_dark.png"


def register_application_callbacks(app: Dash) -> None:
    """
    Register application-level Dash callbacks.
    """
    logger.debug("Registering app-level callbacks")

    @app.callback(
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
            return THEME_LIGHT, {"theme": "light"}

        return THEME_DARK, {"theme": "dark"}

    @app.callback(
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

    @app.callback(
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

    @app.callback(
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
            return LOGO_LIGHT

        logger.debug("Using dark theme logo")
        return LOGO_DARK