# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

import dash


@dataclass(frozen=True)
class PeakSectionIds:
    """
    ID factory for the scattering peak detection section.

    Static IDs are strings.
    Dynamic IDs are dictionaries used by Dash pattern matching callbacks.

    The static detector_dropdown property is kept for compatibility with older
    sections that still expect page.ids.Scattering.detector_dropdown to be a
    string ID.
    """

    prefix: str

    process_detector_dropdown_type: str = "peak-script-detector-dropdown"
    process_controls_container_type: str = "peak-script-controls-container"
    process_action_button_type: str = "peak-script-action-button"
    process_status_type: str = "peak-script-status"
    process_setting_type: str = "peak-script-setting"

    @property
    def detector_dropdown(self) -> str:
        """
        Legacy static detector dropdown ID.

        Keep this because other sections still reference:
            page.ids.Scattering.detector_dropdown
        """
        return f"{self.prefix}-detector-dropdown"

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
    def nbins_control_container(self) -> str:
        return f"{self.prefix}-fluorescence-nbins-control-container"

    @property
    def nbins_input(self) -> str:
        return f"{self.prefix}-nbins-input"

    @property
    def graph_hist(self) -> str:
        return f"{self.prefix}-scattering-histogram-graph"

    @property
    def xscale_switch(self) -> str:
        return f"{self.prefix}-scattering-xscale-switch"

    @property
    def yscale_switch(self) -> str:
        return f"{self.prefix}-scattering-yscale-switch"

    @property
    def peak_count_input(self) -> str:
        return f"{self.prefix}-peak-count-input"

    @property
    def peak_lines_store(self) -> str:
        return f"{self.prefix}-peak-lines-store"

    def process_detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.process_detector_dropdown_type,
            "process": process_name,
            "channel": channel_name,
        }

    def process_detector_dropdown_pattern(self) -> dict[str, Any]:
        return {
            "type": self.process_detector_dropdown_type,
            "process": dash.ALL,
            "channel": dash.ALL,
        }

    def process_controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.process_controls_container_type,
            "process": process_name,
        }

    def process_controls_container_pattern(self) -> dict[str, Any]:
        return {
            "type": self.process_controls_container_type,
            "process": dash.ALL,
        }

    def process_action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.process_action_button_type,
            "process": process_name,
            "action": action_name,
        }

    def process_action_button_pattern(self) -> dict[str, Any]:
        return {
            "type": self.process_action_button_type,
            "process": dash.ALL,
            "action": dash.ALL,
        }

    def process_status(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.process_status_type,
            "process": process_name,
        }

    def process_status_pattern(self) -> dict[str, Any]:
        return {
            "type": self.process_status_type,
            "process": dash.ALL,
        }

    def process_setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, str]:
        return {
            "type": self.process_setting_type,
            "process": process_name,
            "setting": setting_name,
        }

    def process_setting_pattern(self) -> dict[str, Any]:
        return {
            "type": self.process_setting_type,
            "process": dash.ALL,
            "setting": dash.ALL,
        }