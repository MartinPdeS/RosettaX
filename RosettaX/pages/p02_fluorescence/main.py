# -*- coding: utf-8 -*-

from typing import Self

import dash

from .ids import Ids
from .sections import callbacks as section_callbacks
from .sections import layout as section_layout
from .sections import services as section_services

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

        self.sections = section_services.build_sections(self)

    def register_callbacks(self) -> Self:
        """
        Register all section callbacks.

        Returns
        -------
        Self
            Current page instance.
        """
        section_callbacks.register_callbacks(self.sections)
        return self

    def layout(self) -> dash.html.Div:
        """
        Build the fluorescence page layout.

        Returns
        -------
        dash.html.Div
            Page layout.
        """
        return section_layout.build_page_layout(self, self.sections)


_page = FluorescencePage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/fluorescence",
    name="Fluorescence",
    order=1,
    layout=layout,
)
