# -*- coding: utf-8 -*-
import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.calibrate import sections
from RosettaX.pages.calibrate.ids import Ids


class ApplyCalibrationPage:
    def __init__(self) -> None:
        self.path = "/apply-calibration"
        self.name = "Apply Calibration"
        self.container_style = {"paddingBottom": "48px"}

        self.ids = Ids()

        self.sections = [
            sections.HeaderSection(page=self),
            sections.CalibrationPickerSection(page=self),
            sections.FilePickerSection(page=self),
            sections.ChannelPickerSection(page=self),
            sections.ApplySection(page=self),
            # sections.PlotSection(page=self),
        ]

    def register(self) -> "ApplyCalibrationPage":
        dash.register_page(__name__, path=self.path, name=self.name, order=3)
        return self

    def register_callbacks(self) -> "ApplyCalibrationPage":
        for section in self.sections:
            section.register_callbacks()

        return self

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [section.get_layout() for section in self.sections],
            fluid=True,
            style=self.container_style,
        )

layout = ApplyCalibrationPage().register().register_callbacks().layout()