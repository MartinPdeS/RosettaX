# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

from dash import ALL


@dataclass(frozen=True)
class PeakSectionIds:
    """
    ID factory for the fluorescence peak section.

    This factory intentionally exposes the same script-facing API as the
    scattering peak section because the fluorescence section reuses the shared
    scripts from RosettaX.peak_script.

    The generated pattern IDs remain fluorescence scoped through their type
    strings, so fluorescence and scattering peak sections can coexist safely.
    """

    prefix: str

    detector_dropdown_type: str = "fluorescence-peak-script-detector-dropdown"
    controls_container_type: str = "fluorescence-peak-script-controls-container"
    action_button_type: str = "fluorescence-peak-script-action-button"
    setting_type: str = "fluorescence-peak-script-setting"
    status_type: str = "fluorescence-peak-script-status"

    @property
    def process_dropdown(self) -> str:
        return f"{self.prefix}-fluorescence-process-dropdown"

    @property
    def graph_toggle_switch(self) -> str:
        return f"{self.prefix}-fluorescence-graph-toggle-switch"

    @property
    def graph_toggle_container(self) -> str:
        return f"{self.prefix}-fluorescence-graph-toggle-container"

    @property
    def histogram_controls_container(self) -> str:
        return f"{self.prefix}-fluorescence-histogram-controls-container"

    @property
    def graph_hist(self) -> str:
        return f"{self.prefix}-fluorescence-histogram-graph"

    @property
    def yscale_switch(self) -> str:
        return f"{self.prefix}-fluorescence-yscale-switch"

    @property
    def xscale_switch(self) -> str:
        return f"{self.prefix}-fluorescence-xscale-switch"

    @property
    def nbins_input(self) -> str:
        return f"{self.prefix}-fluorescence-nbins-input"

    @property
    def peak_lines_store(self) -> str:
        return f"{self.prefix}-fluorescence-peak-lines-store"

    @property
    def source_channel_store(self) -> str:
        return f"{self.prefix}-fluorescence-source-channel-store"

    @property
    def hist_store(self) -> str:
        return f"{self.prefix}-fluorescence-histogram-store"

    @property
    def script_status(self) -> str:
        return f"{self.prefix}-fluorescence-peak-script-status-global"

    @property
    def peak_count_input(self) -> str:
        """
        Compatibility ID expected by older shared automatic 1D scripts.
        """
        return f"{self.prefix}-fluorescence-peak-count-input"

    @property
    def find_peaks_btn(self) -> str:
        """
        Compatibility ID expected by older shared automatic 1D scripts.
        """
        return f"{self.prefix}-fluorescence-find-peaks-button"

    @property
    def clear_manual_peaks_btn(self) -> str:
        """
        Compatibility ID expected by older shared manual 1D scripts.
        """
        return f"{self.prefix}-fluorescence-clear-manual-peaks-button"

    @property
    def clear_manual_2d_peaks_btn(self) -> str:
        """
        Compatibility ID expected by older shared manual 2D scripts.
        """
        return f"{self.prefix}-fluorescence-clear-manual-2d-peaks-button"

    @property
    def manual_click_status(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared manual 1D scripts.
        """
        return self.process_status(
            process_name="1D manual click",
        )

    @property
    def manual_2d_click_status(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared manual 2D scripts.
        """
        return self.process_status(
            process_name="2D manual click",
        )

    @property
    def automatic_peak_status(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared automatic scripts.
        """
        return self.process_status(
            process_name="1D automatic peak finding",
        )

    @property
    def manual_click_controls_container(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared manual 1D scripts.
        """
        return self.controls_container(
            process_name="1D manual click",
        )

    @property
    def manual_2d_click_controls_container(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared manual 2D scripts.
        """
        return self.controls_container(
            process_name="2D manual click",
        )

    @property
    def automatic_peak_controls_container(self) -> dict[str, Any]:
        """
        Compatibility ID expected by older shared automatic scripts.
        """
        return self.controls_container(
            process_name="1D automatic peak finding",
        )

    def detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.detector_dropdown_type,
            "process": process_name,
            "channel": channel_name,
        }

    def detector_dropdown_pattern(self) -> dict[str, Any]:
        return {
            "type": self.detector_dropdown_type,
            "process": ALL,
            "channel": ALL,
        }

    def controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.controls_container_type,
            "process": process_name,
        }

    def controls_container_pattern(self) -> dict[str, Any]:
        return {
            "type": self.controls_container_type,
            "process": ALL,
        }

    def action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.action_button_type,
            "process": process_name,
            "action": action_name,
        }

    def action_button_pattern(self) -> dict[str, Any]:
        return {
            "type": self.action_button_type,
            "process": ALL,
            "action": ALL,
        }

    def setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.setting_type,
            "process": process_name,
            "setting": setting_name,
        }

    def setting_pattern(self) -> dict[str, Any]:
        return {
            "type": self.setting_type,
            "process": ALL,
            "setting": ALL,
        }

    def status(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.status_type,
            "process": process_name,
        }

    def status_pattern(self) -> dict[str, Any]:
        return {
            "type": self.status_type,
            "process": ALL,
        }

    def peak_count_setting(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return self.setting(
            process_name=process_name,
            setting_name="peak_count",
        )

    def process_detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, Any]:
        """
        Compatibility method expected by shared peak scripts.
        """
        return self.detector_dropdown(
            process_name=process_name,
            channel_name=channel_name,
        )

    def process_detector_dropdown_pattern(self) -> dict[str, Any]:
        """
        Compatibility method matching the scattering peak section API.
        """
        return self.detector_dropdown_pattern()

    def process_controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        """
        Compatibility method expected by shared peak scripts.
        """
        return self.controls_container(
            process_name=process_name,
        )

    def process_controls_container_pattern(self) -> dict[str, Any]:
        """
        Compatibility method matching the scattering peak section API.
        """
        return self.controls_container_pattern()

    def process_action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, Any]:
        """
        Compatibility method expected by shared peak scripts.
        """
        return self.action_button(
            process_name=process_name,
            action_name=action_name,
        )

    def process_action_button_pattern(self) -> dict[str, Any]:
        """
        Compatibility method matching the scattering peak section API.
        """
        return self.action_button_pattern()

    def process_setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, Any]:
        """
        Compatibility method expected by shared peak scripts.
        """
        return self.setting(
            process_name=process_name,
            setting_name=setting_name,
        )

    def process_setting_pattern(self) -> dict[str, Any]:
        """
        Compatibility method matching the scattering peak section API.
        """
        return self.setting_pattern()

    def process_status(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        """
        Compatibility method expected by shared peak scripts.
        """
        return self.status(
            process_name=process_name,
        )

    def process_status_pattern(self) -> dict[str, Any]:
        """
        Compatibility method matching the scattering peak section API.
        """
        return self.status_pattern()