"""Table workflow package.

This facade stays lazy so pure table logic can be imported without requiring
Dash layout dependencies during test collection.
"""

from importlib import import_module
from typing import Any


__all__ = [
    "FluorescenceReferenceTable",
    "ReferenceTableConfig",
    "ReferenceTableLayout",
    "layout",
    "services",
]

_EXPORTS: dict[str, tuple[str, str | None]] = {
    "FluorescenceReferenceTable": (".fluorescence", "FluorescenceReferenceTable"),
    "ReferenceTableConfig": (".layout", "ReferenceTableConfig"),
    "ReferenceTableLayout": (".layout", "ReferenceTableLayout"),
    "layout": (".layout", None),
    "services": (".services", None),
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