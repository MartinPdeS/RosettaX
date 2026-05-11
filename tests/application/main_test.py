# -*- coding: utf-8 -*-

import importlib
from types import SimpleNamespace

application_main = importlib.import_module("RosettaX.application.main")


class Test_ApplicationMain:
    def test_configure_logging_uses_info_by_default(self) -> None:
        resolved_log_level = application_main.configure_logging(
            debug=False,
            log_level="INFO",
        )

        assert resolved_log_level == 20

    def test_configure_logging_promotes_debug_flag(self) -> None:
        resolved_log_level = application_main.configure_logging(
            debug=True,
            log_level="ERROR",
        )

        assert resolved_log_level == 10

    def test_main_passes_runtime_flags_to_application(
        self,
        monkeypatch,
    ) -> None:
        captured_application_kwargs: dict[str, object] = {}
        application_run_calls: list[bool] = []

        class _FakeApplication:
            def __init__(self, **kwargs) -> None:
                captured_application_kwargs.update(kwargs)

            def run(self) -> None:
                application_run_calls.append(True)

        monkeypatch.setattr(
            application_main,
            "_parse_args",
            lambda argv: SimpleNamespace(
                host="0.0.0.0",
                port=9000,
                no_browser=True,
                debug=True,
                log_level="WARNING",
            ),
        )
        monkeypatch.setattr(application_main, "RosettaXApplication", _FakeApplication)

        application_main.main(["--debug"])

        assert captured_application_kwargs == {
            "host": "0.0.0.0",
            "port": 9000,
            "open_browser": False,
            "debug": True,
        }
        assert application_run_calls == [True]
