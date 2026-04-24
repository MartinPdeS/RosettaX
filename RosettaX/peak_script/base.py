# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, ClassVar, Optional
import logging

import dash

from RosettaX.utils import styling


logger = logging.getLogger(__name__)


PEAK_SCRIPT_DETECTOR_DROPDOWN_TYPE = "peak-script-detector-dropdown"
PEAK_SCRIPT_CONTROLS_CONTAINER_TYPE = "peak-script-controls-container"
PEAK_SCRIPT_ACTION_BUTTON_TYPE = "peak-script-action-button"
PEAK_SCRIPT_STATUS_TYPE = "peak-script-status"
PEAK_SCRIPT_SETTING_TYPE = "peak-script-setting"


@dataclass(frozen=True)
class PeakProcessResult:
    """
    Generic result returned by peak process actions.

    Attributes
    ----------
    peak_positions:
        Peak positions. A 1D process should return list[float]. A 2D process
        should return list[dict[str, float]] with keys x and y.

    peak_lines_payload:
        Payload stored in peak_lines_store and rendered by the graph builder.

    status:
        Human readable status string.
    """

    peak_positions: list[Any]
    peak_lines_payload: dict[str, list[Any]]
    status: str


class BasePeakProcess:
    """
    Base class for a peak detection or peak selection process.

    New process scripts should define one subclass and instantiate it as:

        PROCESS = MyProcess()
    """

    process_name: ClassVar[str] = ""
    process_label: ClassVar[str] = ""
    graph_type: ClassVar[str] = "1d_histogram"
    sort_order: ClassVar[int] = 100

    supports_manual_click: ClassVar[bool] = False
    supports_clear: ClassVar[bool] = False
    supports_automatic_action: ClassVar[bool] = False
    force_graph_visible: ClassVar[bool] = False

    def get_process_option(self) -> dict[str, str]:
        """
        Return the dropdown option for this process.
        """
        return {
            "label": self.get_label(),
            "value": self.process_name,
        }

    def get_label(self) -> str:
        """
        Return the display label for this process.
        """
        if self.process_label:
            return self.process_label

        return self.process_name

    def get_required_detector_channels(self) -> list[str]:
        """
        Return the detector channel names required by this process.
        """
        return ["primary"]

    def build_detector_dropdown_id(
        self,
        *,
        channel_name: str,
    ) -> dict[str, str]:
        """
        Build a pattern matching ID for a detector dropdown owned by this process.
        """
        return {
            "type": PEAK_SCRIPT_DETECTOR_DROPDOWN_TYPE,
            "process": self.process_name,
            "channel": channel_name,
        }

    def build_controls_container_id(self) -> dict[str, str]:
        """
        Build a pattern matching ID for this process control container.
        """
        return {
            "type": PEAK_SCRIPT_CONTROLS_CONTAINER_TYPE,
            "process": self.process_name,
        }

    def build_action_button_id(
        self,
        *,
        action_name: str,
    ) -> dict[str, str]:
        """
        Build a pattern matching ID for a process action button.
        """
        return {
            "type": PEAK_SCRIPT_ACTION_BUTTON_TYPE,
            "process": self.process_name,
            "action": action_name,
        }

    def build_status_id(self) -> dict[str, str]:
        """
        Build a pattern matching ID for this process status text.
        """
        return {
            "type": PEAK_SCRIPT_STATUS_TYPE,
            "process": self.process_name,
        }

    def build_setting_id(
        self,
        *,
        setting_name: str,
    ) -> dict[str, str]:
        """
        Build a pattern matching ID for a process owned setting component.
        """
        return {
            "type": PEAK_SCRIPT_SETTING_TYPE,
            "process": self.process_name,
            "setting": setting_name,
        }

    def build_visibility_style(
        self,
        *,
        selected_process_name: Any,
    ) -> dict[str, Any]:
        """
        Build the visibility style for this process control block.
        """
        if str(selected_process_name) == self.process_name:
            return styling.CARD

        return {"display": "none"}

    def should_force_graph_visible(
        self,
        *,
        selected_process_name: Any,
    ) -> bool:
        """
        Return True when this process requires the graph to be visible.
        """
        return bool(
            self.force_graph_visible
            and str(selected_process_name) == self.process_name
        )

    def build_status_component(self) -> dash.html.Div:
        """
        Build the status component for this process.
        """
        return dash.html.Div(
            id=self.build_status_id(),
            style={
                "marginLeft": "12px",
                "opacity": 0.8,
            },
        )

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build process specific controls.

        Subclasses must override this.
        """
        raise NotImplementedError

    def add_clicked_peak(
        self,
        *,
        click_data: Any,
        existing_peak_lines_payload: Any,
    ) -> Optional[PeakProcessResult]:
        """
        Handle a graph click.

        Manual click processes should override this.
        """
        logger.debug(
            "Process %r does not implement add_clicked_peak.",
            self.process_name,
        )
        return None

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear process owned peaks.

        Manual click processes should override this when supports_clear=True.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload={
                "positions": [],
                "labels": [],
                "x_positions": [],
                "y_positions": [],
                "points": [],
            },
            status="Cleared peaks.",
        )

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: int,
    ) -> Optional[PeakProcessResult]:
        """
        Run an automatic process action.

        Automatic processes should override this.
        """
        logger.debug(
            "Process %r does not implement run_automatic_action.",
            self.process_name,
        )
        return None