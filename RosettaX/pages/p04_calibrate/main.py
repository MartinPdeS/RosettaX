# -*- coding: utf-8 -*-

from typing import Self

import dash
import dash_bootstrap_components as dbc

from .ids import Ids
from .sections import callbacks as section_callbacks
from .sections import layout as section_layout
from .sections import services as section_services


class ApplyCalibrationPage:
    """
    Apply calibration page.

    The page owns one serialized page state store and a small number of
    section-level stores used by the current calibration application workflow.

    Stores
    ------
    - page_state_store:
      Serialized page state.

    - selected_calibration_path_store:
      Selected calibration dropdown value, for example
      "fluorescence/example.json" or "scattering/example.json".

    - selected_calibration_summary_store:
      Lightweight metadata extracted from the selected calibration file.
      This is used by the UI to show scattering target model controls when
      a scattering calibration is selected.

    - uploaded_fcs_path_store:
      Uploaded input FCS path or paths.
    """

    header_color = "green"
    calibration_picker_color = "pink"
    file_picker_color = "blue"
    apply_color = "orange"

    def __init__(self) -> None:
        self.container_style = {
            "paddingBottom": "48px",
        }

        self.ids = Ids()

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

    def layout(self, **_kwargs) -> dbc.Container:
        """
        Build the apply calibration page layout.

        Returns
        -------
        dbc.Container
            Page layout.
        """
        return section_layout.build_page_layout(self, self.sections)


_page = ApplyCalibrationPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/calibrate",
    name="Apply Calibration",
    order=3,
    layout=layout,
)
