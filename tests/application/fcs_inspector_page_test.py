"""Regression tests for application FCS inspector page."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash
import dash_bootstrap_components as dbc
from dash import html


def test_fcs_inspector_registers_callbacks_and_retains_page_instance(monkeypatch) -> None:
    """Check FCS inspector registers callbacks and retains page instance."""
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p23_fcs_inspector.main import FCSInspectorPage

    page = FCSInspectorPage()

    assert page.register_callbacks() is page

def test_fcs_inspector_uses_one_open_card(monkeypatch) -> None:
    """Check the upload, status, and report share a directly visible card body."""
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p23_fcs_inspector.main import FCSInspectorPage

    page = FCSInspectorPage()
    card, = page.layout().children
    assert isinstance(card, dbc.Card)
    header, body = card.children
    assert isinstance(header.children, html.H1)
    assert isinstance(body, dbc.CardBody)
    assert {getattr(child, "id", None) for child in body.children} >= {
        "fcs-inspector-upload",
        "fcs-inspector-status",
        "fcs-inspector-report",
    }
