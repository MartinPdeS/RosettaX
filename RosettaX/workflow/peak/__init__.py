# -*- coding: utf-8 -*-

"""Peak workflow package.

Keep this facade lazy so importing the package does not eagerly load Dash UI
modules during logic-only test collection.
"""

from importlib import import_module
from typing import Any


__all__ = [
    "FluorescencePeakWorkflowAdapter",
    "PeakConfig",
    "PeakIds",
    "PeakLayout",
    "ScatteringPeakWorkflowAdapter",
    "register_peak_callbacks",
    "registry",
]

_EXPORTS: dict[str, tuple[str, str | None]] = {
    "FluorescencePeakWorkflowAdapter": (".adapters.fluorescence", "FluorescencePeakWorkflowAdapter"),
    "PeakConfig": (".models", "PeakConfig"),
    "PeakIds": (".ids", "PeakIds"),
    "PeakLayout": (".layout", "PeakLayout"),
    "ScatteringPeakWorkflowAdapter": (".adapters.scattering", "ScatteringPeakWorkflowAdapter"),
    "register_peak_callbacks": (".callbacks.main", "register_peak_callbacks"),
    "registry": (".registry", None),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    value = module if attribute_name is None else getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))