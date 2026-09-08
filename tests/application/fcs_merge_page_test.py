# -*- coding: utf-8 -*-

import dash


def test_fcs_merge_registers_callbacks_and_retains_page_instance(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    from RosettaX.pages.p24_fcs_merge.main import FCSMergePage

    page = FCSMergePage()

    assert page.register_callbacks() is page
