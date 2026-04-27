# -*- coding: utf-8 -*-

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

    def __init__(self) -> None:
        self.container_style = {
            "paddingBottom": "48px",
        }

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
                self._build_page_state_store(),
                self._build_selected_calibration_path_store(),
                self._build_selected_calibration_summary_store(),
                self._build_uploaded_fcs_path_store(),
                *[
                    section.get_layout()
                    for section in self.sections
                ],
            ],
            fluid=True,
            style=self.container_style,
        )

    def _build_page_state_store(self) -> dcc.Store:
        """
        Build the serialized page state store.
        """
        return dcc.Store(
            id=self.ids.State.page_state_store,
            data=ApplyCalibrationPageState.empty().to_dict(),
            storage_type="session",
        )

    def _build_selected_calibration_path_store(self) -> dcc.Store:
        """
        Build the selected calibration path store.
        """
        return dcc.Store(
            id=self.ids.Stores.selected_calibration_path_store,
            data=None,
            storage_type="session",
        )

    def _build_selected_calibration_summary_store(self) -> dcc.Store:
        """
        Build the selected calibration summary store.
        """
        return dcc.Store(
            id=self.ids.Stores.selected_calibration_summary_store,
            data=None,
            storage_type="session",
        )

    def _build_uploaded_fcs_path_store(self) -> dcc.Store:
        """
        Build the uploaded FCS path store.
        """
        return dcc.Store(
            id=self.ids.Stores.uploaded_fcs_path_store,
            data=None,
            storage_type="session",
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