"""Real-dependency checks run separately from the stubbed unit suite."""

import importlib
from pathlib import Path

import pytest


def pytest_sessionstart(session):
    for name in ("PyMieSim", "PyMieSim.units", "dash_bootstrap_components"):
        module = importlib.import_module(name)
        if not getattr(module, "__file__", None) or module.__spec__ is None:
            raise pytest.UsageError(
                f"{name} is stubbed. Run integration_tests in a separate pytest process."
            )


def pytest_collection_modifyitems(items):
    integration_directory = Path(__file__).resolve().parent
    if any(integration_directory not in Path(item.path).resolve().parents for item in items):
        raise pytest.UsageError(
            "Run integration_tests separately; mixing suites can contaminate dependencies with stubs."
        )


@pytest.fixture(scope="session")
def application():
    from RosettaX.application.main import RosettaXApplication

    return RosettaXApplication(
        host="127.0.0.1", port=8050, open_browser=False, debug=False,
    ).app
