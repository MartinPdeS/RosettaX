# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from ...state import SettingsPageState
from RosettaX.utils.browser_profiles import (
    BROWSER_PROFILES_STORE_ID,
    BrowserProfileLibrary,
)
from RosettaX.utils import styling, ui_forms


logger = logging.getLogger(__name__)


class DeleteProfile:
    """
    Section for deleting an existing settings profile.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.DeleteProfile

        logger.debug("Initialized DeleteProfile section with page=%r", page)

    def _build_profile_options(self) -> list[dict[str, str]]:
        """
        Build dropdown options from available profiles.

        Returns
        -------
        list[dict[str, str]]
            Profile dropdown options.
        """
        options = BrowserProfileLibrary.from_seed_data().build_options()

        logger.debug("Built delete profile options=%r", options)

        return options

    def get_layout(self) -> dbc.Card:
        """
        Build the layout for the delete profile section.

        Returns
        -------
        dbc.Card
            Delete profile layout.
        """
        logger.debug("Building delete profile layout.")

        return dbc.Card(
            [
                dbc.CardHeader(
                    "3. Delete settings profile",
                    style=ui_forms.build_workflow_section_header_style(
                        color_name=styling.get_workflow_section_color(3),
                    ),
                ),
                dbc.CardBody(
                    [
                        html.P(
                            "Delete an existing settings profile saved in this browser.",
                            style={
                                "opacity": 0.8,
                                "marginBottom": "14px",
                            },
                        ),
                        self._build_delete_profile_controls(),
                        html.Div(
                            id=self.ids.delete_profile_status,
                            style={
                                "marginTop": "10px",
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_section_body_style(
                        style_overrides=self.page.style["card_body_scroll"],
                    ),
                ),
            ],
            style={
                **ui_forms.build_workflow_section_card_style(
                    color_name=styling.get_workflow_section_color(3),
                ),
                "marginBottom": "16px",
            },
        )

    def _build_delete_profile_controls(self) -> html.Div:
        """
        Build delete profile controls.

        Returns
        -------
        html.Div
            Delete profile controls.
        """
        return html.Div(
            [
                dbc.Select(
                    id=self.ids.delete_profile_name,
                    options=self._build_profile_options(),
                    placeholder="Select profile",
                    style={
                        "width": "100%",
                    },
                ),
                dbc.Button(
                    "Delete profile",
                    id=self.ids.delete_profile_button,
                    color="danger",
                    outline=True,
                    n_clicks=0,
                    style={
                        "width": "fit-content",
                    },
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "minmax(260px, 1fr) auto",
                "gap": "12px",
                "alignItems": "center",
                "width": "100%",
            },
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the delete profile section.
        """
        logger.debug("Registering delete profile callbacks.")

        @callback(
            Output(self.ids.delete_profile_name, "options"),
            Output(self.ids.delete_profile_name, "value"),
            Input(BROWSER_PROFILES_STORE_ID, "data"),
            State(self.ids.delete_profile_name, "value"),
            prevent_initial_call=False,
        )
        def sync_delete_profile_options(
            browser_profiles_payload: Any,
            current_value: Any,
        ) -> tuple[list[dict[str, str]], Any]:
            browser_profiles = BrowserProfileLibrary.from_dict(
                browser_profiles_payload,
            )
            profile_options = browser_profiles.build_options()
            option_values = {
                option.get("value")
                for option in profile_options
                if isinstance(option, dict) and option.get("value")
            }

            if current_value in option_values:
                return profile_options, dash.no_update

            return profile_options, browser_profiles.selected_profile

        @callback(
            Output(self.ids.delete_profile_status, "children"),
            Output(BROWSER_PROFILES_STORE_ID, "data", allow_duplicate=True),
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.delete_profile_button, "n_clicks"),
            State(self.ids.delete_profile_name, "value"),
            State(BROWSER_PROFILES_STORE_ID, "data"),
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def delete_selected_profile(
            n_clicks: Any,
            profile_name: Any,
            browser_profiles_payload: Any,
            page_state_payload: Any,
        ) -> tuple[str, Any, Any]:
            logger.debug(
                "delete_selected_profile called with n_clicks=%r profile_name=%r",
                n_clicks,
                profile_name,
            )

            if not n_clicks:
                logger.debug("No delete click detected.")

                return (
                    "",
                    dash.no_update,
                    dash.no_update,
                )

            normalized_profile_name = str(profile_name or "").strip()

            page_state = SettingsPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            if not normalized_profile_name:
                status_message = "Please select a profile to delete."

                page_state = page_state.update(
                    status_message=status_message,
                )

                logger.debug("No profile selected for deletion.")

                return (
                    status_message,
                    dash.no_update,
                    page_state.to_dict(),
                )

            try:
                browser_profiles = BrowserProfileLibrary.from_dict(
                    browser_profiles_payload,
                )
                next_browser_profiles = browser_profiles.delete_profile(
                    profile_name=normalized_profile_name,
                )
                result_message = (
                    f"Profile '{normalized_profile_name}' deleted successfully from this browser."
                )

                next_value = next_browser_profiles.selected_profile

                if page_state.selected_profile == normalized_profile_name:
                    page_state = page_state.update(
                        selected_profile=next_value,
                        status_message=result_message,
                    )

                else:
                    page_state = page_state.update(
                        status_message=result_message,
                    )

                logger.debug(
                    "delete_profile returned result_message=%r for normalized_profile_name=%r",
                    result_message,
                    normalized_profile_name,
                )

                return (
                    result_message,
                    next_browser_profiles.to_dict(),
                    page_state.to_dict(),
                )

            except Exception as exc:
                logger.exception(
                    "Failed to delete profile profile_name=%r",
                    normalized_profile_name,
                )

                status_message = f"{type(exc).__name__}: {exc}"

                page_state = page_state.update(
                    status_message=status_message,
                )

                return (
                    status_message,
                    dash.no_update,
                    page_state.to_dict(),
                )