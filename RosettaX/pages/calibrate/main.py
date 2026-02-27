# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.calibrate.header import HeaderSection
from RosettaX.pages.calibrate.calibration_picker import CalibrationPickerSection
from RosettaX.pages.calibrate.file_picker import FilePickerSection
from RosettaX.pages.calibrate.channel_picker import ChannelPickerSection
from RosettaX.pages.calibrate.apply import ApplySection
from RosettaX.pages.calibrate.plot import PlotSection


class ApplyCalibrationPage:
    def __init__(self) -> None:
        self.path = "/apply-calibration"
        self.name = "Apply Calibration"
        self.container_style = {"paddingBottom": "48px"}

        self.header_section = HeaderSection()
        self.calibration_picker_section = CalibrationPickerSection()
        self.file_picker_section = FilePickerSection()
        self.channel_picker_section = ChannelPickerSection()
        self.apply_section = ApplySection()
        self.plot_section = PlotSection()

    def register(self) -> "ApplyCalibrationPage":
        dash.register_page(__name__, path=self.path, name=self.name, order=3)
        return self

    def register_callbacks(self) -> "ApplyCalibrationPage":
        self.calibration_picker_section.register_callbacks()
        self.file_picker_section.register_callbacks()
        self.channel_picker_section.register_callbacks()
        self.apply_section.register_callbacks()
        self.plot_section.register_callbacks()
        return self

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                self.header_section.get_layout(),
                html.Hr(),
                self.file_picker_section.get_layout(),
                html.Div(style={"height": "12px"}),
                self.channel_picker_section.get_layout(),
                html.Div(style={"height": "12px"}),
                self.calibration_picker_section.get_layout(),
                html.Div(style={"height": "12px"}),
                self.apply_section.get_layout(),
                html.Div(style={"height": "12px"}),
                self.plot_section.get_layout(),
            ],
            fluid=True,
            style=self.container_style,
        )


page = ApplyCalibrationPage().register().register_callbacks()
layout = page.layout()