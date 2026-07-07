# -*- coding: utf-8 -*-

import importlib
import logging


logger = logging.getLogger(__name__)


PAGE_MODULES: list[str] = [
    "RosettaX.pages.p01_home.main",
    "RosettaX.pages.p02_fluorescence.main",
    "RosettaX.pages.p03_scattering.main",
    "RosettaX.pages.p08_cross_calibration.main",
    "RosettaX.pages.p04_calibrate.main",
    "RosettaX.pages.p05_settings.main",
    "RosettaX.pages.p06_help.main",
    "RosettaX.pages.p09_sample_files.main",
    "RosettaX.pages.p07_documentation.main",
    "RosettaX.pages.p10_visualization.main",
    "RosettaX.pages.p11_docs_peak_scripts.main",
    "RosettaX.pages.p12_docs_supported_cytometers.main",
    "RosettaX.pages.p13_docs_regression_models.main",
    "RosettaX.pages.p14_docs_reports.main",
    "RosettaX.pages.p15_docs_system_model.main",
    "RosettaX.pages.p16_docs_refractive_index.main",
    "RosettaX.pages.p17_docs_calibration_payload.main",
    "RosettaX.pages.p18_docs_apply_checks.main",
    "RosettaX.pages.p19_docs_install_local.main",
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
