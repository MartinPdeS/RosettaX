from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import os 

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages import styling
from RosettaX.pages.calibrate import ids
from RosettaX.pages.fluorescence.backend import BackEnd
from RosettaX.pages.runtime_config import get_runtime_config
from RosettaX.pages.settings.ids import Ids

class NewProfilePage():
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

    def _new_profile_get_layout(self) -> dbc.Card:
        """
        Build the layout for the load section and inject an initial file path store.
        """
        runtime_config = get_runtime_config()
        return dbc.Card(
            [
                dbc.CardHeader("Create New Settings Profile"),
                dbc.CardBody(
                    [
                        html.P(
                            "Creates a new settings profile. This will allow you to save and load different configurations for your RosettaX instance, making it easier to switch between different experimental setups or user preferences."
                        ),
                        html.Div(
                            [
                                dcc.Input(
                                    id=Ids.NewProfile.new_profile_name_input,
                                    placeholder="Enter profile name",
                                    type="text",
                                    style={"marginRight": "10px"},
                                ),
                                dbc.Button("Create New Profile", id=Ids.NewProfile.save_new_profile_button, color="primary"),
                                html.Div(id=Ids.NewProfile.new_profile_status, style={"marginTop": "10px"}),
                            ]
                        ),

                    ],
                    style=self.card_body_scroll,
                ),
            ]
        )

    def _new_profile_register_callbacks(self) -> None:
        """
        Register callbacks for:
        - showing filename
        - loading from upload or CLI path
        """
        @callback(
            Output(Ids.NewProfile.new_profile_status, "children"),
            Input(Ids.NewProfile.save_new_profile_button, "n_clicks"),
            State(Ids.NewProfile.new_profile_name_input, "value"),
            prevent_initial_call=True,
        )
        def create_new_profile(n_clicks: Any, name: Any) -> str:
            if n_clicks is None:
                return ""
            if name:
                src = Path("RosettaX/data/settings/settings.json")
                dst = Path(f"RosettaX/data/settings/{name}.json")
                if not dst.exists():
                    with open(src, "r") as f_src, open(dst, "w") as f_dst:
                        f_dst.write(f_src.read())
                    return f"Profile '{name}' created."
                else:
                    return f"Profile '{name}' already exists."
            return "Please enter a profile name."