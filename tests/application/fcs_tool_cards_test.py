# -*- coding: utf-8 -*-

import importlib
import json
from typing import Any

import dash
import dash_bootstrap_components as dbc
import pytest

from RosettaX.application.callbacks import register_application_callbacks
from RosettaX.workflow import calibration_cards


def _collect_pattern_ids(component: Any) -> list[dict[str, str]]:
    component_id = getattr(component, "id", None)
    pattern_ids = [component_id] if isinstance(component_id, dict) else []
    children = getattr(component, "children", None)

    if isinstance(children, (list, tuple)):
        for child in children:
            pattern_ids.extend(_collect_pattern_ids(child))
    elif children is not None:
        pattern_ids.extend(_collect_pattern_ids(children))

    return pattern_ids


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


def _callback_input_id_types(callback: dict[str, Any]) -> set[str]:
    component_id_types = set()
    for callback_input in callback["inputs"]:
        component_id = callback_input["id"]
        if isinstance(component_id, str) and component_id.startswith("{"):
            component_id = json.loads(component_id)
        if isinstance(component_id, dict):
            component_id_types.add(component_id["type"])
    return component_id_types


@pytest.mark.parametrize(
    (
        "module_name",
        "page_class_name",
        "page_name",
        "section_keys",
        "step_section_keys",
    ),
    [
        (
            "RosettaX.pages.p10_visualization.main",
            "VisualizationPage",
            "visualization",
            ("1",),
            (),
        ),
        (
            "RosettaX.pages.p21_fcs_slicer.main",
            "FCSSlicerPage",
            "fcs-slicer",
            ("1", "2", "3"),
            ("1", "2", "3"),
        ),
        (
            "RosettaX.pages.p23_fcs_inspector.main",
            "FCSInspectorPage",
            "fcs-inspector",
            ("1", "2"),
            ("1", "2"),
        ),
        (
            "RosettaX.pages.p24_fcs_merge.main",
            "FCSMergePage",
            "fcs-merge",
            ("1", "2"),
            ("1", "2"),
        ),
    ],
)
def test_fcs_tool_layouts_include_collapsible_cards_with_uniform_gaps(
    monkeypatch,
    module_name: str,
    page_class_name: str,
    page_name: str,
    section_keys: tuple[str, ...],
    step_section_keys: tuple[str, ...],
) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    page_module = importlib.import_module(module_name)
    layout = getattr(page_module, page_class_name)().layout()
    pattern_ids = _collect_pattern_ids(layout)
    card_stack = (
        layout
        if page_name == "visualization"
        else layout.children[0]
    )

    assert card_stack.style == {
        "display": "flex",
        "flexDirection": "column",
        "gap": calibration_cards.FCS_TOOL_CARD_GAP,
    }
    for section_key in section_keys:
        assert {
            "type": calibration_cards.TOGGLE_ID_TYPE,
            "page": page_name,
            "section": section_key,
        } in pattern_ids
        assert {
            "type": calibration_cards.COLLAPSE_ID_TYPE,
            "page": page_name,
            "section": section_key,
        } in pattern_ids
        section_card = _find_component_by_id(
            layout,
            calibration_cards.workflow_section_dom_id(
                page_name=page_name,
                section_key=section_key,
            ),
        )
        assert section_card is not None
        assert "marginBottom" not in section_card.style

    direct_cards = [
        child for child in card_stack.children if isinstance(child, dbc.Card)
    ]
    assert direct_cards[0].style["marginBottom"] == "0px"

    for section_key in step_section_keys:
        assert {
            "type": calibration_cards.WORKFLOW_STEP_CARD_ID_TYPE,
            "page": page_name,
            "section": section_key,
        } in pattern_ids


def test_card_toggle_callback_has_no_required_workflow_step_matcher() -> None:
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    register_application_callbacks(app)

    callback_input_types = [
        _callback_input_id_types(callback)
        for callback in app.callback_map.values()
    ]

    assert {
        calibration_cards.TOGGLE_ID_TYPE,
    } in callback_input_types
    assert {
        calibration_cards.WORKFLOW_STEP_CARD_ID_TYPE,
    } in callback_input_types
