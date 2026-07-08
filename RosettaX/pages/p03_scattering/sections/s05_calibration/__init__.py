# -*- coding: utf-8 -*-

__all__ = ["Calibration"]


def __getattr__(name: str):
	if name == "Calibration":
		from .main import Calibration

		return Calibration

	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
