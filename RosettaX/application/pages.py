# -*- coding: utf-8 -*-

import importlib
import logging


logger = logging.getLogger(__name__)


PAGE_MODULES: list[str] = [
    "RosettaX.pages.p01_home.main",
    "RosettaX.pages.p02_fluorescence.main",
    "RosettaX.pages.p03_scattering.main",
    "RosettaX.pages.p04_calibrate.main",
    "RosettaX.pages.p05_settings.main",
    "RosettaX.pages.p06_help.main",
]


def register_pages() -> None:
    """
    Import all Dash page modules after Dash app instantiation.

    The calibration JSON viewer is intentionally not a Dash page.
    It is served through a Flask route so opening a calibration record does not
    disturb the current Dash route or theme state.
    """
    logger.debug("Registering page modules")

    for page_module_name in PAGE_MODULES:
        try:
            logger.debug("Importing page module=%r", page_module_name)
            importlib.import_module(page_module_name)
            logger.debug("Successfully imported page module=%r", page_module_name)
        except Exception:
            logger.exception("Failed to import page module=%r", page_module_name)
            raise