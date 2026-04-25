# -*- coding: utf-8 -*-

from typing import Any


class PeakWorkflowIds:
    """
    Documentation interface for peak workflow ID factories.

    Existing page specific ID classes do not need to inherit this class, but
    they must expose the same methods and properties.
    """

    process_dropdown: str
    peak_count_input: str
    graph_toggle_switch: str
    graph_toggle_container: str
    histogram_controls_container: str
    graph_hist: str
    yscale_switch: str
    nbins_input: str

    detector_dropdown_type: str
    controls_container_type: str
    action_button_type: str
    status_type: str
    setting_type: str

    def process_detector_dropdown(
        self,
        *,
        process_name: str,
        channel_name: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def process_detector_dropdown_pattern(self) -> dict[str, Any]:
        raise NotImplementedError

    def process_controls_container(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def process_controls_container_pattern(self) -> dict[str, Any]:
        raise NotImplementedError

    def process_action_button(
        self,
        *,
        process_name: str,
        action_name: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def process_action_button_pattern(self) -> dict[str, Any]:
        raise NotImplementedError

    def process_setting(
        self,
        *,
        process_name: str,
        setting_name: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def process_setting_pattern(self) -> dict[str, Any]:
        raise NotImplementedError

    def process_status(
        self,
        *,
        process_name: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def process_status_pattern(self) -> dict[str, Any]:
        raise NotImplementedError