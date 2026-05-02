# -*- coding: utf-8 -*-

from typing import Iterable, Protocol


class _Section(Protocol):
    def register_callbacks(self) -> None: ...


def register_callbacks(sections: Iterable[_Section]) -> None:
    """
    Register callbacks for every apply calibration page section.
    """
    for section in sections:
        section.register_callbacks()
