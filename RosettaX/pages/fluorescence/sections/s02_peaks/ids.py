# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

from dash import ALL


@dataclass(frozen=True)
class PeakSectionIds:
    """
    ID factory for the fluorescence peak section.

    The public method names intentionally match the scattering peak ID API
    because fluorescence and scattering use the same peak scripts.

    The pattern matching type values are fluorescence specific to avoid Dash
    callback collisions with the scattering page.
    """

    prefix: str

    detector_dropdown_type: str = "fluorescence-peak-script-detector-dropdown"
    controls_container_type: str = "fluorescence-peak-script-controls-container"
    action_button_type: str = "fluorescence-peak-script-action-button"
    status_type: str = "fluorescence-peak-script-status"
    setting_type: str = "fluorescence-peak-script-setting"

    @property
    def process_detector_dropdown_type(self) -> str:
        return self.detector_dropdown_type

    @property
    def process_action_button_type(self) -> str:
        return self.action_button_type

    @property
    def process_dropdown(self) -> str:
        return f"{self.prefix}-fluorescence-process-dropdown"

    @property
    def peak_count_input(self) -> str:
        return f"{self.prefix}-fluorescence-peak-count-input"

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

    def process_detector_dropdown(
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

    def process_detector_dropdown_pattern(self) -> dict[str, Any]:
        return {
            "type": self.detector_dropdown_type,
            "process": ALL,
            "channel": ALL,
        }

    def process_controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.controls_container_type,
            "process": process_name,
        }

    def process_controls_container_pattern(self) -> dict[str, Any]:
        return {
            "type": self.controls_container_type,
            "process": ALL,
        }

    def process_action_button(
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

    def process_action_button_pattern(self) -> dict[str, Any]:
        return {
            "type": self.action_button_type,
            "process": ALL,
            "action": ALL,
        }

    def process_setting(
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

    def process_setting_pattern(self) -> dict[str, Any]:
        return {
            "type": self.setting_type,
            "process": ALL,
            "setting": ALL,
        }

    def process_status(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return {
            "type": self.status_type,
            "process": process_name,
        }

    def process_status_pattern(self) -> dict[str, Any]:
        return {
            "type": self.status_type,
            "process": ALL,
        }

    def detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, Any]:
        return self.process_detector_dropdown(
            process_name=process_name,
            channel_name=channel_name,
        )

    def detector_dropdown_pattern(self) -> dict[str, Any]:
        return self.process_detector_dropdown_pattern()

    def controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return self.process_controls_container(
            process_name=process_name,
        )

    def controls_container_pattern(self) -> dict[str, Any]:
        return self.process_controls_container_pattern()

    def action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, Any]:
        return self.process_action_button(
            process_name=process_name,
            action_name=action_name,
        )

    def action_button_pattern(self) -> dict[str, Any]:
        return self.process_action_button_pattern()

    def setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, Any]:
        return self.process_setting(
            process_name=process_name,
            setting_name=setting_name,
        )

    def setting_pattern(self) -> dict[str, Any]:
        return self.process_setting_pattern()

    def status(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        return self.process_status(
            process_name=process_name,
        )

    def status_pattern(self) -> dict[str, Any]:
        return self.process_status_pattern()