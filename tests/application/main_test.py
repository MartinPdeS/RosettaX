"""Regression tests for application main."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import importlib
from types import SimpleNamespace

application_main = importlib.import_module("RosettaX.application.main")
application_pages = importlib.import_module("RosettaX.application.pages")


class Test_ApplicationMain:
    """Regression checks for application main."""

    def test_configure_logging_uses_info_by_default(self) -> None:
        """Check configure logging uses info by default."""
        resolved_log_level = application_main.configure_logging(
            debug=False,
            log_level="INFO",
        )

        assert resolved_log_level == 20

    def test_configure_logging_promotes_debug_flag(self) -> None:
        """Check configure logging promotes debug flag."""
        resolved_log_level = application_main.configure_logging(
            debug=True,
            log_level="ERROR",
        )

        assert resolved_log_level == 10

    def test_main_passes_runtime_flags_to_application(
        self,
        monkeypatch,
    ) -> None:
        """Check main passes runtime flags to application."""
        captured_application_kwargs: dict[str, object] = {}
        application_run_calls: list[bool] = []

        class _FakeApplication:
            """Test double for fake application."""

            def __init__(self, **kwargs) -> None:
                """Initialize the state required by this test double."""
                captured_application_kwargs.update(kwargs)

            def run(self) -> None:
                """Run for this test."""
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

    def test_page_module_registry_includes_sample_files_page(self) -> None:
        """Check page module registry includes sample files page."""
        assert "RosettaX.pages.p09_sample_files.main" in application_pages.PAGE_MODULES

    def test_page_module_registry_includes_visualization_page(self) -> None:
        """Check page module registry includes visualization page."""
        assert "RosettaX.pages.p10_visualization.main" in application_pages.PAGE_MODULES

    def test_page_module_registry_includes_fcs_slicer_page(self) -> None:
        """Check page module registry includes FCS slicer page."""
        assert "RosettaX.pages.p21_fcs_slicer.main" in application_pages.PAGE_MODULES

    def test_page_module_registry_includes_fcs_merge_page(self) -> None:
        """Check page module registry includes FCS merge page."""
        assert "RosettaX.pages.p24_fcs_merge.main" in application_pages.PAGE_MODULES

    def test_page_module_registry_includes_citation_page(self) -> None:
        """Check page module registry includes citation page."""
        assert "RosettaX.pages.p20_citation.main" in application_pages.PAGE_MODULES

    def test_page_module_registry_includes_admin_page(self) -> None:
        """Check page module registry includes admin page."""
        assert "RosettaX.pages.p22_admin.main" in application_pages.PAGE_MODULES
