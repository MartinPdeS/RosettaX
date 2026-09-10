
import importlib

import dash
import pytest

from RosettaX.pages.p22_admin import services
from RosettaX.utils import usage_metrics


def _collect_component_ids(component) -> set[str]:
    component_id = getattr(component, "id", None)
    collected_ids = {component_id} if isinstance(component_id, str) else set()
    children = getattr(component, "children", None)

    if children is None:
        return collected_ids

    if isinstance(children, (list, tuple)):
        for child in children:
            collected_ids.update(_collect_component_ids(child))
        return collected_ids

    collected_ids.update(_collect_component_ids(children))
    return collected_ids


def _import_admin_main(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

    admin_main = importlib.import_module("RosettaX.pages.p22_admin.main")
    return importlib.reload(admin_main)


class Test_AdminPage:
    def test_admin_page_registers_admin_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        registered_pages: list[dict] = []
        monkeypatch.setattr(
            dash,
            "register_page",
            lambda *args, **kwargs: registered_pages.append(kwargs),
        )

        admin_main = importlib.import_module("RosettaX.pages.p22_admin.main")
        importlib.reload(admin_main)

        assert any(
            registration.get("path") == "/admin" for registration in registered_pages
        )

    def test_layout_denies_access_when_token_is_not_configured(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        monkeypatch.delenv(services.ROSETTAX_ADMIN_TOKEN_ENV_VAR, raising=False)
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )

        admin_main = _import_admin_main(monkeypatch)

        layout = admin_main.layout(token="anything")

        assert "admin-visits-over-time-graph" not in _collect_component_ids(layout)

    def test_layout_denies_access_with_wrong_or_missing_token(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        monkeypatch.setenv(services.ROSETTAX_ADMIN_TOKEN_ENV_VAR, "secret-token")
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )

        admin_main = _import_admin_main(monkeypatch)

        missing_token_layout = admin_main.layout()
        wrong_token_layout = admin_main.layout(token="not-the-token")

        assert "admin-visits-over-time-graph" not in _collect_component_ids(missing_token_layout)
        assert "admin-visits-over-time-graph" not in _collect_component_ids(wrong_token_layout)

    def test_layout_grants_access_with_matching_token(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        monkeypatch.setenv(services.ROSETTAX_ADMIN_TOKEN_ENV_VAR, "secret-token")
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(tmp_path / "usage_metrics.json"),
        )

        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-08T10:00:00+00:00",
        )

        admin_main = _import_admin_main(monkeypatch)

        layout = admin_main.layout(token="secret-token")
        component_ids = _collect_component_ids(layout)

        assert "admin-visits-over-time-graph" in component_ids
        assert "admin-page-breakdown-graph" in component_ids
        assert "admin-recent-visits-table" in component_ids
        assert "admin-stat-total-visits" in component_ids
        assert "admin-stat-unique-visitors" in component_ids
        assert "admin-stat-visits-today" in component_ids
        assert "admin-stat-unique-visitors-today" in component_ids
        assert "admin-stat-apply-clicks" in component_ids
        assert "admin-stat-calibrated-files" in component_ids


class Test_AdminServices:
    def test_token_gate_requires_configured_token(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv(services.ROSETTAX_ADMIN_TOKEN_ENV_VAR, raising=False)

        assert not services.is_admin_access_granted("anything")
        assert not services.is_admin_access_granted(None)

    def test_token_gate_requires_exact_match(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(services.ROSETTAX_ADMIN_TOKEN_ENV_VAR, "secret-token")

        assert services.is_admin_access_granted("secret-token")
        assert not services.is_admin_access_granted("secret-token-extra")
        assert not services.is_admin_access_granted("")
        assert not services.is_admin_access_granted(None)

    def test_collect_admin_dashboard_data_aggregates_metrics_and_visits(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(tmp_path / "usage_metrics.json"),
        )

        usage_metrics.record_apply_button_click()
        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-08T10:00:00+00:00",
        )

        dashboard_data = services.collect_admin_dashboard_data()

        assert dashboard_data.metrics.apply_button_click_count == 1
        assert dashboard_data.visit_summary.total_visits == 1
        assert dashboard_data.visit_summary.unique_visitor_count == 1
        assert dashboard_data.generated_at.endswith("UTC")

    def test_build_visits_over_time_figure_has_visit_and_unique_traces(self) -> None:
        visit_summary = usage_metrics.summarize_visit_events(
            [
                usage_metrics.VisitEvent(
                    visited_at="2026-09-07T10:00:00+00:00",
                    ip_address="8.8.8.8",
                    path="/",
                    user_agent="agent",
                ),
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T10:00:00+00:00",
                    ip_address="1.1.1.1",
                    path="/",
                    user_agent="agent",
                ),
            ]
        )

        figure = services.build_visits_over_time_figure(
            visit_summary=visit_summary,
            theme="dark",
        )

        assert len(figure.data) == 2
        assert list(figure.data[0].x) == ["2026-09-07", "2026-09-08"]
        assert list(figure.data[0].y) == [1, 1]
        assert list(figure.data[1].y) == [1, 1]

    def test_build_visits_over_time_figure_handles_empty_summary(self) -> None:
        figure = services.build_visits_over_time_figure(
            visit_summary=usage_metrics.VisitSummary(),
            theme="light",
        )

        assert len(figure.data) == 2
        assert list(figure.data[0].x) == []

    def test_build_page_breakdown_figure_orders_pages_by_visit_count(self) -> None:
        visit_summary = usage_metrics.summarize_visit_events(
            [
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T10:00:00+00:00",
                    ip_address="8.8.8.8",
                    path="/",
                    user_agent="agent",
                ),
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T11:00:00+00:00",
                    ip_address="8.8.8.8",
                    path="/settings",
                    user_agent="agent",
                ),
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T12:00:00+00:00",
                    ip_address="1.1.1.1",
                    path="/settings",
                    user_agent="agent",
                ),
            ]
        )

        figure = services.build_page_breakdown_figure(
            visit_summary=visit_summary,
            theme="dark",
        )

        assert len(figure.data) == 1
        assert list(figure.data[0].y) == ["/", "/settings"]
        assert list(figure.data[0].x) == [1, 2]

    def test_build_recent_visit_rows_formats_table_rows(self) -> None:
        visit_summary = usage_metrics.summarize_visit_events(
            [
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T10:00:00+00:00",
                    ip_address="8.8.8.8",
                    path="/",
                    user_agent="Mozilla/5.0",
                ),
                usage_metrics.VisitEvent(
                    visited_at="2026-09-08T11:00:00+00:00",
                    ip_address="",
                    path="/help",
                    user_agent="",
                ),
            ],
            include_local=True,
        )

        rows = services.build_recent_visit_rows(visit_summary=visit_summary)

        assert rows == [
            {
                "visited_at": "2026-09-08 11:00:00 UTC",
                "ip_address": "unknown",
                "path": "/help",
                "user_agent": "unknown",
            },
            {
                "visited_at": "2026-09-08 10:00:00 UTC",
                "ip_address": "8.8.8.8",
                "path": "/",
                "user_agent": "Mozilla/5.0",
            },
        ]
