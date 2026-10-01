
import importlib

import dash
import pytest

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


def _collect_components(component) -> list[object]:
    if component is None or isinstance(component, str):
        return []

    collected = [component]
    children = getattr(component, "children", None)

    if isinstance(children, (list, tuple)):
        for child in children:
            collected.extend(_collect_components(child))
    else:
        collected.extend(_collect_components(children))

    return collected


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
            "record_home_page_visit",
            lambda: UsageMetrics(
                apply_button_click_count=12,
                total_calibrated_files=34,
                home_page_visit_count=56,
            ),
        )
        layout = home_main.HomePage().layout()
        text_nodes = _collect_text(layout)

        assert "Version:" in text_nodes
        expected_version = home_main.resolve_software_version_label()
        assert expected_version in text_nodes
        assert "Support Developer" in text_nodes
        assert "Project resources" not in text_nodes
        assert "What you can do" in text_nodes
        assert "Calibrations" in text_nodes
        assert "FCS tools" in text_nodes
        assert "Manage" in text_nodes
        assert "Learn" in text_nodes
        assert "RosettaX usage metrics." in text_nodes
        assert "Home page visits" in text_nodes
        assert "Apply button clicks" in text_nodes
        assert "Total calibrated files" in text_nodes
        assert "56" in text_nodes
        assert "12" in text_nodes
        assert "34" in text_nodes

        citation_buttons = [
            component
            for component in _collect_components(layout)
            if getattr(component, "children", None) == "Citing this work"
        ]
        assert len(citation_buttons) == 1
        assert citation_buttons[0].href == "/citation"


@pytest.mark.parametrize(
    "installed_version, generated_version, expected",
    [
        ("1.2.3", "0.0", "v1.2.3"),
        ("1.2.3", "0.9.0", "v1.2.3"),
        ("0.0", "0.9.0", "v0.9.0"),
        (None, "0.9.0", "v0.9.0"),
        ("v0.9.0", "0.0", "v0.9.0"),
        ("0.0.1", "0.0", "v0.0.1"),
        ("0.0.dev2", "0.9.0", "v0.9.0"),
        (None, "0.0.0", "Unavailable"),
    ],
)
def test_home_version_resolves_installed_metadata_and_source_fallback(
    monkeypatch, installed_version, generated_version, expected,
):
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    home_main = importlib.import_module("RosettaX.pages.p01_home.main")

    def read_installed_version(_name):
        if installed_version is None:
            raise home_main.importlib.metadata.PackageNotFoundError("RosettaX")
        return installed_version

    monkeypatch.setattr(home_main.importlib.metadata, "version", read_installed_version)
    monkeypatch.setattr(home_main, "__version__", generated_version)
    assert home_main.resolve_software_version_label() == expected
    assert expected in _collect_text(home_main.HomePage()._github_tag_widget())


class Test_GitHubTagResolution:
    def test_resolve_latest_github_tag_label_uses_ttl_cache(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        home_main = importlib.import_module("RosettaX.pages.p01_home.main")
        home_main = importlib.reload(home_main)

        current_time = {"value": 100.0}
        fetched_labels = iter(["v1.2.3", "v1.2.4"])

        monkeypatch.setattr(
            home_main.time,
            "monotonic",
            lambda: current_time["value"],
        )
        monkeypatch.setattr(
            home_main,
            "_fetch_latest_github_tag_label",
            lambda: next(fetched_labels),
        )

        assert home_main.resolve_latest_github_tag_label() == "v1.2.3"

        current_time["value"] += home_main.GITHUB_TAG_CACHE_TTL_SECONDS - 1.0
        assert home_main.resolve_latest_github_tag_label() == "v1.2.3"

        current_time["value"] += 2.0
        assert home_main.resolve_latest_github_tag_label() == "v1.2.4"

    def test_resolve_latest_github_tag_label_falls_back_to_last_known_tag(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        home_main = importlib.import_module("RosettaX.pages.p01_home.main")
        home_main = importlib.reload(home_main)

        current_time = {"value": 100.0}
        fetched_labels = iter(["v1.2.3", None])

        monkeypatch.setattr(
            home_main.time,
            "monotonic",
            lambda: current_time["value"],
        )
        monkeypatch.setattr(
            home_main,
            "_fetch_latest_github_tag_label",
            lambda: next(fetched_labels),
        )

        assert home_main.resolve_latest_github_tag_label() == "v1.2.3"

        current_time["value"] += home_main.GITHUB_TAG_CACHE_TTL_SECONDS + 1.0
        assert home_main.resolve_latest_github_tag_label() == "v1.2.3"
