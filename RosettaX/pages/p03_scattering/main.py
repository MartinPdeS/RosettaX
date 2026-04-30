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

    section_color = "blue"

    def __init__(self) -> None:
        self.ids = Ids()
        self.backend = None

        self.sections = [
            sections.Header(
                page=self,
                card_color="white",
            ),
            sections.Upload(
                page=self,
                section_number=1,
                card_color="pink",
            ),
            sections.Peaks(
                page=self,
                section_number=2,
                card_color="blue",
            ),
            sections.Model(
                page=self,
                section_number=3,
                card_color="orange",
            ),
            sections.ReferenceTable(
                page=self,
                section_number=4,
                card_color="green",
            ),
            sections.Calibration(
                page=self,
                section_number=5,
                card_color="yellow",
            ),
            sections.Save(
                page=self,
                section_number=6,
                card_color="gray",
            ),
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
                dash.html.Div(
                    [
                        section.get_layout()
                        for section in self.sections
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "18px",
                    },
                ),
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