import dash
import dash_bootstrap_components as dbc
import logging
from .ids import SidebarIds
from dash import dcc, html
from datetime import UTC, datetime
from RosettaX.application.access import can_edit_settings, is_hosted
from RosettaX.utils import styling
from RosettaX.utils.browser_profiles import (
    BROWSER_PROFILES_STORE_ID,
    build_profile_label,
)
from RosettaX.workflow.sidebar import services
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

NAVIGATION_ICONS = {
    "/": '<path d="M3 11 12 4l9 7v9h-6v-6H9v6H3z"/>',
    "/fluorescence": '<path d="M12 2c1 6 3 8 9 10-6 1-8 3-9 10-1-7-3-9-9-10 6-2 8-4 9-10z"/>',
    "/scattering": '<circle cx="6" cy="18" r="1"/><circle cx="9" cy="15" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="15" cy="9" r="1"/><circle cx="18" cy="6" r="1"/><circle cx="10" cy="19" r="1"/><circle cx="16" cy="13" r="1"/>',
    "/calibrate": '<path d="m12 3 9 5-9 5-9-5 9-5zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
    "/cross-calibration": '<path d="M3 8h17m-4-4 4 4-4 4M21 16H4m4-4-4 4 4 4"/>',
    "/visualization": '<path d="M4 20v-7h4v7zm6 0V4h4v16zm6 0v-11h4v11z"/>',
    "/fcs-slicer": '<path d="M4 9V4h5m6 0h5v5m0 6v5h-5M9 20H4v-5" stroke-dasharray="3 2"/>',
    "/fcs-inspector": '<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
    "/fcs-merge": '<circle cx="9" cy="12" r="7"/><circle cx="15" cy="12" r="7"/>',
    "/sample-files": '<path d="M3 7h7l2 2h9v10H3z"/><path d="M3 7V5h7l2 2"/>',
    "/tutorials": '<path d="M4 4h12a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3z"/><path d="M4 17a3 3 0 0 1 3-3h12M8 8h7"/>',
    "/documentation": '<path d="M5 3h10l4 4v14H5zM14 3v5h5M8 12h8M8 16h8"/>',
    "/help": '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 1 1 4 3c-1 .5-1 1-1 2m0 3h.01"/>',
    "/settings": '<path d="M10 2h4l.6 2.2 2 .8 2-1 2.8 2.8-1 2 .8 2L23 11v3l-2.2.6-.8 2 1 2-2.8 2.8-2-1-2 .8L14 23h-4l-.6-2.2-2-.8-2 1-2.8-2.8 1-2-.8-2L1 14v-3l2.2-.6.8-2-1-2L5.8 3.6l2 1 2-.8z"/><circle cx="12" cy="12" r="3"/>',
}


