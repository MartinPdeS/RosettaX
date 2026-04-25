# -*- coding: utf-8 -*-

PAGE_NAME = "fluorescent_calibration"

from RosettaX.pages.fluorescence.sections.s01_upload.ids import UploadSectionIds
from RosettaX.pages.fluorescence.sections.s02_gating.ids import GatingSectionIds
from RosettaX.pages.fluorescence.sections.s03_peaks.ids import PeakSectionIds
from RosettaX.pages.fluorescence.sections.s04_calibration.ids import CalibrationSectionIds
from RosettaX.pages.fluorescence.sections.s05_save.ids import SaveSectionIds


class Ids:
    """
    Centralized Dash ids for the fluorescence calibration page.

    Section ids remain grouped by section. Page level ids, such as the page
    state store, live directly under the State namespace.
    """

    page_name = PAGE_NAME

    class State:
        page_state_store = f"{PAGE_NAME}-page-state-store"

    Upload = UploadSectionIds(
        prefix=PAGE_NAME,
    )

    Scattering = GatingSectionIds(
        prefix=PAGE_NAME,
    )

    Fluorescence = PeakSectionIds(
        prefix=PAGE_NAME,
    )

    Calibration = CalibrationSectionIds(
        prefix=PAGE_NAME,
    )

    Save = SaveSectionIds(
        prefix=PAGE_NAME,
    )

    class Sidebar:
        sidebar_store = f"{PAGE_NAME}-sidebar-store"
        sidebar_content = f"{PAGE_NAME}-sidebar-content"