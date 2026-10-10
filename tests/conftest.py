"""Dependency setup for the stubbed unit-test suite."""


import sys
import types


class _DashBootstrapComponent:
    """Component arguments and attributes exposed by the Bootstrap test double."""
    def __init__(self, *args, **kwargs):
        """Initialize the state required by this test double."""
        self.children = kwargs.pop("children", None)
        if self.children is None and args:
            self.children = args[0] if len(args) == 1 else list(args)

        self.args = args
        self.kwargs = dict(kwargs)
        self.id = kwargs.get("id")
        self.href = kwargs.get("href")
        self.style = kwargs.get("style")
        self.color = kwargs.get("color")


class _DashBootstrapComponentsStub(types.ModuleType):
    """Minimal Dash Bootstrap components used by the unit tests."""
    themes = types.SimpleNamespace(
        FLATLY="FLATLY",
        SLATE="SLATE",
    )

    def __init__(self, name):
        """Initialize the state required by this test double."""
        super().__init__(name)
        self._component_types = {}

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        component_type = self._component_types.get(name)
        if component_type is None:
            component_type = type(name, (_DashBootstrapComponent,), {})
            self._component_types[name] = component_type
        return component_type


class _PyMieSimStub(types.ModuleType):
    """Minimal PyMieSim module used by the unit tests."""
    experiment = types.SimpleNamespace()


class _PyMieSimUnitsStub(types.ModuleType):
    """Minimal PyMieSim units module used by the unit tests."""
    ureg = types.SimpleNamespace()


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)
sys.modules.setdefault(
    "PyMieSim",
    _PyMieSimStub("PyMieSim"),
)
sys.modules.setdefault(
    "PyMieSim.units",
    _PyMieSimUnitsStub("PyMieSim.units"),
)
