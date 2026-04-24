# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Optional
import logging

import dash

from RosettaX.utils import styling


logger = logging.getLogger(__name__)


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

    def build_status_component(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build the status component for this process.
        """
        return dash.html.Div(
            id=ids.process_status(
                process_name=self.process_name,
            ),
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