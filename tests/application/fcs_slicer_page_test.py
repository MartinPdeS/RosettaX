# -*- coding: utf-8 -*-

import importlib

import dash


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
