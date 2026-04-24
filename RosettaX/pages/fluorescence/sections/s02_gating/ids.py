# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass(frozen=True)
class GatingSectionIds:
    """
    ID factory for the fluorescence calibration scattering gating section.
    """

    prefix: str

    @property
    def detector_dropdown(self) -> str:
        return f"{self.prefix}-scattering-detector-dropdown"

    @property
    def debug_store(self) -> str:
        return f"{self.prefix}-scattering-debug-store"

    @property
    def debug_switch(self) -> str:
        return f"{self.prefix}-scattering-debug-switch"

    @property
    def debug_container(self) -> str:
        return f"{self.prefix}-scattering-debug-container"

    @property
    def find_threshold_btn(self) -> str:
        return f"{self.prefix}-scattering-find-threshold-button"

    @property
    def threshold_input(self) -> str:
        return f"{self.prefix}-scattering-threshold-input"

    @property
    def threshold_store(self) -> str:
        return f"{self.prefix}-scattering-threshold-store"

    @property
    def graph_hist(self) -> str:
        return f"{self.prefix}-scattering-histogram-graph"

    @property
    def yscale_switch(self) -> str:
        return f"{self.prefix}-scattering-yscale-switch"

    @property
    def nbins_input(self) -> str:
        return f"{self.prefix}-scattering-nbins-input"