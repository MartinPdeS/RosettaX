# -*- coding: utf-8 -*-

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
        Cumulative peak positions used for graph annotations.

        A 1D process should return ``list[float]``.
        A 2D process may return ``list[dict[str, float]]`` with keys such as
        ``x`` and ``y``.

    peak_lines_payload:
        Serializable payload stored in page state and rendered by the graph
        builder.

    status:
        Human readable status string.

    new_peak_positions:
        Delta peak positions produced by the current action only.

        Manual click processes should use this for the newly clicked point.
        Automatic processes may use this for newly detected peaks.
        Table update logic must use this field instead of inferring changes from
        the cumulative ``peak_positions`` or ``peak_lines_payload``.

    clear_existing_table_peaks:
        Whether downstream table update logic should clear the measured peak
        column before applying the current result.
    """

    peak_positions: list[Any]
    peak_lines_payload: dict[str, Any]
    status: str
    new_peak_positions: Optional[list[Any]] = None
    clear_existing_table_peaks: bool = False


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

        Returns
        -------
        dict[str, str]
            Dash dropdown option.
        """
        return {
            "label": self.get_label(),
            "value": self.process_name,
        }

    def get_label(self) -> str:
        """
        Return the display label for this process.

        Returns
        -------
        str
            Display label.
        """
        if self.process_label:
            return self.process_label

        return self.process_name

    def get_required_detector_channels(self) -> list[str]:
        """
        Return the detector channel names required by this process.

        Returns
        -------
        list[str]
            Required detector channel names.
        """
        return [
            "primary",
        ]

    def build_visibility_style(
        self,
        *,
        selected_process_name: Any,
    ) -> dict[str, Any]:
        """
        Build the visibility style for this process control block.

        Parameters
        ----------
        selected_process_name:
            Currently selected process name.

        Returns
        -------
        dict[str, Any]
            CSS style dictionary.
        """
        if str(selected_process_name) == self.process_name:
            return styling.CARD

        return {
            "display": "none",
        }

    def should_force_graph_visible(
        self,
        *,
        selected_process_name: Any,
    ) -> bool:
        """
        Return whether this process requires the graph to be visible.

        Parameters
        ----------
        selected_process_name:
            Currently selected process name.

        Returns
        -------
        bool
            True if the graph should be forced visible.
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

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Status component.
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

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Process controls.

        Raises
        ------
        NotImplementedError
            Always raised by the base class.
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

        Parameters
        ----------
        click_data:
            Plotly clickData payload.

        existing_peak_lines_payload:
            Existing cumulative peak annotation payload.

        Returns
        -------
        Optional[PeakProcessResult]
            Peak process result, or None.
        """
        logger.debug(
            "Process %r does not implement add_clicked_peak.",
            self.process_name,
        )

        return None

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear process owned peaks.

        Manual click processes should override this when ``supports_clear=True``.

        Returns
        -------
        PeakProcessResult
            Empty peak result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
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

        Parameters
        ----------
        backend:
            Backend compatible with the selected process.

        detector_channels:
            Mapping from process channel name to selected detector column.

        peak_count:
            Requested peak count.

        max_events_for_analysis:
            Maximum number of events used for the analysis.

        Returns
        -------
        Optional[PeakProcessResult]
            Peak process result, or None.
        """
        logger.debug(
            "Process %r does not implement run_automatic_action.",
            self.process_name,
        )

        return None

    def build_empty_peak_lines_payload(self) -> dict[str, list[Any]]:
        """
        Build an empty peak annotation payload.

        Returns
        -------
        dict[str, list[Any]]
            Empty peak annotation payload.
        """
        return {
            "positions": [],
            "labels": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }