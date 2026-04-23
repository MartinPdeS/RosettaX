from typing import Any
import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.settings.ids import Ids
from . import services

logger = logging.getLogger(__name__)


class CreateProfile:
    """
    Section for creating a new settings profile.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized CreateProfile section with page=%r", page)

    def _get_layout(self) -> dbc.Card:
        """
        Build the layout for the create profile section.
        """
        logger.debug("Building create profile layout.")

        return dbc.Card(
            [
                dbc.CardHeader("Create New Settings Profile"),
                dbc.CardBody(
                    [
                        html.P(
                            (
                                "Creates a new settings profile. This allows you to save "
                                "and load different RosettaX configurations so you can "
                                "switch more easily between experimental setups or user "
                                "preferences."
                            )
                        ),
                        html.Div(
                            [
                                dcc.Input(
                                    id=Ids.NewProfile.new_profile_name,
                                    placeholder="Enter profile name",
                                    type="text",
                                    style={"marginRight": "10px"},
                                ),
                                dbc.Button(
                                    "Create New Profile",
                                    id=Ids.NewProfile.save_new_profile_button,
                                    color="primary",
                                ),
                                html.Div(
                                    id=Ids.NewProfile.new_profile_status,
                                    style={"marginTop": "10px"},
                                ),
                            ]
                        ),
                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the create profile section.
        """
        logger.debug("Registering create profile callbacks.")

        @callback(
            Output(Ids.NewProfile.new_profile_status, "children"),
            Input(Ids.NewProfile.save_new_profile_button, "n_clicks"),
            State(Ids.NewProfile.new_profile_name, "value"),
            prevent_initial_call=True,
        )
        def create_new_profile(
            n_clicks: Any,
            name: Any,
        ) -> str:
            logger.debug(
                "create_new_profile called with n_clicks=%r name=%r",
                n_clicks,
                name,
            )

            if not n_clicks:
                logger.debug("No create profile click detected. Returning empty status.")
                return ""

            profile_name = str(name or "").strip()

            if not profile_name:
                logger.debug("Profile name is empty.")
                return "Please enter a profile name."

            result_message = services.create_profile(profile_name)

            logger.debug(
                "create_profile returned result_message=%r for profile_name=%r",
                result_message,
                profile_name,
            )
            return result_message