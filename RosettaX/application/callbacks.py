
import logging
from typing import Any

import dash
from dash import MATCH, Dash, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import request as flask_request

from RosettaX.application.layout import THEME_DARK, THEME_LIGHT
from RosettaX.pages.p00_sidebar.main import SidebarIds, sidebar_html
from RosettaX.utils import usage_metrics
from RosettaX.utils.browser_profiles import (
    BROWSER_PROFILES_STORE_ID,
    BrowserProfileLibrary,
)
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow import calibration_cards

logger = logging.getLogger(__name__)


def resolve_active_profile_runtime_config(
    browser_profiles_payload: Any,
    selected_profile_name: Any,
) -> dict[str, Any] | None:
    """Return the browser profile that determines initial workflow card state."""
    browser_profiles = BrowserProfileLibrary.from_dict(browser_profiles_payload)
    return browser_profiles.get_profile_payload(
        str(selected_profile_name) if selected_profile_name else None
    )


def resolve_client_ip_address() -> str:
    """
    Resolve the client IP address for the in-flight request.

    Prefers the first entry of the X-Forwarded-For header so deployments
    behind a reverse proxy still record the originating address.
    """
    forwarded_for = str(flask_request.headers.get("X-Forwarded-For", "")).strip()

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return str(flask_request.remote_addr or "").strip()


def record_request_page_visit(pathname: Any) -> None:
    """
    Record one page visit for the in-flight request.

    Safe to call outside a request context: client metadata is left empty.
    """
    ip_address = ""
    user_agent = ""

    try:
        ip_address = resolve_client_ip_address()
        user_agent = str(flask_request.headers.get("User-Agent", ""))
    except RuntimeError:
        logger.debug("Recording page visit without request context metadata.")

    try:
        usage_metrics.record_page_visit(
            ip_address=ip_address,
            path=str(pathname or "/"),
            user_agent=user_agent,
        )
    except Exception:
        logger.exception("Failed to record page visit for pathname=%r", pathname)


LOGO_LIGHT = "/assets/logo/logo_light.svg"
LOGO_DARK = "/assets/logo/logo_dark.svg"


def register_application_callbacks(app: Dash) -> None:
    """
    Register application-level Dash callbacks.
    """
    logger.debug("Registering app-level callbacks")

    @app.callback(
        Output(
            {"type": calibration_cards.COLLAPSE_ID_TYPE, "page": MATCH, "section": MATCH},
            "is_open",
        ),
        Output(
            {"type": calibration_cards.TOGGLE_LABEL_ID_TYPE, "page": MATCH, "section": MATCH},
            "children",
        ),
        Input(
            {"type": calibration_cards.TOGGLE_ID_TYPE, "page": MATCH, "section": MATCH},
            "n_clicks",
        ),
        Input(
            {
                "type": calibration_cards.WORKFLOW_STEP_CARD_ID_TYPE,
                "page": MATCH,
                "section": MATCH,
            },
            "n_clicks",
        ),
        Input(BROWSER_PROFILES_STORE_ID, "data"),
        Input(SidebarIds.selected_profile_store, "data"),
        State(
            {"type": calibration_cards.COLLAPSE_ID_TYPE, "page": MATCH, "section": MATCH},
            "is_open",
        ),
        prevent_initial_call=True,
    )
    def toggle_calibration_card(
        toggle_clicks: Any,
        workflow_step_clicks: Any,
        browser_profiles_payload: Any,
        selected_profile_name: Any,
        is_open: Any,
    ) -> tuple[bool, str]:
        triggered_id = dash.ctx.triggered_id
        active_profile_config = None

        if not isinstance(triggered_id, dict):
            active_profile_config = resolve_active_profile_runtime_config(
                browser_profiles_payload,
                selected_profile_name,
            )
            if active_profile_config is None:
                raise PreventUpdate

        result = calibration_cards.resolve_card_toggle(
            triggered_id=triggered_id,
            is_open=is_open,
            runtime_config_data=active_profile_config,
            toggle_clicks=toggle_clicks,
            workflow_step_clicks=workflow_step_clicks,
        )
        if result is None:
            raise PreventUpdate

        return result

    @app.callback(
        Output("visit-tracking-store", "data"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def track_page_visit(pathname: Any):
        record_request_page_visit(pathname)

        return dash.no_update

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
        Input("apply-calibration-store", "data"),
        prevent_initial_call=False,
    )
    def update_sidebar(
        sidebar_refresh_signal: Any,
    ):
        logger.debug(
            "Refreshing sidebar for sidebar_refresh_signal=%r",
            sidebar_refresh_signal,
        )

        return sidebar_html(None)

    @app.callback(
        Output("runtime-config-store", "data"),
        Input(SidebarIds.selected_profile_store, "data"),
        State(BROWSER_PROFILES_STORE_ID, "data"),
        prevent_initial_call=False,
    )
    def load_runtime_config_from_sidebar_profile(
        selected_profile_from_sidebar: str | None,
        browser_profiles_payload: Any,
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

            browser_profiles = BrowserProfileLibrary.from_dict(
                browser_profiles_payload,
            )
            selected_profile_payload = browser_profiles.get_profile_payload(
                selected_profile_name,
            )

            if selected_profile_payload is None:
                logger.debug(
                    "Selected browser profile was not found. Leaving runtime config unchanged. selected_profile_name=%r",
                    selected_profile_name,
                )
                return dash.no_update

            runtime_config = RuntimeConfig.from_dict(selected_profile_payload)

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
