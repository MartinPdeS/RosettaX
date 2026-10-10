"""Regression tests for application FCS inspector page."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import dash


def test_fcs_inspector_registers_callbacks_and_retains_page_instance(monkeypatch) -> None:
    """Check FCS inspector registers callbacks and retains page instance."""
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p23_fcs_inspector.main import FCSInspectorPage

    page = FCSInspectorPage()

    assert page.register_callbacks() is page
