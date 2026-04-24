# -*- coding: utf-8 -*-

"""
Compatibility facade for the scattering peak section.

The public API is intentionally re-exported here so main.py can keep using:

    from . import services

Implementation is split into focused modules to avoid a monolithic service file.
"""

from .services_common import *
from .services_processes import *
from .services_detectors import *
from .services_graphs import *
from .services_tables import *
from .services_actions import *