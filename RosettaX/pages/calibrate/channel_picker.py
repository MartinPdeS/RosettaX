# -*- coding: utf-8 -*-

from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages.calibrate.ids import Ids
from RosettaX.utils.reader import FCSFile


class ChannelPickerSection:
    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("2. Select target channel"),
                dbc.CardBody(
                    [
                        html.Div("Target channel", style={"marginBottom": "6px"}),
                        dcc.Dropdown(
                            id=Ids.ChannelPicker.dropdown,
                            options=[],
                            value=None,
                            placeholder="Select channel",
                            clearable=True,
                        ),
                        html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Upload an FCS file to populate channels.",
                            id=Ids.ChannelPicker.status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(Ids.ChannelPicker.dropdown, "options"),
            dash.Output(Ids.ChannelPicker.dropdown, "value"),
            dash.Output(Ids.ChannelPicker.status, "children"),
            dash.Input(Ids.Stores.uploaded_fcs_path_store, "data"),
            prevent_initial_call=True,
        )
        def populate_channels(fcs_path: Optional[str]):
            if not fcs_path:
                return [], None, "Upload an FCS file to populate channels."

            try:
                with FCSFile(str(fcs_path), writable=False) as fcs:
                    names = fcs.get_column_names()
            except Exception as exc:
                return [], None, f"Could not read channels: {type(exc).__name__}: {exc}"

            options = [{"label": n, "value": n} for n in names]
            if not options:
                return [], None, "No channels found in file."

            return options, None, f"Loaded {len(options)} channel(s)."