
from collections.abc import Iterable
from typing import Protocol


class _Section(Protocol):
    def register_callbacks(self) -> None: ...


def register_callbacks(sections: Iterable[_Section]) -> None:
    """
    Register callbacks for every fluorescence page section.
    """
    for section in sections:
        section.register_callbacks()
