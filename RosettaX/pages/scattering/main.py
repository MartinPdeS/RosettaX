# -*- coding: utf-8 -*-
import dash

from . import sections
from .ids import Ids
from .state import ScatteringPageState


class ScatterCalibrationPage:
    """
    Scattering calibration page.

    The page owns one serialized page state store. Individual sections should
    progressively migrate away from section-specific stores and use the page
    state as the single source of truth.
    """

    def __init__(self) -> None:
        self.ids = Ids()
        self.backend = None

        self.sections = [
            sections.Upload(page=self),
            sections.Peaks(page=self),
            sections.Parameters(page=self),
            sections.Calibration(page=self),
            sections.Save(page=self),
        ]

    def register_callbacks(self) -> "ScatterCalibrationPage":
        """
        Register all section callbacks.

        Returns
        -------
        ScatterCalibrationPage
            Current page instance.
        """
        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dash.html.Div:
        """
        Build the scattering calibration page layout.

        Returns
        -------
        dash.html.Div
            Page layout.
        """
        return dash.html.Div(
            [
                dash.dcc.Store(
                    id=self.ids.State.page_state_store,
                    data=ScatteringPageState.empty().to_dict(),
                    storage_type="session",
                ),
                dash.html.Br(),
                *[section.get_layout() for section in self.sections],
            ]
        )


_page = ScatterCalibrationPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/scattering",
    name="Scattering",
    order=2,
    layout=layout,
)