from typing import Any
import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils import directories
from RosettaX.pages.settings.ids import Ids
from RosettaX.pages.settings.utils import delete_profile as delete_profile_file


logger = logging.getLogger(__name__)


class DeleteProfile:
    """
    Section for deleting an existing settings profile.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized DeleteProfile section with page=%r", page)

    def _build_profile_options(self) -> list[dict[str, str]]:
        """
        Build dropdown options from available profiles.
        """
        options: list[dict[str, str]] = []

        for profile_name in directories.list_profiles():
            profile_file_name = str(profile_name).strip()

            if not profile_file_name:
                continue

            profile_label = (
                profile_file_name[:-5]
                if profile_file_name.endswith(".json")
                else profile_file_name
            )

            options.append(
                {
                    "label": profile_label,
                    "value": profile_file_name,
                }
            )

        logger.debug("Built delete profile options=%r", options)
        return options

    def _get_layout(self) -> dbc.Card:
        """
        Build the layout for the delete profile section.
        """
        logger.debug("Building delete profile layout.")

        return dbc.Card(
            [
                dbc.CardHeader("Delete Settings Profile"),
                dbc.CardBody(
                    [
                        html.P(
                            "Delete an existing settings profile. This removes the "
                            "profile and its associated configuration file."
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id=Ids.DeleteProfile.delete_profile_name,
                                    options=self._build_profile_options(),
                                    placeholder="Select Profile",
                                ),
                                dbc.Button(
                                    "Delete Profile",
                                    id=Ids.DeleteProfile.delete_profile_button,
                                    color="danger",
                                ),
                                html.Div(
                                    id=Ids.DeleteProfile.delete_profile_status,
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
        Register callbacks for the delete profile section.
        """
        logger.debug("Registering delete profile callbacks.")

        @callback(
            Output(Ids.DeleteProfile.delete_profile_status, "children"),
            Input(Ids.DeleteProfile.delete_profile_button, "n_clicks"),
            State(Ids.DeleteProfile.delete_profile_name, "value"),
            prevent_initial_call=True,
        )
        def delete_selected_profile(
            n_clicks: Any,
            profile_name: Any,
        ) -> str:
            logger.debug(
                "delete_selected_profile called with n_clicks=%r profile_name=%r",
                n_clicks,
                profile_name,
            )

            if not n_clicks:
                logger.debug("No delete click detected. Returning empty status.")
                return ""

            normalized_profile_name = str(profile_name or "").strip()

            if not normalized_profile_name:
                logger.debug("No profile selected for deletion.")
                return "Please select a profile to delete."

            result_message = delete_profile_file(normalized_profile_name)

            logger.debug(
                "delete_profile_file returned result_message=%r for normalized_profile_name=%r",
                result_message,
                normalized_profile_name,
            )
            return result_message