# -*- coding: utf-8 -*-

import importlib
from typing import Any

import dash
import pytest

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


@pytest.mark.parametrize(
    ("module_name", "page_class_name", "page_name", "section_keys"),
    [
        (
            "RosettaX.pages.p10_visualization.main",
            "VisualizationPage",
            "visualization",
            ("1",),
        ),
        (
            "RosettaX.pages.p21_fcs_slicer.main",
            "FCSSlicerPage",
            "fcs-slicer",
            ("1", "2", "3"),
        ),
        (
            "RosettaX.pages.p23_fcs_inspector.main",
            "FCSInspectorPage",
            "fcs-inspector",
            ("1", "2"),
        ),
        (
            "RosettaX.pages.p24_fcs_merge.main",
            "FCSMergePage",
            "fcs-merge",
            ("1", "2"),
        ),
    ],
)
def test_fcs_tool_layouts_include_collapsible_calibration_card_ids(
    monkeypatch,
    module_name: str,
    page_class_name: str,
    page_name: str,
    section_keys: tuple[str, ...],
) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    page_module = importlib.import_module(module_name)
    layout = getattr(page_module, page_class_name)().layout()
    pattern_ids = _collect_pattern_ids(layout)

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
