"""Regression tests for application FCS merge page."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import dash


def test_fcs_merge_registers_callbacks_and_retains_page_instance(monkeypatch) -> None:
    """Check FCS merge registers callbacks and retains page instance."""
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p24_fcs_merge.main import FCSMergePage

    page = FCSMergePage()

    assert page.register_callbacks() is page
