# -*- coding: utf-8 -*-

from .main import ReferenceTable


def build_section(*args, **kwargs) -> ReferenceTable:
    """
    Build the scattering s04_table section instance.
    """
    return ReferenceTable(*args, **kwargs)
