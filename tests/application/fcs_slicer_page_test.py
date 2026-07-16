# -*- coding: utf-8 -*-

import importlib

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.upload_limits import get_max_upload_bytes
from RosettaX.workflow.calibration_cards import COLLAPSE_ID_TYPE


def _find_component_by_id(component, target_id: str):
    if getattr(component, "id", None) == target_id:
        return component

    children = getattr(component, "children", None)
    if children is None:
        return None
    if isinstance(children, (list, tuple)):
        for child in children:
            found = _find_component_by_id(child, target_id)
            if found is not None:
                return found
        return None
    return _find_component_by_id(children, target_id)


def _collect_text(component) -> list[str]:
    if component is None:
        return []
    if isinstance(component, str):
        return [component]

    children = getattr(component, "children", None)
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return [text for child in children for text in _collect_text(child)]
    return _collect_text(children)


def test_header_includes_three_workflow_overview_cards(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    slicer_main = importlib.import_module("RosettaX.pages.p21_fcs_slicer.main")

    header = slicer_main.FCSSlicerPage()._build_header_card()
    text_nodes = _collect_text(header)

    assert "Upload compatible files" in text_nodes
    assert "Choose channels" in text_nodes
    assert "Download sliced files" in text_nodes
    assert "1" in text_nodes
    assert "2" in text_nodes
    assert "3" in text_nodes


def test_upload_uses_configured_file_size_limit(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    slicer_main = importlib.import_module("RosettaX.pages.p21_fcs_slicer.main")
    page = slicer_main.FCSSlicerPage()

    layout = page.layout()
    upload = _find_component_by_id(layout, page.ids.upload)

    assert upload is not None
    assert upload.max_size == get_max_upload_bytes()
    assert "Maximum file size:" in " ".join(_collect_text(layout))


def test_workflow_cards_start_collapsed(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    slicer_main = importlib.import_module("RosettaX.pages.p21_fcs_slicer.main")
    page = slicer_main.FCSSlicerPage()

    cards = [
        page._build_upload_card(),
        page._build_selection_card(),
        page._build_export_card(),
    ]

    for section_number, card in enumerate(cards, start=1):
        collapse = card.children[1]
        assert isinstance(collapse, dbc.Collapse)
        assert collapse.kwargs["is_open"] is False
        assert collapse.id == {
            "type": COLLAPSE_ID_TYPE,
            "page": page.ids.page_prefix,
            "section": str(section_number),
        }
