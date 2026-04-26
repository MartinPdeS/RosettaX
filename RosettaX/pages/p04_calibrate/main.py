# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Self

import dash
import dash_bootstrap_components as dbc
from dash import dcc

from . import sections
from .ids import Ids
from .state import ApplyCalibrationPageState


class ApplyCalibrationPage:
    """
    Apply calibration page.

    The page owns one serialized page state store. Individual sections should
    progressively migrate away from section-specific stores and use the page
    state as the single source of truth.
    """

    def __init__(self) -> None:
        self.container_style = {"paddingBottom": "48px"}

        self.ids = Ids()

        self.sections = [
            sections.Header(page=self),
            sections.CalibrationPicker(page=self),
            sections.FilePicker(page=self),
            sections.Apply(page=self),
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

    def layout(self, **_kwargs) -> dbc.Container:
        """
        Build the apply calibration page layout.

        Returns
        -------
        dbc.Container
            Page layout.
        """
        return dbc.Container(
            [
                dcc.Location(
                    id=self.ids.Page.location,
                    refresh=False,
                ),
                dcc.Store(
                    id=self.ids.State.page_state_store,
                    data=ApplyCalibrationPageState.empty().to_dict(),
                    storage_type="session",
                ),
                *[section.get_layout() for section in self.sections],
            ],
            fluid=True,
            style=self.container_style,
        )


_page = ApplyCalibrationPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/calibrate",
    name="Apply Calibration",
    order=3,
    layout=layout,
)