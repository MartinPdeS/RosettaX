# -*- coding: utf-8 -*-

from typing import Optional

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.reader import FCSFile


class ChannelPickerSection:
    def __init__(self, page) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("2. Select target channel"),
                dbc.CardBody(
                    [
                        dash.html.Div("Target channel", style={"marginBottom": "6px"}),
                        dash.dcc.Dropdown(
                            id=self.page.ids.ChannelPicker.dropdown,
                            options=[],
                            value=None,
                            placeholder="Select channel",
                            clearable=True,
                        ),
                        dash.html.Div(style={"height": "10px"}),
                        dbc.Alert(
                            "Upload an FCS file to populate channels.",
                            id=self.page.ids.ChannelPicker.status,
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )

    def _register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.ChannelPicker.dropdown, "options"),
            dash.Output(self.page.ids.ChannelPicker.dropdown, "value"),
            dash.Output(self.page.ids.ChannelPicker.status, "children"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
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