# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


THEME_LIGHT = dbc.themes.FLATLY
THEME_DARK = dbc.themes.SLATE


def build_main_content() -> html.Div:
    """
    Build the main page container.
    """
    logger.debug("Building main content container")

    return html.Div(
        dash.page_container,
        id="page-content",
        style=styling.CONTENT,
    )


def build_sidebar_content() -> html.Div:
    """
    Build the sidebar container.

    The actual sidebar children are populated by the application level sidebar
    callback so the sidebar can be refreshed when route or calibration state changes.
    """
    logger.debug("Building sidebar content container")

    return html.Div(
        id="sidebar-content",
        style=styling.SIDEBAR,
    )


def build_stores() -> tuple[list[Any], str]:
    """
    Build global application stores and return initial theme mode.

    Only truly global stores should exist here.

    Returns
    -------
    tuple[list[Any], str]
        A tuple of ``(stores, initial_theme_mode)`` so callers can reuse the
        already-loaded runtime config without reading the profile twice.
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

    stores = [
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

    return stores, initial_theme_mode


def build_theme_link(initial_theme_mode: str = "dark") -> html.Link:
    """
    Build the Bootstrap theme stylesheet link.

    Parameters
    ----------
    initial_theme_mode : str
        Theme mode string (``"dark"`` or ``"light"``).  Defaults to ``"dark"``.
        Pass the value already resolved by :func:`build_stores` to avoid
        loading the default profile a second time.
    """
    if initial_theme_mode == "light":
        initial_theme_href = THEME_LIGHT
    else:
        initial_theme_href = THEME_DARK

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


def build_application_layout() -> html.Div:
    """
    Build the root Dash layout.
    """
    logger.debug("Building application layout")

    main_content = build_main_content()
    sidebar_content = build_sidebar_content()
    stores, initial_theme_mode = build_stores()
    theme_link = build_theme_link(initial_theme_mode)

    layout = html.Div(
        [
            dcc.Location(id="url"),
            *stores,
            theme_link,
            sidebar_content,
            main_content,
        ]
    )

    logger.debug("Application layout built successfully")

    return layout