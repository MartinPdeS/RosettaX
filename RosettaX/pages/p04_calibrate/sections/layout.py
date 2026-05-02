# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import dcc

from ..state import ApplyCalibrationPageState


def build_page_layout(page, sections) -> dbc.Container:
    """
    Build the apply calibration page layout from the section instances.
    """
    return dbc.Container(
        [
            dcc.Location(
                id=page.ids.Page.location,
                refresh=False,
            ),
            _build_page_state_store(page),
            _build_selected_calibration_path_store(page),
            _build_selected_calibration_summary_store(page),
            _build_uploaded_fcs_path_store(page),
            dbc.Container(
                [
                    section.get_layout()
                    for section in sections
                ],
                fluid=True,
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "18px",
                    "padding": "0px",
                },
            ),
        ],
        fluid=True,
        style=page.container_style,
    )


def _build_page_state_store(page) -> dcc.Store:
    """
    Build the serialized page state store.
    """
    return dcc.Store(
        id=page.ids.State.page_state_store,
        data=ApplyCalibrationPageState.empty().to_dict(),
        storage_type="session",
    )


def _build_selected_calibration_path_store(page) -> dcc.Store:
    """
    Build the selected calibration path store.
    """
    return dcc.Store(
        id=page.ids.Stores.selected_calibration_path_store,
        data=None,
        storage_type="session",
    )


def _build_selected_calibration_summary_store(page) -> dcc.Store:
    """
    Build the selected calibration summary store.
    """
    return dcc.Store(
        id=page.ids.Stores.selected_calibration_summary_store,
        data=None,
        storage_type="session",
    )


def _build_uploaded_fcs_path_store(page) -> dcc.Store:
    """
    Build the uploaded FCS path store.
    """
    return dcc.Store(
        id=page.ids.Stores.uploaded_fcs_path_store,
        data=None,
        storage_type="session",
    )
