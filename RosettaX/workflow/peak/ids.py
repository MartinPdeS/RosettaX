# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any

import dash


@dataclass(frozen=True)
class PeakIds:
    """
    Shared ID factory for reusable peak sections.

    The string IDs are made page specific through the prefix.

    The pattern matching IDs use a namespace because Dash pattern IDs do not
    include the page prefix unless we explicitly add it to the type string.
    """

    prefix: str
    namespace: str | None = None

    @property
    def resolved_namespace(self) -> str:
        """
        Resolve the namespace used in pattern matching type strings.
        """
        if self.namespace:
            return str(self.namespace)

        prefix_lower = str(self.prefix).lower()

        if "fluores" in prefix_lower:
            return "fluorescence"

        if "scatter" in prefix_lower:
            return "scattering"

        return str(self.prefix)

    @property
    def process_detector_dropdown_type(self) -> str:
        return f"{self.resolved_namespace}-peak-script-detector-dropdown"

    @property
    def process_controls_container_type(self) -> str:
        return f"{self.resolved_namespace}-peak-script-controls-container"

    @property
    def process_action_button_type(self) -> str:
        return f"{self.resolved_namespace}-peak-script-action-button"

    @property
    def process_status_type(self) -> str:
        return f"{self.resolved_namespace}-peak-script-status"

    @property
    def process_setting_type(self) -> str:
        return f"{self.resolved_namespace}-peak-script-setting"

    @property
    def detector_dropdown_type(self) -> str:
        return self.process_detector_dropdown_type

    @property
    def controls_container_type(self) -> str:
        return self.process_controls_container_type

    @property
    def action_button_type(self) -> str:
        return self.process_action_button_type

    @property
    def status_type(self) -> str:
        return self.process_status_type

    @property
    def setting_type(self) -> str:
        return self.process_setting_type

    @property
    def detector_dropdown(self) -> str:
        """
        Legacy static detector dropdown ID.
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
        return f"{self.prefix}-nbins-control-container"

    @property
    def nbins_input(self) -> str:
        return f"{self.prefix}-nbins-input"

    @property
    def graph_hist(self) -> str:
        return f"{self.prefix}-histogram-graph"

    @property
    def hist_store(self) -> str:
        return f"{self.prefix}-histogram-store"

    @property
    def source_channel_store(self) -> str:
        return f"{self.prefix}-source-channel-store"

    @property
    def script_status(self) -> str:
        return f"{self.prefix}-peak-script-status-global"

    @property
    def xscale_switch(self) -> str:
        return f"{self.prefix}-xscale-switch"

    @property
    def yscale_switch(self) -> str:
        return f"{self.prefix}-yscale-switch"

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

    def detector_dropdown_pattern(self) -> dict[str, Any]:
        return self.process_detector_dropdown_pattern()

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

    def controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return self.process_controls_container(
            process_name=process_name,
        )

    def controls_container_pattern(self) -> dict[str, Any]:
        return self.process_controls_container_pattern()

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

    def action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, str]:
        return self.process_action_button(
            process_name=process_name,
            action_name=action_name,
        )

    def action_button_pattern(self) -> dict[str, Any]:
        return self.process_action_button_pattern()

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

    def status(
        self,
        *,
        process_name: str,
    ) -> dict[str, str]:
        return self.process_status(
            process_name=process_name,
        )

    def status_pattern(self) -> dict[str, Any]:
        return self.process_status_pattern()

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

    def setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, str]:
        return self.process_setting(
            process_name=process_name,
            setting_name=setting_name,
        )

    def setting_pattern(self) -> dict[str, Any]:
        return self.process_setting_pattern()