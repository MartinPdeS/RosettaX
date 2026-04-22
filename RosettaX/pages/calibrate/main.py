# -*- coding: utf-8 -*-
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from typing import Self

from RosettaX.pages.calibrate import sections
from RosettaX.pages.calibrate.ids import Ids


class ApplyCalibrationPage:
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
        for section in self.sections:
            section.register_callbacks()
        return self

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                dcc.Location(id=self.ids.Page.location, refresh=False),
                dcc.Store(
                    id=self.ids.Stores.selected_calibration_path_store,
                    storage_type="session",
                ),
                dcc.Store(
                    id=self.ids.Stores.uploaded_fcs_path_store,
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