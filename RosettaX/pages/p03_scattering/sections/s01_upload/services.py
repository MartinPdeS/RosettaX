# -*- coding: utf-8 -*-

from .main import Upload


def build_section(*args, **kwargs) -> Upload:
    """
    Build the scattering s01_upload section instance.
    """
    return Upload(*args, **kwargs)
