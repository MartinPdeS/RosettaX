# -*- coding: utf-8 -*-

from .main import Calibration


def build_section(*args, **kwargs) -> Calibration:
    """
    Build the scattering s05_calibration section instance.
    """
    return Calibration(*args, **kwargs)
