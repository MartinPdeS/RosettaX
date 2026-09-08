# -*- coding: utf-8 -*-

import importlib
from typing import Any

import dash
import dash_bootstrap_components as dbc
import pytest

from RosettaX.application.callbacks import (
    register_application_callbacks,
    resolve_active_profile_runtime_config,
)
from RosettaX.workflow import calibration_cards


def _find_component_by_id(component: Any, component_id: Any) -> Any | None:
    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found = _find_component_by_id(child, component_id)
            if found is not None:
                return found
    elif children is not None:
        return _find_component_by_id(children, component_id)
    return None


def _collect_text(component: Any) -> list[str]:
    if isinstance(component, str):
        return [component]

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        return [text for child in children for text in _collect_text(child)]
    return _collect_text(children) if children is not None else []


@pytest.mark.parametrize(
    ("module_name", "page_class_name", "page_name", "section_keys", "subtitles"),
    [
        (
            "RosettaX.pages.p02_fluorescence.main",
            "FluorescencePage",
            "fluorescent_calibration",
            ("1", "2", "3", "4", "5"),
            tuple(
                calibration_cards.CALIBRATION_WORKFLOW_SUBTITLES[
                    "fluorescent_calibration"
                ].values()
            ),
        ),
        (
            "RosettaX.pages.p03_scattering.main",
            "ScatterCalibrationPage",
            "scattering_calibration",
            ("1", "2", "3", "4", "5", "6"),
            tuple(
                calibration_cards.CALIBRATION_WORKFLOW_SUBTITLES[
                    "scattering_calibration"
                ].values()
            ),
        ),
        (
            "RosettaX.pages.p04_calibrate.main",
            "ApplyCalibrationPage",
            "apply_calibration",
            ("1", "2", "3"),
            tuple(
                calibration_cards.CALIBRATION_WORKFLOW_SUBTITLES[
                    "apply_calibration"
                ].values()
            ),
        ),
        (
            "RosettaX.pages.p08_cross_calibration.main",
            "CrossCalibrationPage",
            "cross-calibration",
            ("1", "2", "3"),
            (
                "Load the reference and routine-bead calibrations used to build the transfer relation.",
                "Inspect the fitted relation before exporting it for routine-bead calibration.",
                "Download the transfer calibration for later use with the routine bead set.",
            ),
        ),
    ],
)
def test_calibration_workflow_cards_start_collapsed_with_subtitles(
    monkeypatch,
    module_name: str,
    page_class_name: str,
    page_name: str,
    section_keys: tuple[str, ...],
    subtitles: tuple[str, ...],
) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    sections_callback_module_name = module_name.rsplit(".", 1)[0] + ".sections.callbacks"
    if page_name != "cross-calibration":
        sections_callbacks = importlib.import_module(sections_callback_module_name)
        monkeypatch.setattr(
            sections_callbacks,
            "register_callbacks",
            lambda _sections: None,
        )
    page_module = importlib.import_module(module_name)
    layout = getattr(page_module, page_class_name)().layout()

    for section_key, subtitle in zip(section_keys, subtitles, strict=True):
        card = _find_component_by_id(
            layout,
            calibration_cards.workflow_section_dom_id(
                page_name=page_name,
                section_key=section_key,
            ),
        )

        assert isinstance(card, dbc.Card)
        assert isinstance(card.children[1], dbc.Collapse)
        assert card.children[1].kwargs["is_open"] is False
        assert calibration_cards.collapse_label(is_open=False) in _collect_text(
            card.children[0]
        )
        assert subtitle in _collect_text(card.children[0])


def test_calibration_card_callback_does_not_hydrate_card_state() -> None:
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    register_application_callbacks(app)

    card_callbacks = [
        callback
        for callback in app._callback_list
        if calibration_cards.COLLAPSE_ID_TYPE in str(callback["output"])
    ]

    assert len(card_callbacks) == 1
    assert card_callbacks[0]["prevent_initial_call"] is True


def test_card_callback_owns_header_and_workflow_step_actions() -> None:
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    register_application_callbacks(app)

    card_callback = next(
        callback
        for callback in app._callback_list
        if calibration_cards.COLLAPSE_ID_TYPE in str(callback["output"])
    )
    input_ids = {str(input_spec["id"]) for input_spec in card_callback["inputs"]}

    assert any(calibration_cards.TOGGLE_ID_TYPE in input_id for input_id in input_ids)
    assert any(
        calibration_cards.WORKFLOW_STEP_CARD_ID_TYPE in input_id
        for input_id in input_ids
    )


def test_active_browser_profile_keeps_workflow_cards_collapsed() -> None:
    active_profile_config = resolve_active_profile_runtime_config(
        {
            "profiles": {
                "collapsed.json": {
                    "ui": {"collapse_calibration_cards": True},
                }
            },
            "selected_profile": "collapsed.json",
        },
        selected_profile_name="collapsed.json",
    )

    is_open, label = calibration_cards.resolve_card_toggle(
        triggered_id="browser-profiles-store",
        is_open=True,
        runtime_config_data=active_profile_config,
    )

    assert is_open is False
    assert label == "Show"
