# -*- coding: utf-8 -*-

PAGE_NAME = "fluorescent_calibration"

from .sections.s03_calibration.ids import CalibrationSectionIds
from RosettaX.workflow.upload.ids import UploadIds as UploadSectionIds
from RosettaX.workflow.save.ids import SaveIds as SaveSectionIds
from RosettaX.workflow.peak.ids import PeakIds



class PeakSectionIds(PeakIds):
    """
    Fluorescence peak section IDs.
    """

    def __init__(
        self,
        *,
        prefix: str,
    ) -> None:
        super().__init__(
            prefix=prefix,
            namespace="fluorescence",
        )


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