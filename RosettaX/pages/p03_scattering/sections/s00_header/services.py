# -*- coding: utf-8 -*-

from .main import Header


def build_section(*args, **kwargs) -> Header:
    """
    Build the scattering s00_header section instance.
    """
    return Header(*args, **kwargs)
