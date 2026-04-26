# -*- coding: utf-8 -*-

import dash

from . import sections
from .ids import Ids
from .state import SettingsPageState
from RosettaX.utils import styling


class SettingsPage:
    """
    Settings page.

    This page owns one SettingsPageState store shared by all settings sections.
    """

    def __init__(self) -> None:
        self.ids = Ids()
        self.style = styling.PAGE

        self.sections = [
            sections.DefaultProfile(page=self),
            sections.CreateProfile(page=self),
            sections.DeleteProfile(page=self),
        ]

        self.backend = None

    def register_callbacks(self) -> "SettingsPage":
        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.dcc.Store(
                    id=self.ids.State.page_state_store,
                    storage_type="session",
                    data=SettingsPageState.empty().to_dict(),
                ),
                *[
                    section._get_layout()
                    for section in self.sections
                ],
            ]
        )


_page = SettingsPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/settings",
    name="Settings",
    order=4,
    layout=layout,
)