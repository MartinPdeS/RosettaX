# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

import dash


@dataclass(frozen=True)
class PeakSectionIds:
    """
    ID factory for the scattering peak detection section.

    Static IDs are strings.
    Dynamic IDs are dicts used by Dash pattern matching callbacks.
    """

    prefix: str

    detector_dropdown_type: str = "peak-script-detector-dropdown"
    controls_container_type: str = "peak-script-controls-container"
    action_button_type: str = "peak-script-action-button"
    status_type: str = "peak-script-status"
    setting_type: str = "peak-script-setting"

    @property
    def process_dropdown(self) -> str:
        return f"{self.prefix}-process-dropdown"

    @property
    def graph_toggle_switch(self) -> str:
        return f"{self.prefix}-graph-toggle-switch"

    @property
    def graph_toggle_container(self) -> str:
        return f"{self.prefix}-graph-toggle-container"

    @property
    def histogram_controls_container(self) -> str:
        return f"{self.prefix}-histogram-controls-container"

    @property
    def graph_hist(self) -> str:
        return f"{self.prefix}-graph-hist"

    @property
    def nbins_input(self) -> str:
        return f"{self.prefix}-nbins-input"

    @property
    def yscale_switch(self) -> str:
        return f"{self.prefix}-yscale-switch"

    @property
    def peak_count_input(self) -> str:
        return f"{self.prefix}-peak-count-input"

    @property
    def peak_lines_store(self) -> str:
        return f"{self.prefix}-peak-lines-store"

    def detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.detector_dropdown_type,
            "process": process_name,
            "channel": channel_name,
        }

    def detector_dropdown_pattern(self) -> dict[str, Any]:
        return {
            "type": self.detector_dropdown_type,
            "process": dash.ALL,
            "channel": dash.ALL,
        }

    def controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.controls_container_type,
            "process": process_name,
        }

    def controls_container_pattern(self) -> dict[str, Any]:
        return {
            "type": self.controls_container_type,
            "process": dash.ALL,
        }

    def action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.action_button_type,
            "process": process_name,
            "action": action_name,
        }

    def action_button_pattern(self) -> dict[str, Any]:
        return {
            "type": self.action_button_type,
            "process": dash.ALL,
            "action": dash.ALL,
        }

    def status(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.status_type,
            "process": process_name,
        }

    def status_pattern(self) -> dict[str, Any]:
        return {
            "type": self.status_type,
            "process": dash.ALL,
        }

    def setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.setting_type,
            "process": process_name,
            "setting": setting_name,
        }

    def setting_pattern(self) -> dict[str, Any]:
        return {
            "type": self.setting_type,
            "process": dash.ALL,
            "setting": dash.ALL,
        }