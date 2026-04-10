from typing import Any
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.settings.ids import Ids
from RosettaX.pages.settings.utils import create_profile

class CreateSection():
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
        Build the layout for the load section and inject an initial file path store.
        """
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
                                    id=Ids.NewProfile.new_profile_name,
                                    placeholder="Enter profile name",
                                    type="text",
                                    style={"marginRight": "10px"},
                                ),
                                dbc.Button("Create New Profile", id=Ids.NewProfile.save_new_profile_button, color="primary"),
                                html.Div(id=Ids.NewProfile.new_profile_status, style={"marginTop": "10px"}),
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
            Output(Ids.NewProfile.new_profile_status, "children"),
            Input(Ids.NewProfile.save_new_profile_button, "n_clicks"),
            State(Ids.NewProfile.new_profile_name, "value"),
            prevent_initial_call=True,
        )
        def create_new_profile(n_clicks: Any, name: Any) -> str:
            if n_clicks is None:
                return ""

            if name:
                return create_profile(name)

            return "Please enter a profile name."