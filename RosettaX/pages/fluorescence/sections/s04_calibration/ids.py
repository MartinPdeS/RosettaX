# -*- coding: utf-8 -*-

from dataclasses import dataclass


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