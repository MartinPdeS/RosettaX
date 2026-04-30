# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, ClassVar, Optional
import logging

import numpy as np
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


def resolve_integer_value(
    *,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve a bounded integer value.
    """
    try:
        resolved_value = int(value)
    except (TypeError, ValueError):
        resolved_value = int(default)

    resolved_value = max(int(minimum), resolved_value)
    resolved_value = min(int(maximum), resolved_value)

    return resolved_value


def resolve_integer_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve an integer process setting.
    """
    return resolve_integer_value(
        value=settings.get(name),
        default=default,
        minimum=minimum,
        maximum=maximum,
    )


def resolve_float_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Resolve a bounded float process setting.
    """
    try:
        resolved_value = float(settings.get(name, default))
    except (TypeError, ValueError):
        resolved_value = float(default)

    if not np.isfinite(resolved_value):
        resolved_value = float(default)

    resolved_value = max(float(minimum), resolved_value)
    resolved_value = min(float(maximum), resolved_value)

    return resolved_value


def resolve_yes_no_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: bool,
) -> bool:
    """
    Resolve a yes or no setting.
    """
    value = settings.get(name, None)

    if value is None:
        return bool(default)

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in ("yes", "true", "1", "on", "enabled")


def deduplicate_1d_peak_positions(
    *,
    peak_positions: list[float],
    decimal_places: int = 12,
) -> list[float]:
    """
    Remove duplicate 1D peak positions while preserving order.
    """
    unique_peak_positions: list[float] = []
    seen_keys: set[float] = set()

    for peak_position in peak_positions:
        try:
            x_value = float(peak_position)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(x_value):
            continue

        key = round(x_value, int(decimal_places))

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_peak_positions.append(x_value)

    return unique_peak_positions


def deduplicate_2d_peak_positions(
    *,
    peak_positions: list[dict[str, float]],
    decimal_places: int = 12,
) -> list[dict[str, float]]:
    """
    Remove duplicate 2D peak positions while preserving order.
    """
    unique_peak_positions: list[dict[str, float]] = []
    seen_keys: set[tuple[float, float]] = set()

    for peak_position in peak_positions:
        try:
            x_value = float(peak_position["x"])
            y_value = float(peak_position["y"])
        except (KeyError, TypeError, ValueError):
            continue

        if not np.isfinite(x_value) or not np.isfinite(y_value):
            continue

        key = (round(x_value, int(decimal_places)), round(y_value, int(decimal_places)))

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_peak_positions.append({"x": x_value, "y": y_value})

    return unique_peak_positions