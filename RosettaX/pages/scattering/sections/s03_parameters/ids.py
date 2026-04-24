# -*- coding: utf-8 -*-

from dataclasses import dataclass


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