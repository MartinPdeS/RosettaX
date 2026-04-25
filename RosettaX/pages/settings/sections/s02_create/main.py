# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from RosettaX.pages.settings.state import SettingsPageState

from . import services


logger = logging.getLogger(__name__)


class CreateProfile:
    """
    Section for creating a new settings profile.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.NewProfile

        logger.debug("Initialized CreateProfile section with page=%r", page)

    def _get_layout(self) -> dbc.Card:
        """
        Build the layout for the create profile section.
        """
        logger.debug("Building create profile layout.")

        return dbc.Card(
            [
                dbc.CardHeader("2. Create settings profile"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "Create a new settings profile to store a separate "
                                "RosettaX configuration."
                            ),
                            style={
                                "opacity": 0.8,
                                "marginBottom": "14px",
                            },
                        ),
                        self._build_create_profile_controls(),
                        html.Div(
                            id=self.ids.new_profile_status,
                            style={
                                "marginTop": "10px",
                            },
                        ),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ],
            className="mb-4",
        )

    def _build_create_profile_controls(self) -> html.Div:
        """
        Build the create profile input and action button.

        Returns
        -------
        html.Div
            Create profile controls.
        """
        return html.Div(
            [
                dbc.Input(
                    id=self.ids.new_profile_name,
                    placeholder="Profile name",
                    type="text",
                    style={
                        "width": "100%",
                    },
                ),
                dbc.Button(
                    "Create profile",
                    id=self.ids.save_new_profile_button,
                    color="primary",
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
        Register callbacks for the create profile section.
        """
        logger.debug("Registering create profile callbacks.")

        @callback(
            Output(self.ids.new_profile_status, "children"),
            Output(self.ids.new_profile_name, "value"),
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.save_new_profile_button, "n_clicks"),
            State(self.ids.new_profile_name, "value"),
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def create_new_profile(
            n_clicks: Any,
            name: Any,
            page_state_payload: Any,
        ) -> tuple[str, Any, Any]:
            logger.debug(
                "create_new_profile called with n_clicks=%r name=%r",
                n_clicks,
                name,
            )

            if not n_clicks:
                logger.debug("No create profile click detected.")
                return "", dash.no_update, dash.no_update

            profile_name = str(name or "").strip()

            page_state = SettingsPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            if not profile_name:
                status_message = "Please enter a profile name."

                page_state = page_state.update(
                    status_message=status_message,
                )

                logger.debug("Profile name is empty.")

                return status_message, dash.no_update, page_state.to_dict()

            try:
                result_message = services.create_profile(
                    profile_name,
                )

                page_state = page_state.update(
                    status_message=result_message,
                )

                logger.debug(
                    "create_profile returned result_message=%r for profile_name=%r",
                    result_message,
                    profile_name,
                )

                return result_message, "", page_state.to_dict()

            except Exception as exc:
                logger.exception(
                    "Failed to create profile with profile_name=%r",
                    profile_name,
                )

                status_message = f"{type(exc).__name__}: {exc}"

                page_state = page_state.update(
                    status_message=status_message,
                )

                return status_message, dash.no_update, page_state.to_dict()