# -*- coding: utf-8 -*-
from dataclasses import dataclass

PAGE_NAME = "fluorescent_calibration"

from RosettaX.workflow.upload.ids import UploadIds as UploadSectionIds
from RosettaX.workflow.save.ids import SaveIds as SaveSectionIds
from RosettaX.workflow.peak.ids import PeakIds


@dataclass(frozen=True)
class CalibrationSectionIds:
    """
    ID factory for the fluorescence calibration section.
    """

    prefix: str

    @property
    def collapse(self) -> str:
        return f"{self.prefix}-calibration-collapse"

    @property
    def graph_store(self) -> str:
        return f"{self.prefix}-calibration-graph-store"

    @property
    def calibration_store(self) -> str:
        return f"{self.prefix}-calibration-store"

    @property
    def bead_table(self) -> str:
        return f"{self.prefix}-calibration-bead-table"

    @property
    def add_row_btn(self) -> str:
        return f"{self.prefix}-calibration-add-row-button"

    @property
    def calibrate_btn(self) -> str:
        return f"{self.prefix}-calibration-create-button"

    @property
    def graph_calibration(self) -> str:
        return f"{self.prefix}-calibration-graph"

    @property
    def graph_toggle_container(self) -> str:
        return f"{self.prefix}-calibration-graph-container"

    @property
    def slope_out(self) -> str:
        return f"{self.prefix}-calibration-slope-output"

    @property
    def intercept_out(self) -> str:
        return f"{self.prefix}-calibration-intercept-output"

    @property
    def r_squared_out(self) -> str:
        return f"{self.prefix}-calibration-r-squared-output"

    @property
    def apply_status(self) -> str:
        return f"{self.prefix}-calibration-apply-status"

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