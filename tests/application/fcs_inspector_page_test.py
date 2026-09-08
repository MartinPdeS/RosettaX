import dash


def test_fcs_inspector_registers_callbacks_and_retains_page_instance(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p23_fcs_inspector.main import FCSInspectorPage

    page = FCSInspectorPage()

    assert page.register_callbacks() is page
