"""Settings sections package.

Keep this facade lazy so service-level imports do not pull Dash UI modules
during test collection.
"""

from importlib import import_module
from typing import Any


__all__ = [
	"CreateProfile",
	"DefaultProfile",
	"DeleteProfile",
]

_EXPORTS: dict[str, tuple[str, str]] = {
	"CreateProfile": (".s02_create.main", "CreateProfile"),
	"DefaultProfile": (".s01_default.main", "DefaultProfile"),
	"DeleteProfile": (".s03_delete.main", "DeleteProfile"),
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