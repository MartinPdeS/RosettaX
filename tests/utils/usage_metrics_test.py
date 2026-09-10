
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from RosettaX.utils import usage_metrics


class Test_UsageMetrics:
    def test_usage_metrics_round_trip_click_and_file_counters(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metrics_file_path = tmp_path / "usage_metrics.json"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(metrics_file_path),
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics()

        usage_metrics.record_apply_button_click()
        usage_metrics.record_apply_button_click()
        usage_metrics.record_home_page_visit()
        usage_metrics.record_home_page_visit()
        usage_metrics.record_home_page_visit()
        usage_metrics.record_calibrated_files(
            file_count=7,
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics(
            apply_button_click_count=2,
            total_calibrated_files=7,
            home_page_visit_count=3,
        )

    def test_record_home_page_visit_increments_counter(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metrics_file_path = tmp_path / "usage_metrics.json"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(metrics_file_path),
        )

        usage_metrics.record_home_page_visit()

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics(
            apply_button_click_count=0,
            total_calibrated_files=0,
            home_page_visit_count=1,
        )

    def test_usage_metrics_ignores_invalid_payload_values(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        metrics_file_path = tmp_path / "usage_metrics.json"
        metrics_file_path.write_text(
            (
                '{"apply_button_click_count": "abc", '
                '"total_calibrated_files": -3, '
                '"home_page_visit_count": "invalid"}'
            ),
            encoding="utf-8",
        )

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_USAGE_METRICS_PATH_ENV_VAR,
            str(metrics_file_path),
        )

        assert usage_metrics.load_usage_metrics() == usage_metrics.UsageMetrics(
            apply_button_click_count=0,
            total_calibrated_files=0,
            home_page_visit_count=0,
        )


class Test_VisitLog:
    def test_is_local_ip_identifies_local_and_loopback_addresses(self) -> None:
        assert usage_metrics.is_local_ip("127.0.0.1")
        assert usage_metrics.is_local_ip("::1")
        assert usage_metrics.is_local_ip("localhost")
        assert usage_metrics.is_local_ip("0.0.0.0")
        assert usage_metrics.is_local_ip("192.168.1.10")
        assert usage_metrics.is_local_ip("10.0.0.2")
        assert usage_metrics.is_local_ip("172.16.0.1")
        assert usage_metrics.is_local_ip("")
        assert usage_metrics.is_local_ip(None)

        assert not usage_metrics.is_local_ip("8.8.8.8")
        assert not usage_metrics.is_local_ip("1.1.1.1")
        assert not usage_metrics.is_local_ip("93.184.216.34")

    def test_record_page_visit_skips_local_ips_by_default(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        usage_metrics.record_page_visit(
            ip_address="127.0.0.1",
            path="/",
            user_agent="agent",
        )

        assert usage_metrics.load_visit_events() == []

    def test_record_and_load_page_visits_round_trip_for_public_ips(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-06T10:00:00+00:00",
        )
        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/settings",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-08T11:00:00+00:00",
        )
        usage_metrics.record_page_visit(
            ip_address="1.1.1.1",
            path="/settings",
            user_agent="curl/8.0",
            visited_at="2026-09-08T12:00:00+00:00",
        )

        events = usage_metrics.load_visit_events()

        assert events == [
            usage_metrics.VisitEvent(
                visited_at="2026-09-06T10:00:00+00:00",
                ip_address="8.8.8.8",
                path="/",
                user_agent="Mozilla/5.0",
            ),
            usage_metrics.VisitEvent(
                visited_at="2026-09-08T11:00:00+00:00",
                ip_address="8.8.8.8",
                path="/settings",
                user_agent="Mozilla/5.0",
            ),
            usage_metrics.VisitEvent(
                visited_at="2026-09-08T12:00:00+00:00",
                ip_address="1.1.1.1",
                path="/settings",
                user_agent="curl/8.0",
            ),
        ]

    def test_record_page_visit_generates_timestamp_when_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        event = usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="",
            user_agent=None,
        )

        assert event.visited_at
        assert event.path == "/"
        assert event.user_agent == ""

        events = usage_metrics.load_visit_events()

        assert len(events) == 1
        assert events[0].visited_at == event.visited_at

    def test_load_visit_events_skips_malformed_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"
        visit_log_file_path.write_text(
            "\n".join(
                [
                    "not-json",
                    json.dumps({"no_timestamp": True}),
                    json.dumps(
                        {
                            "visited_at": "2026-09-08T10:00:00+00:00",
                            "ip_address": "8.8.8.8",
                            "path": "/",
                            "user_agent": "Mozilla/5.0",
                        }
                    ),
                    "",
                ]
            ),
            encoding="utf-8",
        )

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        events = usage_metrics.load_visit_events()

        assert events == [
            usage_metrics.VisitEvent(
                visited_at="2026-09-08T10:00:00+00:00",
                ip_address="8.8.8.8",
                path="/",
                user_agent="Mozilla/5.0",
            ),
        ]

    def test_load_visit_events_returns_empty_when_log_is_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "missing_visit_log.jsonl"),
        )

        assert usage_metrics.load_visit_events() == []

    def test_summarize_visit_events_builds_daily_series_and_counts(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-06T10:00:00+00:00",
        )
        usage_metrics.record_page_visit(
            ip_address="8.8.8.8",
            path="/settings",
            user_agent="Mozilla/5.0",
            visited_at="2026-09-08T11:00:00+00:00",
        )
        usage_metrics.record_page_visit(
            ip_address="1.1.1.1",
            path="/settings",
            user_agent="curl/8.0",
            visited_at="2026-09-08T12:00:00+00:00",
        )

        summary = usage_metrics.summarize_visit_events(
            usage_metrics.load_visit_events(),
            today="2026-09-08",
        )

        assert summary.total_visits == 3
        assert summary.unique_visitor_count == 2
        assert summary.visits_today == 2
        assert summary.unique_visitors_today == 2
        assert summary.daily.dates == ["2026-09-06", "2026-09-07", "2026-09-08"]
        assert summary.daily.visit_counts == [1, 0, 2]
        assert summary.daily.unique_visitor_counts == [1, 0, 2]
        assert summary.page_visit_counts == [("/settings", 2), ("/", 1)]
        assert [event.ip_address for event in summary.recent_visits] == [
            "1.1.1.1",
            "8.8.8.8",
            "8.8.8.8",
        ]

    def test_summarize_visit_events_filters_local_ips_by_default(self) -> None:
        events = [
            usage_metrics.VisitEvent(
                visited_at="2026-09-08T10:00:00+00:00",
                ip_address="127.0.0.1",
                path="/",
                user_agent="agent",
            ),
            usage_metrics.VisitEvent(
                visited_at="2026-09-08T10:05:00+00:00",
                ip_address="8.8.8.8",
                path="/",
                user_agent="agent",
            ),
        ]

        summary = usage_metrics.summarize_visit_events(events, today="2026-09-08")

        assert summary.total_visits == 1
        assert summary.unique_visitor_count == 1
        assert [event.ip_address for event in summary.recent_visits] == ["8.8.8.8"]

    def test_summarize_visit_events_limits_recent_visits(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        visit_log_file_path = tmp_path / "visit_log.jsonl"

        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(visit_log_file_path),
        )

        for index in range(5):
            usage_metrics.record_page_visit(
                ip_address=f"8.8.8.{10 + index}",
                path="/",
                user_agent="agent",
                visited_at=f"2026-09-08T10:0{index}:00+00:00",
            )

        summary = usage_metrics.summarize_visit_events(
            usage_metrics.load_visit_events(),
            recent_limit=2,
        )

        assert [event.ip_address for event in summary.recent_visits] == [
            "8.8.8.14",
            "8.8.8.13",
        ]

    def test_summarize_visit_events_handles_empty_history(self) -> None:
        summary = usage_metrics.summarize_visit_events([], today="2026-09-08")

        assert summary == usage_metrics.VisitSummary()

    def test_summarize_visit_events_defaults_today_to_current_utc_date(self) -> None:
        current_utc_date = datetime.now(timezone.utc).date().isoformat()

        summary = usage_metrics.summarize_visit_events(
            [
                usage_metrics.VisitEvent(
                    visited_at=f"{current_utc_date}T10:00:00+00:00",
                    ip_address="8.8.8.8",
                    path="/",
                    user_agent="agent",
                ),
            ]
        )

        assert summary.visits_today == 1
        assert summary.unique_visitors_today == 1

    def test_visit_event_from_dict_ignores_invalid_payload(self) -> None:
        assert usage_metrics.VisitEvent.from_dict("not-a-dict") == usage_metrics.VisitEvent()
