# -*- coding: utf-8 -*-

PAGE_NAME = "fluorescent_calibration"

from .sections.s01_upload.ids import UploadSectionIds
from .sections.s02_peaks.ids import PeakSectionIds
from .sections.s03_calibration.ids import CalibrationSectionIds
from .sections.s04_save.ids import SaveSectionIds


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