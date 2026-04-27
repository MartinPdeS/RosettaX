# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationSectionIds:
    """
    ID factory for the scattering calibration section.

    This keeps all calibration related component IDs centralized.

    Some IDs are used outside the instrument response fit section:
    - bead_table is rendered in the calibration standard table section.
    - add_row_btn is rendered in the calibration standard table section.
    - compute_model_btn is rendered in the calibration standard table section.

    They remain here because they are calibration standard table actions and are
    already referenced through page.ids.Calibration.
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
        return f"{self.prefix}-fit-instrument-response-button"

    @property
    def graph_calibration(self) -> str:
        return f"{self.prefix}-instrument-response-graph"

    @property
    def graph_model(self) -> str:
        return f"{self.prefix}-calibration-standard-mie-relation-graph"

    @property
    def instrument_response_x_log_switch(self) -> str:
        return f"{self.prefix}-instrument-response-x-log-switch"

    @property
    def instrument_response_y_log_switch(self) -> str:
        return f"{self.prefix}-instrument-response-y-log-switch"

    @property
    def mie_relation_x_log_switch(self) -> str:
        return f"{self.prefix}-mie-relation-x-log-switch"

    @property
    def mie_relation_y_log_switch(self) -> str:
        return f"{self.prefix}-mie-relation-y-log-switch"

    @property
    def slope_out(self) -> str:
        return f"{self.prefix}-instrument-response-gain-output"

    @property
    def intercept_out(self) -> str:
        return f"{self.prefix}-instrument-response-offset-output"

    @property
    def r_squared_out(self) -> str:
        return f"{self.prefix}-instrument-response-r-squared-output"

    @property
    def apply_status(self) -> str:
        return f"{self.prefix}-instrument-response-apply-status"

    @property
    def bead_table(self) -> str:
        return f"{self.prefix}-calibration-standard-table"

    @property
    def add_row_btn(self) -> str:
        return f"{self.prefix}-calibration-standard-table-add-row-button"

    @property
    def compute_model_btn(self) -> str:
        return f"{self.prefix}-calibration-standard-table-compute-model-button"