class Sidebar:
    """
    Application sidebar.

    Responsibilities
    ----------------
    - Render the logo and main navigation.
    - Show saved profile controls.
    - Expose small utility actions such as refresh and open folder.

    Notes
    -----
    Internal app navigation is always performed with ``dcc.Link(..., refresh=False)``
    so route changes stay inside Dash routing instead of triggering a full browser reload.
    """

    def __init__(self) -> None:
        self.page_name = "sidebar"
        self.logo_src = "/assets/logo/logo_light.svg"
        self.logo_max_height_px = 156
        self.sidebar_width_px = 346
        self.style = styling.PAGE

        logger.debug(
            "Initialized Sidebar with sidebar_width_px=%r logo_src=%r",
            self.sidebar_width_px,
            self.logo_src,
        )

    def register_callbacks(self) -> None:
        """
        Register all sidebar callbacks.
        """
        logger.debug("Registering sidebar callbacks.")

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_dropdown, "options"),
            dash.Output(SidebarIds.saved_profiles_dropdown, "value"),
            dash.Output(SidebarIds.selected_profile_store, "data"),
            dash.Input(BROWSER_PROFILES_STORE_ID, "data"),
            dash.State(SidebarIds.saved_profiles_dropdown, "value"),
            dash.State(SidebarIds.selected_profile_store, "data"),
            prevent_initial_call=False,
        )
        def initialize_or_sync_selected_profile(
            browser_profiles_payload: Any,
            dropdown_value: str | None,
            selected_profile_store_data: str | None,
        ):
            """Restore the active profile and preserve a valid pending choice."""
            library = services.get_available_profiles(browser_payload=browser_profiles_payload)
            active_profile = selected_profile_store_data
            if not isinstance(active_profile, str) or active_profile not in library.profiles:
                active_profile = library.selected_profile
            profile_options = services.build_profile_picker_options(library=library)
            option_values = {option["value"] for option in profile_options}
            selected_option = dropdown_value if isinstance(dropdown_value, str) and dropdown_value in option_values else active_profile
            return (
                profile_options,
                selected_option if selected_option != dropdown_value else dash.no_update,
                active_profile if active_profile != selected_profile_store_data else dash.no_update,
            )

        @dash.callback(
            dash.Output(SidebarIds.profile_description, "children"),
            dash.Input(SidebarIds.saved_profiles_dropdown, "value"),
        )
        def describe_profile(profile_name: str | None) -> str:
            """Describe the selected preset before loading it."""
            return services.PROFILE_DESCRIPTIONS.get(profile_name, "")

        @dash.callback(
            dash.Output(
                SidebarIds.selected_profile_store, "data", allow_duplicate=True
            ),
            dash.Output(BROWSER_PROFILES_STORE_ID, "data", allow_duplicate=True),
            dash.Output(SidebarIds.profile_load_event_store, "data"),
            dash.Input(SidebarIds.saved_profiles_load_button, "n_clicks"),
            dash.State(SidebarIds.saved_profiles_dropdown, "value"),
            dash.State(BROWSER_PROFILES_STORE_ID, "data"),
            prevent_initial_call=True,
        )
        def load_selected_profile(
            n_clicks: int | None,
            selected_profile: str | None,
            browser_profiles_payload: Any,
        ):
            logger.debug(
                "load_selected_profile called with n_clicks=%r selected_profile=%r",
                n_clicks,
                selected_profile,
            )

            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update

            try:
                browser_profiles = services.get_available_profiles(browser_payload=browser_profiles_payload)
                if not isinstance(selected_profile, str) or selected_profile not in browser_profiles.profiles:
                    raise dash.exceptions.PreventUpdate
                resolved_profile_name = selected_profile
                status_message = f"Selected profile: {browser_profiles.get_profile_label(resolved_profile_name)}"

                profile_load_event = {
                    "profile_name": resolved_profile_name,
                    "n_clicks": int(n_clicks),
                    "loaded_at": datetime.now(UTC).isoformat(),
                    "status": status_message,
                }

                logger.debug(
                    "Resolved selected profile to resolved_profile_name=%r profile_load_event=%r",
                    resolved_profile_name,
                    profile_load_event,
                )

                return (
                    resolved_profile_name,
                    browser_profiles.with_selected_profile(resolved_profile_name).to_dict() if can_edit_settings() else dash.no_update,
                    profile_load_event,
                )

            except dash.exceptions.PreventUpdate:
                raise
            except Exception:
                logger.exception(
                    "Failed to resolve selected_profile=%r",
                    selected_profile,
                )

                return dash.no_update, dash.no_update, dash.no_update

        @dash.callback(
            dash.Output(SidebarIds.saved_profiles_load_status, "children"),
            dash.Input(SidebarIds.selected_profile_store, "data"),
            dash.Input(BROWSER_PROFILES_STORE_ID, "data"),
            prevent_initial_call=False,
        )
        def render_selected_profile_status(
            selected_profile: Any,
            browser_profiles_payload: Any,
        ) -> str:
            logger.debug(
                "render_selected_profile_status called with selected_profile=%r",
                selected_profile,
            )

            if not selected_profile:
                return "No profile selected."

            browser_profiles = services.get_available_profiles(browser_payload=browser_profiles_payload)
            profile_label = browser_profiles.get_profile_label(
                str(selected_profile),
            ) or build_profile_label(str(selected_profile))

            return f"Selected profile: {profile_label}"

    def layout(
        self,
        sidebar: dict[str, list[str]] | None = None,
    ) -> html.Div:
        """
        Build the complete sidebar layout.

        The selected profile dropdown and store are intentionally initialized
        with ``None`` here. The synchronization callback initializes them only
        when no valid session value already exists. This prevents page navigation
        from resetting the active profile back to ``default_profile``.
        """
        logger.debug(
            "Building sidebar layout with sidebar=%r",
            sidebar,
        )

        saved_profile_library = services.get_available_profiles(browser_payload=None)
        saved_profile_options = services.build_profile_picker_options(library=saved_profile_library)
        initial_selected_profile = saved_profile_library.selected_profile

        return html.Div(
            [
                self._build_logo_section(),
                self._build_navigation_section(),
                self._build_saved_profiles_section(
                    profile_options=saved_profile_options,
                    selected_profile=initial_selected_profile,
                ),
                dcc.Store(
                    id=SidebarIds.selected_profile_store,
                    data=initial_selected_profile,
                    storage_type="local",
                ),
                dcc.Store(
                    id=SidebarIds.profile_load_event_store,
                    data=None,
                    storage_type="session",
                ),
                html.Div(
                    dbc.Nav(
                        self._nav_link("Settings", "/settings"),
                        vertical=True,
                        pills=True,
                        style={
                            "--bs-nav-pills-link-active-color": "#111827",
                            "--bs-nav-pills-link-active-bg": "#e2e8f0",
                        },
                    ),
                    className="rosettax-sidebar-footer",
                ) if can_edit_settings() else None,
            ],
            style={
                "width": "100%",
                "height": "var(--rosettax-sidebar-height, calc(100dvh - 32px))",
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
                dcc.Link(
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
                    href="/",
                    refresh=False,
                    style={
                        "display": "block",
                    },
                ),
            ],
            style={
                "width": "100%",
            },
        )

    def _build_navigation_section(self) -> html.Nav:
        """Build permanently visible navigation grouped into section panels."""
        return html.Nav(
            [
                dbc.Nav(self._nav_link("Home", "/"), vertical=True, pills=True),
                self._build_navigation_group(
                    label="Calibration",
                    links=[
                        self._nav_link("Fluorescence", "/fluorescence", tier="child"),
                        self._nav_link("Scattering", "/scattering", tier="child"),
                        self._nav_link("Cross-calibration", "/cross-calibration", tier="child"),
                        self._nav_link("Apply calibration", "/calibrate", tier="child"),
                    ],
                ),
                self._build_navigation_group(
                    label="FCS data tools",
                    links=[
                        self._nav_link("FCS Inspector", "/fcs-inspector", tier="child"),
                        self._nav_link("Visualize data", "/visualization", tier="child"),
                        self._nav_link("Slice FCS files", "/fcs-slicer", tier="child"),
                        self._nav_link("Merge FCS files", "/fcs-merge", tier="child"),
                    ],
                ),
                self._build_navigation_group(
                    label="Guides & examples",
                    links=[
                        self._nav_link("Sample files", "/sample-files", tier="child"),
                        self._nav_link("Tutorials", "/tutorials", tier="child"),
                        self._nav_link("Documentation", "/documentation", tier="child"),
                        self._nav_link("Help", "/help", tier="child"),
                    ],
                ),
            ],
            className="rosettax-sidebar-navigation",
            **{"aria-label": "Main navigation"},
        )

    def _build_navigation_group(
        self,
        *,
        label: str,
        links: list[dbc.NavLink],
    ) -> html.Section:
        """Build a labeled panel containing all links for one workflow group.

        Parameters
        ----------
        label : str
            Visible section heading and accessible section name.
        links : list[dbc.NavLink]
            Navigation links shown in their supplied order.

        Returns
        -------
        html.Section
            Always visible navigation panel.
        """
        return html.Section(
            [
                html.H2(label, className="rosettax-sidebar-group-title"),
                dbc.Nav(links, vertical=True, pills=True),
            ],
            className="rosettax-sidebar-group",
            **{"aria-label": label},
        )

    def _nav_link(
        self,
        label: str,
        href: str,
        *,
        tier: str = "top",
    ) -> dbc.NavLink:
        """
        Build a sidebar navigation link.
        """
        if tier == "child":
            link_style = {
                "padding": "0.42rem 0.6rem",
                "margin": "0",
                "fontSize": "0.96rem",
                "lineHeight": "1.25",
                "borderRadius": "0.65rem",
                "color": "var(--rosettax-text-color)",
            }
        else:
            link_style = {
                "padding": "0.78rem 1rem",
                "margin": "0",
                "fontSize": "1.08rem",
                "lineHeight": "1.2",
                "borderRadius": "0.9rem",
                "color": "var(--rosettax-text-color)",
            }

        icon = NAVIGATION_ICONS.get(href)
        children: Any = label
        if icon:
            svg = (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                'fill="none" stroke="black" stroke-width="1.8" '
                'stroke-linecap="round" stroke-linejoin="round">'
                f"{icon}</svg>"
            )
            mask = f'url("data:image/svg+xml,{quote(svg)}")'
            children = [
                html.Span(
                    className="rosettax-navigation-icon",
                    style={"maskImage": mask, "WebkitMaskImage": mask},
                    **{"aria-hidden": "true"},
                ),
                html.Span(label),
            ]

        return dbc.NavLink(
            children,
            href=href,
            active="exact",
            className="rosettax-sidebar-link",
            style={**link_style, "display": "flex", "alignItems": "center", "gap": "0.7rem"},
        )

    def _build_saved_profiles_section(
        self,
        *,
        profile_options: list[dict[str, Any]],
        selected_profile: str | None,
    ) -> dbc.Card:
        """
        Build the saved profiles card.
        """
        return dbc.Card(
            [
                dbc.CardHeader("Workflow profiles" if is_hosted() else "Saved profiles"),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.Div(
                                    dcc.Dropdown(
                                        id=SidebarIds.saved_profiles_dropdown,
                                        options=profile_options,
                                        value=selected_profile,
                                        placeholder="Select a profile",
                                        clearable=False,
                                        persistence=True,
                                        persistence_type="session",
                                        maxHeight=220,
                                    ),
                                    style={
                                        "flex": "1",
                                    },
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
                        html.Small(id=SidebarIds.profile_description, className="rosettax-profile-description"),
                        html.Small(
                            id=SidebarIds.saved_profiles_load_status,
                            style={
                                "opacity": 0.75,
                            },
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
                        html.Div(
                            style={
                                "height": "8px",
                            }
                        ),
                        html.Small(
                            id=SidebarIds.saved_calibrations_open_folder_status,
                            style={
                                "opacity": 0.75,
                            },
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
            file_names = saved_calibrations.get(
                folder_key,
                [],
            )

            logger.debug(
                "Rendering folder_key=%r with %d files",
                folder_key,
                len(file_names),
            )

            if file_names:
                file_list = html.Ul(
                    [
                        self._saved_file_item(
                            folder_key,
                            file_name,
                        )
                        for file_name in file_names
                    ],
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
                    style={
                        "marginBottom": "12px",
                    },
                )
            )

        return body_children

    def _saved_file_item(
        self,
        folder: str,
        file_name: str,
    ) -> html.Li:
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

        apply_href = services.build_apply_href(
            folder,
            file_name,
        )

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


def sidebar_html(
    sidebar: dict[str, list[str]] | None,
) -> html.Div:
    """
    Build sidebar HTML for the singleton sidebar instance.
    """
    logger.debug(
        "sidebar_html called with sidebar=%r",
        sidebar,
    )

    return _sidebar_instance.layout(sidebar)
