from typing import Any

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.settings.utils import list_setting_files
from RosettaX.pages.settings.ids import Ids

class DeleteSection():
    """
    Section 1: Load an FCS file and initialize the detector dropdowns.

    Supported modes
    ---------------
    1. Upload mode
       User uploads an FCS file through the UI.

    2. CLI path mode
       An FCS file path is provided via runtime configuration and loaded on startup.

    This section is the sole owner of detector dropdown Outputs.
    """
    def __init__(self, page) -> None:
        self.page = page

    def _get_layout(self) -> dbc.Card:
        """
        Build the layout for the delete section and inject an initial file path store.
        """
        return dbc.Card(
            [
                dbc.CardHeader("Delete Settings Profile"),
                dbc.CardBody(
                    [
                        html.P(
                            "Delete an existing settings profile. This will remove the profile and all its associated configurations."
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    options=[{"label": profile, "value": profile+'.json'} for profile in list_setting_files()],
                                    placeholder="Select Profile",
                                    id=Ids.DeleteProfile.delete_profile_name,
                                ),
                                dbc.Button("Delete Profile", id=Ids.DeleteProfile.delete_profile_button, color="danger"),
                                html.Div(id=Ids.DeleteProfile.delete_profile_status, style={"marginTop": "10px"}),
                            ]
                        ),

                    ],
                    style=self.page.style["card_body_scroll"],
                ),
            ]
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for:
        - showing filename
        - loading from upload or CLI path
        """
        @callback(
            Output(Ids.DeleteProfile.delete_profile_status, "children"),
            Input(Ids.DeleteProfile.delete_profile_button, "n_clicks"),
            State(Ids.DeleteProfile.delete_profile_name, "value"),
            prevent_initial_call=True,
        )
        def delete_profile(n_clicks: Any, name: Any) -> str:
            if n_clicks is None:
                return ""
            if name is None:
                return "Please select a profile to delete."

            return delete_profile(name)
