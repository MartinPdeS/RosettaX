from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import os 

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.runtime_config import get_runtime_config, list_setting_files
from RosettaX.pages.settings.ids import Ids

class DeleteProfilePage():
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

    def _delete_profile_get_layout(self) -> dbc.Card:
        """
        Build the layout for the delete section and inject an initial file path store.
        """
        runtime_config = get_runtime_config()

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
                    style=self.card_body_scroll,
                ),
            ]
        )

    def _delete_profile_register_callbacks(self) -> None:
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
            dst = Path("RosettaX/data/settings") / name
            if dst.exists() and dst.is_file():
                if name == 'default_profile.json':
                    return f"Cannot delete default profile 'default_profile'. Please choose a different profile to delete."
                try:
                    os.remove(dst)
                    return f"Profile '{name}' deleted."
                except Exception as e:
                    return f"Error deleting profile '{name}': {e}"
            else:
                return f"General error occurred."