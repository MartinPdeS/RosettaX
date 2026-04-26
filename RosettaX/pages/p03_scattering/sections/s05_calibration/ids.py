# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationSectionIds:
    """
    ID factory for the scattering calibration section.

    This keeps all calibration related component IDs centralized.

    Some IDs are used outside this section:
    - bead_table is rendered in the parameter section
    - add_row_btn is rendered in the parameter section
    - compute_model_btn is rendered in the parameter section

    They remain here because they are calibration table actions and are already
    referenced through page.ids.Calibration.
    """

    prefix: str

    @property
    def graph_store(self) -> str:
        return f"{self.prefix}-calibration-graph-store"

    @property
    def model_graph_store(self) -> str:
        return f"{self.prefix}-calibration-model-graph-store"

    @property
    def calibration_store(self) -> str:
        return f"{self.prefix}-calibration-store"

    @property
    def calibrate_btn(self) -> str:
        return f"{self.prefix}-fit-calibration-button"

    @property
    def graph_calibration(self) -> str:
        return f"{self.prefix}-calibration-graph"

    @property
    def graph_model(self) -> str:
        return f"{self.prefix}-calibration-model-graph"

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

    @property
    def bead_table(self) -> str:
        return f"{self.prefix}-calibration-reference-table"

    @property
    def add_row_btn(self) -> str:
        return f"{self.prefix}-calibration-reference-table-add-row-button"

    @property
    def compute_model_btn(self) -> str:
        return f"{self.prefix}-calibration-reference-table-compute-model-button"