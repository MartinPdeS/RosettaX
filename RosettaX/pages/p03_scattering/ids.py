# -*- coding: utf-8 -*-

from dataclasses import dataclass

from RosettaX.workflow.upload.ids import UploadIds as UploadSectionIds
from RosettaX.workflow.save.ids import SaveIds as SaveSectionIds
from RosettaX.workflow.peak.ids import PeakIds

@dataclass(frozen=True)
class ParameterSectionIds:
    """
    ID factory for the scattering parameter section.
    """

    prefix: str

    @property
    def collapse_example(self) -> str:
        return f"{self.prefix}-parameters-collapse"

    @property
    def mie_model(self) -> str:
        return f"{self.prefix}-mie-model"

    @property
    def wavelength_nm(self) -> str:
        return f"{self.prefix}-wavelength-nm"

    @property
    def detector_configuration_preset(self) -> str:
        return f"{self.prefix}-detector-configuration-preset"

    @property
    def detector_configuration_preset_refresh_button(self) -> str:
        return f"{self.prefix}-detector-configuration-preset-refresh-button"

    @property
    def detector_configuration_custom_values_container(self) -> str:
        return f"{self.prefix}-detector-configuration-custom-values-container"

    @property
    def detector_numerical_aperture(self) -> str:
        return f"{self.prefix}-detector-numerical-aperture"

    @property
    def detector_cache_numerical_aperture(self) -> str:
        return f"{self.prefix}-detector-cache-numerical-aperture"

    @property
    def blocker_bar_numerical_aperture(self) -> str:
        return f"{self.prefix}-blocker-bar-numerical-aperture"

    @property
    def detector_sampling(self) -> str:
        return f"{self.prefix}-detector-sampling"

    @property
    def detector_phi_angle_degree(self) -> str:
        return f"{self.prefix}-detector-phi-angle-degree"

    @property
    def detector_gamma_angle_degree(self) -> str:
        return f"{self.prefix}-detector-gamma-angle-degree"

    @property
    def optical_configuration_preview(self) -> str:
        return f"{self.prefix}-optical-configuration-preview"

    @property
    def medium_refractive_index_source(self) -> str:
        return f"{self.prefix}-medium-refractive-index-source"

    @property
    def medium_refractive_index_custom(self) -> str:
        return f"{self.prefix}-medium-refractive-index-custom"

    @property
    def particle_refractive_index_source(self) -> str:
        return f"{self.prefix}-particle-refractive-index-source"

    @property
    def particle_refractive_index_custom(self) -> str:
        return f"{self.prefix}-particle-refractive-index-custom"

    @property
    def core_refractive_index_source(self) -> str:
        return f"{self.prefix}-core-refractive-index-source"

    @property
    def core_refractive_index_custom(self) -> str:
        return f"{self.prefix}-core-refractive-index-custom"

    @property
    def shell_refractive_index_source(self) -> str:
        return f"{self.prefix}-shell-refractive-index-source"

    @property
    def shell_refractive_index_custom(self) -> str:
        return f"{self.prefix}-shell-refractive-index-custom"

    @property
    def solid_sphere_container(self) -> str:
        return f"{self.prefix}-solid-sphere-container"

    @property
    def core_shell_container(self) -> str:
        return f"{self.prefix}-core-shell-container"


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

class PeakSectionIds(PeakIds):
    """
    Scattering peak section IDs.
    """

    def __init__(
        self,
        *,
        prefix: str,
    ) -> None:
        super().__init__(
            prefix=prefix,
            namespace="scattering",
        )


PAGE_NAME = "scattering_calibration"

class Ids:
    page_name = PAGE_NAME

    class State:
        page_state_store = f"{PAGE_NAME}-page-state-store"

    Upload = UploadSectionIds(
        prefix=PAGE_NAME,
    )

    Scattering = PeakSectionIds(
        prefix=PAGE_NAME,
    )

    Parameters = ParameterSectionIds(
        prefix=PAGE_NAME,
    )

    Calibration = CalibrationSectionIds(
        prefix=PAGE_NAME,
    )

    Save = SaveSectionIds(
        prefix=PAGE_NAME,
    )