# -*- coding: utf-8 -*-

from .main import Peaks


def build_section(*args, **kwargs) -> Peaks:
    """
    Build the scattering s02_peaks section instance.
    """
    return Peaks(*args, **kwargs)
