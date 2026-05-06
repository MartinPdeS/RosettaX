# -*- coding: utf-8 -*-

__all__ = ["Model"]


def __getattr__(name: str):
	if name == "Model":
		from .main import Model

		return Model

	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
