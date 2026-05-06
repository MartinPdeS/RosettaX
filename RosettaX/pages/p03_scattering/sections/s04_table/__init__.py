# -*- coding: utf-8 -*-

__all__ = ["ReferenceTable"]


def __getattr__(name: str):
	if name == "ReferenceTable":
		from .main import ReferenceTable

		return ReferenceTable

	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
