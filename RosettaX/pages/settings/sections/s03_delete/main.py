# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

from RosettaX.pages.settings.state import SettingsPageState
from RosettaX.utils import directories

from . import services


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

        Returns
        -------
        dbc.Card
            Delete profile layout.
        """
        logger.debug("Building delete profile layout.")

        return dbc.Card(
            [
                dbc.CardHeader("3. Delete settings profile"),
                dbc.CardBody(
                    [
                        html.P(
                            "Delete an existing settings profile and its configuration file.",
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
                    style=self.page.style["card_body_scroll"],
                ),
            ],
            className="mb-4",
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
            Output(self.ids.delete_profile_status, "children"),
            Output(self.ids.delete_profile_name, "options"),
            Output(self.ids.delete_profile_name, "value"),
            Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            Input(self.ids.delete_profile_button, "n_clicks"),
            State(self.ids.delete_profile_name, "value"),
            State(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=True,
        )
        def delete_selected_profile(
            n_clicks: Any,
            profile_name: Any,
            page_state_payload: Any,
        ) -> tuple[str, list[dict[str, str]], Any, Any]:
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
                    dash.no_update,
                    page_state.to_dict(),
                )

            try:
                result_message = services.delete_profile(
                    normalized_profile_name,
                )

                options = self._build_profile_options()

                next_value = None

                if options:
                    next_value = options[0]["value"]

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
                    options,
                    next_value,
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
                    dash.no_update,
                    page_state.to_dict(),
                )