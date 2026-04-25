# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from datetime import datetime, timezone

from RosettaX.pages.sidebar.ids import SidebarIds
from . import services
from RosettaX.utils import styling


logger = logging.getLogger(__name__)


class Sidebar:
    """
    Application sidebar.

    Responsibilities
    ----------------
    - Render the logo and main navigation.
    - Show saved profile controls.
    - Show saved calibration files grouped by category.
    - Let the user navigate to the calibration page with a selected calibration.
    - Expose small utility actions such as refresh and open folder.

    Notes
    -----
    Internal app navigation is always performed with ``dcc.Link(..., refresh=False)``
    so route changes stay inside Dash routing instead of triggering a full browser reload.
    """

    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo_light.png"
        self.logo_max_height_px = 156
        self.sidebar_width_px = 460
        self.style = styling.PAGE

        logger.debug(
            "Initialized Sidebar with sidebar_width_px=%r logo_src=%r",
            self.sidebar_width_px,
            self.logo_src,
        )

    def _get_default_profile_name(self, profile_options: list[dict[str, Any]]) -> Optional[str]:
        """
        Resolve the startup profile name shown in the sidebar.

        At application startup, RosettaX loads ``default_profile`` automatically.
        The sidebar should mirror that initial state if the profile exists.
        """
        option_values = [
            option.get("value")
            for option in profile_options
            if isinstance(option, dict) and option.get("value")
        ]

        if "default_profile" in option_values:
            return "default_profile"

        return option_values[0] if option_values else None

    def register_callbacks(self) -> None:
        """
        Register all sidebar callbacks.
        """
        logger.debug("Registering sidebar callbacks.")

        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_body_container, "children"),
            dash.Input(SidebarIds.saved_calibrations_refresh_button, "n_clicks"),
            dash.Input(SidebarIds.saved_calibrations_refresh_store, "data"),
            prevent_initial_call=True,
        )
        def refresh_saved_calibrations(
            refresh_button_clicks: Optional[int],
            refresh_signal: Any,
        ):
            logger.debug(
                "refresh_saved_calibrations called with refresh_button_clicks=%r refresh_signal=%r",
                refresh_button_clicks,
                refresh_signal,
            )

            saved_calibrations = services.list_saved_calibrations()

            logger.debug(
                "Loaded saved calibrations from disk with fluorescence=%d scattering=%d",
                len(saved_calibrations.get("fluorescence", [])),
                len(saved_calibrations.get("scattering", [])),
            )
            return self._build_saved_calibrations_body(saved_calibrations)

        @dash.callback(
            dash.Output(SidebarIds.saved_calibrations_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_calibrations_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_saved_calibrations_folder(n_clicks: Optional[int]):
            logger.debug(
                "open_saved_calibrations_folder called with n_clicks=%r",
                n_clicks,
            )
            del n_clicks

            try:
                return services.open_saved_calibrations_root()

            except Exception as exc:
                logger.exception("Failed to open calibration folder.")
                return f"Could not open calibration folder: {type(exc).__name__}: {exc}"

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_dropdown, "options"),
            dash.Input(SidebarIds.saved_profiles_refresh_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def refresh_saved_profiles(n_clicks: Optional[int]):
            logger.debug("refresh_saved_profiles called with n_clicks=%r", n_clicks)
            return services.build_saved_profile_options()

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_dropdown, "value"),
            dash.Output(SidebarIds.selected_profile_store, "data"),
            dash.Input(SidebarIds.saved_profiles_dropdown, "options"),
            dash.State(SidebarIds.saved_profiles_dropdown, "value"),
            dash.State(SidebarIds.selected_profile_store, "data"),
            prevent_initial_call=False,
        )
        def initialize_or_sync_selected_profile(
            profile_options: Any,
            dropdown_value: Optional[str],
            selected_profile_store_data: Optional[str],
        ):
            logger.debug(
                "initialize_or_sync_selected_profile called with dropdown_value=%r selected_profile_store_data=%r profile_options=%r",
                dropdown_value,
                selected_profile_store_data,
                profile_options,
            )

            if not isinstance(profile_options, list) or not profile_options:
                return None, None

            option_values = {
                option.get("value")
                for option in profile_options
                if isinstance(option, dict) and option.get("value")
            }

            if selected_profile_store_data in option_values:
                if dropdown_value != selected_profile_store_data:
                    logger.debug(
                        "Syncing dropdown value from selected_profile_store_data=%r",
                        selected_profile_store_data,
                    )
                    return selected_profile_store_data, selected_profile_store_data

                return dash.no_update, dash.no_update

            if dropdown_value in option_values:
                logger.debug(
                    "Syncing selected_profile_store from dropdown_value=%r",
                    dropdown_value,
                )
                return dash.no_update, dropdown_value

            resolved_default_profile = self._get_default_profile_name(profile_options)

            logger.debug(
                "Initializing sidebar selected profile to resolved_default_profile=%r",
                resolved_default_profile,
            )
            return resolved_default_profile, resolved_default_profile

        @dash.callback(
            dash.Output(SidebarIds.selected_profile_store, "data", allow_duplicate=True),
            dash.Output(SidebarIds.profile_load_event_store, "data"),
            dash.Input(SidebarIds.saved_profiles_load_button, "n_clicks"),
            dash.State(SidebarIds.saved_profiles_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_selected_profile(
            n_clicks: Optional[int],
            selected_profile: Optional[str],
        ):
            logger.debug(
                "load_selected_profile called with n_clicks=%r selected_profile=%r",
                n_clicks,
                selected_profile,
            )

            if not n_clicks:
                return dash.no_update, dash.no_update

            try:
                resolved_profile_name, status_message = services.resolve_selected_profile(
                    selected_profile,
                )

                profile_load_event = {
                    "profile_name": resolved_profile_name,
                    "n_clicks": int(n_clicks),
                    "loaded_at": datetime.now(timezone.utc).isoformat(),
                    "status": status_message,
                }

                logger.debug(
                    "Resolved selected profile to resolved_profile_name=%r profile_load_event=%r",
                    resolved_profile_name,
                    profile_load_event,
                )

                return resolved_profile_name, profile_load_event

            except Exception:
                logger.exception(
                    "Failed to resolve selected_profile=%r",
                    selected_profile,
                )

                return dash.no_update, dash.no_update

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_load_status, "children"),
            dash.Input(SidebarIds.selected_profile_store, "data"),
            prevent_initial_call=False,
        )
        def render_selected_profile_status(selected_profile: Any) -> str:
            logger.debug(
                "render_selected_profile_status called with selected_profile=%r",
                selected_profile,
            )

            if not selected_profile:
                return "No profile selected."

            return f"Selected profile: {selected_profile}"

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_open_folder_status, "children"),
            dash.Input(SidebarIds.saved_profiles_open_folder_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def open_saved_profiles_folder(n_clicks: Optional[int]):
            logger.debug("open_saved_profiles_folder called with n_clicks=%r", n_clicks)
            del n_clicks

            try:
                return services.open_profiles_directory()

            except Exception as exc:
                logger.exception("Failed to open profile folder.")
                return f"Could not open profile folder: {type(exc).__name__}: {exc}"

    def layout(self, sidebar: Optional[dict[str, list[str]]] = None) -> html.Div:
        """
        Build the complete sidebar layout.
        """
        logger.debug("Building sidebar layout with sidebar=%r", sidebar)

        if sidebar is None:
            sidebar = services.list_saved_calibrations()

        saved_profile_options = services.build_saved_profile_options()
        initial_selected_profile = self._get_default_profile_name(saved_profile_options)

        return html.Div(
            [
                self._build_logo_section(),
                self._build_navigation_section(),
                self._build_saved_profiles_section(
                    profile_options=saved_profile_options,
                    selected_profile=initial_selected_profile,
                ),
                self._build_saved_calibrations_section(sidebar),
                dcc.Store(
                    id=SidebarIds.saved_calibrations_refresh_store,
                    data=0,
                ),
                dcc.Store(
                    id=SidebarIds.selected_profile_store,
                    data=initial_selected_profile,
                    storage_type="session",
                ),
                dcc.Store(
                    id=SidebarIds.profile_load_event_store,
                    data=None,
                    storage_type="session",
                ),
            ],
            style={
                "width": f"{self.sidebar_width_px}px",
                "height": "100vh",
                "display": "flex",
                "flexDirection": "column",
                "gap": "16px",
                "overflowY": "auto",
                "paddingRight": "8px",
                "boxSizing": "border-box",
            },
        )

    def _build_logo_section(self) -> html.Div:
        """
        Build the logo section.
        """
        return html.Div(
            [
                html.Img(
                    id="sidebar-logo",
                    src=self.logo_src,
                    style={
                        "width": "100%",
                        "height": "auto",
                        "display": "block",
                        "objectFit": "contain",
                        "maxHeight": f"{self.logo_max_height_px}px",
                    },
                ),
            ],
            style={"width": "100%"},
        )

    def _build_navigation_section(self) -> html.Div:
        """
        Build the main navigation section.
        """
        return html.Div(
            [
                dbc.Nav(
                    [
                        self._nav_link("Home", "/home"),
                        self._nav_link("Help", "/help"),
                        self._nav_link("Fluorescence", "/fluorescence"),
                        self._nav_link("Scattering", "/scattering"),
                        self._nav_link("Apply calibration", "/calibrate"),
                        self._nav_link("Settings", "/settings"),
                    ],
                    vertical=True,
                    pills=True,
                ),
            ]
        )

    def _nav_link(self, label: str, href: str) -> dbc.NavLink:
        """
        Build a sidebar navigation link.
        """
        return dbc.NavLink(
            label,
            href=href,
            active="exact",
        )

    def _build_saved_profiles_section(
        self,
        *,
        profile_options: list[dict[str, Any]],
        selected_profile: Optional[str],
    ) -> dbc.Card:
        """
        Build the saved profiles card.
        """
        return dbc.Card(
            [
                dbc.CardHeader("Saved profiles"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Open folder",
                                    id=SidebarIds.saved_profiles_open_folder_button,
                                    size="sm",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Refresh",
                                    id=SidebarIds.saved_profiles_refresh_button,
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "8px",
                                "marginBottom": "10px",
                                "flexWrap": "wrap",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    dcc.Dropdown(
                                        id=SidebarIds.saved_profiles_dropdown,
                                        options=profile_options,
                                        value=selected_profile,
                                        placeholder="Select a saved profile",
                                        clearable=True,
                                        persistence=True,
                                        persistence_type="session",
                                        maxHeight=220,
                                    ),
                                    style={"flex": "1"},
                                ),
                                dbc.Button(
                                    "Load",
                                    id=SidebarIds.saved_profiles_load_button,
                                    size="sm",
                                    color="primary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "8px",
                                "alignItems": "center",
                            },
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_profiles_load_status,
                            style={"opacity": 0.75},
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_profiles_open_folder_status,
                            style={"opacity": 0.75},
                        ),
                    ]
                ),
            ]
        )

    def _build_saved_calibrations_section(
        self,
        saved_calibrations: dict[str, list[str]],
    ) -> dbc.Card:
        """
        Build the saved calibrations card.
        """
        logger.debug(
            "Building saved calibrations section with fluorescence=%d scattering=%d",
            len(saved_calibrations.get("fluorescence", [])),
            len(saved_calibrations.get("scattering", [])),
        )

        return dbc.Card(
            [
                dbc.CardHeader("Saved calibrations"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    "Open folder",
                                    id=SidebarIds.saved_calibrations_open_folder_button,
                                    size="sm",
                                    color="secondary",
                                ),
                                dbc.Button(
                                    "Refresh",
                                    id=SidebarIds.saved_calibrations_refresh_button,
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "8px",
                                "marginBottom": "10px",
                                "flexWrap": "wrap",
                            },
                        ),
                        html.Div(
                            self._build_saved_calibrations_body(saved_calibrations),
                            id=SidebarIds.saved_calibrations_body_container,
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Small(
                            id=SidebarIds.saved_calibrations_open_folder_status,
                            style={"opacity": 0.75},
                        ),
                    ]
                ),
            ]
        )

    def _build_saved_calibrations_body(
        self,
        saved_calibrations: dict[str, list[str]],
    ) -> list[html.Div]:
        """
        Build the body content of the saved calibrations card.
        """
        body_children: list[html.Div] = []

        for folder_key, folder_label in services.FOLDER_DISPLAY_ORDER:
            file_names = saved_calibrations.get(folder_key, [])

            logger.debug(
                "Rendering folder_key=%r with %d files",
                folder_key,
                len(file_names),
            )

            if file_names:
                file_list = html.Ul(
                    [self._saved_file_item(folder_key, file_name) for file_name in file_names],
                    style={
                        "paddingLeft": "20px",
                        "marginBottom": "0px",
                    },
                )
            else:
                file_list = html.Div(
                    services.build_saved_calibrations_empty_state(),
                    style={
                        "opacity": 0.7,
                        "fontStyle": "italic",
                    },
                )

            body_children.append(
                html.Div(
                    [
                        html.Div(
                            folder_label,
                            style={
                                "fontWeight": "600",
                                "marginBottom": "6px",
                            },
                        ),
                        file_list,
                    ],
                    style={"marginBottom": "12px"},
                )
            )

        return body_children

    def _saved_file_item(self, folder: str, file_name: str) -> html.Li:
        """
        Build one saved calibration row.

        Two actions are provided:
        - open the raw calibration JSON in a new tab
        - navigate internally to the calibration application page with this calibration selected
        """
        logger.debug(
            "Building sidebar item for folder=%r file_name=%r",
            folder,
            file_name,
        )

        apply_href = services.build_apply_href(folder, file_name)

        return html.Li(
            html.Div(
                [
                    html.Div(
                        html.A(
                            file_name,
                            href=f"/calibration-json/{folder}/{file_name}",
                            target="_blank",
                            rel="noreferrer",
                            style={
                                "overflowWrap": "anywhere",
                                "wordBreak": "break-word",
                                "textDecoration": "none",
                            },
                        ),
                        style={
                            "flex": "1 1 auto",
                            "minWidth": "0",
                        },
                    ),
                    dcc.Link(
                        "Apply",
                        href=apply_href,
                        refresh=False,
                        style={
                            "padding": "0px",
                            "whiteSpace": "nowrap",
                            "textDecoration": "none",
                            "flex": "0 0 auto",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "gap": "12px",
                    "width": "100%",
                },
            )
        )


_sidebar_instance = Sidebar()


def register_sidebar_callbacks() -> None:
    """
    Register callbacks for the singleton sidebar instance.
    """
    logger.debug("register_sidebar_callbacks called.")
    _sidebar_instance.register_callbacks()


def sidebar_html(sidebar: Optional[dict[str, list[str]]]) -> html.Div:
    """
    Build sidebar HTML for the singleton sidebar instance.
    """
    logger.debug("sidebar_html called with sidebar=%r", sidebar)
    return _sidebar_instance.layout(sidebar)