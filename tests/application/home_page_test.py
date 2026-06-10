# -*- coding: utf-8 -*-

import importlib

import dash

from RosettaX.utils.usage_metrics import UsageMetrics


def _collect_text(component) -> list[str]:
    if component is None:
        return []

    if isinstance(component, str):
        return [component]

    children = getattr(component, "children", None)

    if children is None:
        return []

    if isinstance(children, (list, tuple)):
        collected: list[str] = []
        for child in children:
            collected.extend(_collect_text(child))
        return collected

    return _collect_text(children)


class Test_HomePage:
    def test_layout_includes_usage_metrics_card(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        home_main = importlib.import_module("RosettaX.pages.p01_home.main")
        home_main = importlib.reload(home_main)

        monkeypatch.setattr(
            home_main.usage_metrics,
            "load_usage_metrics",
            lambda: UsageMetrics(
                apply_button_click_count=12,
                total_calibrated_files=34,
            ),
        )

        layout = home_main.HomePage().layout()
        text_nodes = _collect_text(layout)

        assert "Support Developer" in text_nodes
        assert "Project resources" not in text_nodes
        assert "Website usage metrics to date." in text_nodes
        assert "Apply button clicks" in text_nodes
        assert "Total calibrated files" in text_nodes
        assert "12" in text_nodes
        assert "34" in text_nodes