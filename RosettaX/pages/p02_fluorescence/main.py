# -*- coding: utf-8 -*-

from typing import Self

import dash

from . import sections
from .ids import Ids
from .state import FluorescencePageState

class FluorescencePage:
    """
    Fluorescence calibration page.

    The page owns one serialized page state store. Individual sections should
    progressively migrate away from section specific stores and use the page
    state as the single source of truth.
    """

    def __init__(self) -> None:
        self.ids = Ids()
        self.backend = None

        self.sections = [
            sections.Header(page=self, card_color="white"),
            sections.Upload(page=self, section_number=1, card_color="pink"),
            sections.Peaks(page=self, section_number=2, card_color="blue"),
            sections.ReferenceTable(page=self, section_number=3, card_color="orange"),
            sections.Calibration(page=self, section_number=4, card_color="green"),
            sections.Save(page=self, section_number=5, card_color="gray"),
        ]

    def register_callbacks(self) -> Self:
        """
        Register all section callbacks.

        Returns
        -------
        Self
            Current page instance.
        """
        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dash.html.Div:
        """
        Build the fluorescence page layout.

        Returns
        -------
        dash.html.Div
            Page layout.
        """
        return dash.html.Div(
            [
                dash.dcc.Store(
                    id=self.ids.State.page_state_store,
                    data=FluorescencePageState.empty().to_dict(),
                    storage_type="session",
                ),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections],
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "18px",
            },
        )


_page = FluorescencePage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/fluorescence",
    name="Fluorescence",
    order=1,
    layout=layout,
)