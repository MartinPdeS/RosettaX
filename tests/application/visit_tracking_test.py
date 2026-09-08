# -*- coding: utf-8 -*-

from flask import Flask

from RosettaX.application import callbacks as application_callbacks
from RosettaX.utils import usage_metrics


class Test_VisitTracking:
    def test_resolve_client_ip_address_prefers_forwarded_for(self) -> None:
        app = Flask(__name__)

        with app.test_request_context(
            "/",
            headers={"X-Forwarded-For": "8.8.8.8, 10.0.0.1"},
        ):
            assert application_callbacks.resolve_client_ip_address() == "8.8.8.8"

    def test_resolve_client_ip_address_falls_back_to_remote_addr(self) -> None:
        app = Flask(__name__)

        with app.test_request_context(
            "/",
            environ_overrides={"REMOTE_ADDR": "1.1.1.1"},
        ):
            assert application_callbacks.resolve_client_ip_address() == "1.1.1.1"

    def test_record_request_page_visit_persists_request_metadata(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )

        app = Flask(__name__)

        with app.test_request_context(
            "/settings",
            headers={
                "X-Forwarded-For": "8.8.8.8, 10.0.0.1",
                "User-Agent": "Mozilla/5.0",
            },
        ):
            application_callbacks.record_request_page_visit("/settings")

        events = usage_metrics.load_visit_events()

        assert len(events) == 1
        assert events[0].ip_address == "8.8.8.8"
        assert events[0].path == "/settings"
        assert events[0].user_agent == "Mozilla/5.0"
        assert events[0].visited_at

    def test_record_request_page_visit_skips_local_visits_when_untracked(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )

        app = Flask(__name__)

        with app.test_request_context(
            "/settings",
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        ):
            application_callbacks.record_request_page_visit("/settings")

        assert usage_metrics.load_visit_events() == []

    def test_record_request_page_visit_works_without_request_context_when_local_enabled(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_VISIT_LOG_PATH_ENV_VAR,
            str(tmp_path / "visit_log.jsonl"),
        )
        monkeypatch.setenv(
            usage_metrics.ROSETTAX_TRACK_LOCAL_VISITS_ENV_VAR,
            "true",
        )

        application_callbacks.record_request_page_visit(None)

        events = usage_metrics.load_visit_events()

        assert len(events) == 1
        assert events[0].ip_address == ""
        assert events[0].path == "/"
