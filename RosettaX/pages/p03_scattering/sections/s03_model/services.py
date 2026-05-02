# -*- coding: utf-8 -*-

from .main import Model


def build_section(*args, **kwargs) -> Model:
    """
    Build the scattering s03_model section instance.
    """
    return Model(*args, **kwargs)
