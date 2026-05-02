# -*- coding: utf-8 -*-

from .main import Save


def build_section(*args, **kwargs) -> Save:
    """
    Build the scattering s06_save section instance.
    """
    return Save(*args, **kwargs)
