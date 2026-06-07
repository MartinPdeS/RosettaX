# -*- coding: utf-8 -*-

"""Save workflow package.

Keep this facade lazy so importing the package does not eagerly load Dash UI
modules during logic-only test collection.
"""

from importlib import import_module
from typing import Any


__all__ = [
    "CalibrationStoreSaveAdapter",
    "PageStateSaveAdapter",
    "SaveAdapter",
    "SaveConfig",
    "SaveInputs",
    "SaveLayout",
    "SaveResult",
    "register_save_callbacks",
]

_EXPORTS: dict[str, tuple[str, str]] = {
    "CalibrationStoreSaveAdapter": (".adapters", "CalibrationStoreSaveAdapter"),
    "PageStateSaveAdapter": (".adapters", "PageStateSaveAdapter"),
    "SaveAdapter": (".adapters", "SaveAdapter"),
    "SaveConfig": (".models", "SaveConfig"),
    "SaveInputs": (".models", "SaveInputs"),
    "SaveLayout": (".layout", "SaveLayout"),
    "SaveResult": (".models", "SaveResult"),
    "register_save_callbacks": (".callbacks", "register_save_callbacks"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))