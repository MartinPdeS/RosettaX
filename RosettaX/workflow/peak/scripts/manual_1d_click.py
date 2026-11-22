
import logging
import numpy as np
from ..core.process_calls import standard_peak_action
from ._events import filter_finite_peak_events, read_peak_event_columns
from ._manual_controls import ManualPeakControls
from ._manual_selection import read_clicked_position, read_selected_ranges
from .base import (
    BasePeakProcess,
    PeakProcessResult,
    filter_edge_artifact_values,
    resolve_edge_artifact_filter_enabled,
)
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from typing import Any

logger = logging.getLogger(__name__)


class Manual1DClickProcess(ManualPeakControls, BasePeakProcess):
    """
    Manual 1D peak picking process.

    The user selects one detector channel, then clicks the 1D histogram to add
    peak positions.

    The graph receives the cumulative list of picked peaks. The calibration
    table receives only the current click delta through new_peak_positions.
    """

    process_name = "Manual 1D"
    process_label = "Manual 1D"
    description = "Click the one-dimensional signal graph to add calibration peak positions."
    graph_type = "1d_histogram"
    sort_order = 10

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    detector_controls = (("primary", "Detector channel", "Select detector channel"),)
    dropdown_option_height_px = 50
    dropdown_menu_max_height_px = 500

    @standard_peak_action
    def add_clicked_peak(
        self,
        *,
        click_data: Any,
        selected_data: Any = None,
        existing_peak_lines_payload: Any,
        backend: Any = None,
        detector_channels: dict[str, Any] | None = None,
        process_settings: dict[str, Any] | None = None,
        runtime_config_data: Any = None,
        axis_scale_toggle_values: Any = None,
    ) -> PeakProcessResult | None:
        """
        Add one clicked peak to the cumulative peak payload.

        Parameters
        ----------
        click_data:
            Plotly clickData payload.

        existing_peak_lines_payload:
            Existing cumulative peak annotation payload.

        Returns
        -------
        Optional[PeakProcessResult]
            Peak process result, or None if the click is invalid.
        """
        clicked_peak_position = self.extract_clicked_x_position(click_data)
        selected_x_range = self.extract_selected_x_range(selected_data)

        if clicked_peak_position is None and selected_x_range is None:
            logger.debug(
                "Manual 1D click received no valid click or selection. click_data=%r selected_data=%r",
                click_data,
                selected_data,
            )
            return None

        reference_peak_position = (
            float(clicked_peak_position)
            if clicked_peak_position is not None
            else float(
                0.5 * (
                    selected_x_range[0] + selected_x_range[1]
                )
            )
        )

        snapped_peak_position = reference_peak_position
        snap_was_applied = False

        if self._snap_to_local_mode_is_enabled(
            process_settings=process_settings,
        ):
            resolved_peak_position = self.snap_clicked_peak_position(
                backend=backend,
                detector_channels=detector_channels,
                clicked_peak_position=reference_peak_position,
                selected_x_range=selected_x_range,
                process_settings=process_settings,
                runtime_config_data=runtime_config_data,
                axis_scale_toggle_values=axis_scale_toggle_values,
            )

            if resolved_peak_position is not None and np.isfinite(resolved_peak_position):
                snapped_peak_position = float(resolved_peak_position)
                snap_was_applied = not np.isclose(
                    snapped_peak_position,
                    reference_peak_position,
                    rtol=1e-6,
                    atol=0.0,
                )

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload,
        )

        for existing_peak_position in existing_peak_positions:
            if np.isclose(
                existing_peak_position,
                snapped_peak_position,
                rtol=1e-9,
                atol=0.0,
            ):
                return PeakProcessResult(
                    peak_positions=existing_peak_positions,
                    peak_lines_payload=self.build_peak_lines_payload(
                        peak_positions=existing_peak_positions,
                    ),
                    status=(
                        f"Peak at {snapped_peak_position:.6g} is already selected."
                    ),
                    new_peak_positions=[],
                    clear_existing_table_peaks=False,
                )

        next_peak_positions = sorted(
            [
                *existing_peak_positions,
                snapped_peak_position,
            ]
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        if snap_was_applied:
            status = (
                f"Added peak at {snapped_peak_position:.6g} "
                f"(selected around {reference_peak_position:.6g}). "
                f"{len(next_peak_positions)} peak(s) selected."
            )
        else:
            status = (
                f"Added peak at {snapped_peak_position:.6g}. "
                f"{len(next_peak_positions)} peak(s) selected."
            )

        logger.debug(
            "Manual 1D click added clicked_peak_position=%r "
            "existing_peak_positions=%r next_peak_positions=%r "
            "peak_lines_payload=%r",
            snapped_peak_position,
            existing_peak_positions,
            next_peak_positions,
            peak_lines_payload,
        )

        return PeakProcessResult(
            peak_positions=next_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=[
                snapped_peak_position,
            ],
            clear_existing_table_peaks=False,
        )

    def _x_axis_is_log(
        self,
        *,
        axis_scale_toggle_values: Any,
        clicked_peak_position: float,
    ) -> bool:
        """
        Return whether the 1D histogram x axis is currently log scaled.
        """
        if clicked_peak_position <= 0.0:
            return False

        if isinstance(axis_scale_toggle_values, str):
            return axis_scale_toggle_values in (
                "log",
                Scatter2DGraph.x_log_value,
            )

        if isinstance(axis_scale_toggle_values, (list, tuple, set)):
            return (
                "log" in axis_scale_toggle_values
                or Scatter2DGraph.x_log_value in axis_scale_toggle_values
            )

        return False

    def snap_clicked_peak_position(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any] | None,
        clicked_peak_position: float,
        selected_x_range: tuple[float, float] | None,
        process_settings: dict[str, Any] | None,
        runtime_config_data: Any,
        axis_scale_toggle_values: Any,
    ) -> float | None:
        """
        Snap one clicked position to the local modal value nearby.
        """
        if backend is None or not hasattr(backend, "fcs_file_path"):
            return None

        detector_column = (
            detector_channels or {}
        ).get("primary")

        if not str(detector_column or "").strip():
            return None

        max_events, histogram_bins = self._resolve_snap_settings(runtime_config_data=runtime_config_data)
        (values,) = read_peak_event_columns(
            fcs_file_path=backend.fcs_file_path, detector_columns=(detector_column,),
            max_events=max_events, read_column=column_copy,
        )
        if resolve_edge_artifact_filter_enabled(
            process_settings=process_settings,
            default=True,
        ):
            values = filter_edge_artifact_values(
                values=values,
                remove_min=True,
                remove_max=True,
            )
        else:
            (values,), _ = filter_finite_peak_events(columns=(values,))

        if values.size < 8:
            return None

        use_log_x = self._x_axis_is_log(
            axis_scale_toggle_values=axis_scale_toggle_values,
            clicked_peak_position=clicked_peak_position,
        )

        if use_log_x:
            values = values[
                values > 0.0
            ]

            if values.size < 8 or clicked_peak_position <= 0.0:
                return None

            histogram_edges = np.geomspace(
                float(np.min(values)),
                float(
                    max(
                        np.max(values),
                        np.min(values) * 1.01,
                    )
                ),
                num=histogram_bins + 1,
            )
            histogram_counts, histogram_edges = np.histogram(
                values,
                bins=histogram_edges,
            )
            histogram_centers = np.sqrt(
                histogram_edges[:-1] * histogram_edges[1:]
            )
        else:
            histogram_counts, histogram_edges = np.histogram(
                values,
                bins=histogram_bins,
            )
            histogram_centers = 0.5 * (
                histogram_edges[:-1] + histogram_edges[1:]
            )

        histogram_counts = np.asarray(histogram_counts, dtype=float)
        histogram_edges = np.asarray(histogram_edges, dtype=float)
        histogram_centers = np.asarray(histogram_centers, dtype=float)

        if selected_x_range is not None:
            snapped_peak_position = self._find_histogram_peak_in_selected_range(
                counts=histogram_counts,
                centers=histogram_centers,
                selected_x_range=selected_x_range,
                fallback_value=float(clicked_peak_position),
            )
        else:
            snapped_peak_position = self._climb_histogram_peak_1d(
                counts=histogram_counts,
                edges=histogram_edges,
                centers=histogram_centers,
                clicked_value=float(clicked_peak_position),
            )

        if snapped_peak_position is None or not np.isfinite(snapped_peak_position):
            return None

        return float(snapped_peak_position)

    def _find_histogram_peak_in_selected_range(
        self,
        *,
        counts: np.ndarray,
        centers: np.ndarray,
        selected_x_range: tuple[float, float],
        fallback_value: float,
    ) -> float | None:
        """
        Return the tallest histogram bin center inside the selected x range.
        """
        counts = np.asarray(counts, dtype=float)
        centers = np.asarray(centers, dtype=float)

        if counts.size == 0 or centers.size != counts.size:
            return None

        lower_value = float(min(selected_x_range))
        upper_value = float(max(selected_x_range))

        range_mask = (
            np.isfinite(counts)
            & np.isfinite(centers)
            & (centers >= lower_value)
            & (centers <= upper_value)
        )

        if not np.any(range_mask):
            return float(fallback_value)

        range_indices = np.flatnonzero(range_mask)
        range_counts = counts[range_indices]

        if range_counts.size == 0:
            return float(fallback_value)

        highest_count = float(np.max(range_counts))
        highest_indices = range_indices[
            np.isclose(
                range_counts,
                highest_count,
                rtol=1e-9,
                atol=0.0,
            )
        ]

        if highest_indices.size == 0:
            return float(fallback_value)

        chosen_index = int(
            highest_indices[
                np.argmin(
                    np.abs(
                        centers[highest_indices] - float(fallback_value)
                    )
                )
            ]
        )

        return float(centers[chosen_index])

    def _climb_histogram_peak_1d(
        self,
        *,
        counts: np.ndarray,
        edges: np.ndarray,
        centers: np.ndarray,
        clicked_value: float,
    ) -> float | None:
        """
        Climb the histogram from the clicked bin to the local summit.
        """
        counts = np.asarray(
            counts,
            dtype=float,
        )
        edges = np.asarray(edges, dtype=float)
        centers = np.asarray(centers, dtype=float)

        if (
            counts.size == 0
            or edges.size != counts.size + 1
            or centers.size != counts.size
            or not np.isfinite(clicked_value)
        ):
            return None

        finite_mask = np.isfinite(counts) & np.isfinite(centers)

        if not np.any(finite_mask):
            return None

        clicked_index = int(
            np.clip(
                np.searchsorted(
                    edges,
                    float(clicked_value),
                    side="right",
                ) - 1,
                0,
                counts.size - 1,
            )
        )

        current_index = clicked_index

        while True:
            current_count = counts[current_index]
            left_count = (
                counts[current_index - 1]
                if current_index > 0
                else -np.inf
            )
            right_count = (
                counts[current_index + 1]
                if current_index < counts.size - 1
                else -np.inf
            )

            if left_count <= current_count and right_count <= current_count:
                break

            if right_count > current_count and right_count >= left_count:
                current_index += 1
                continue

            if left_count > current_count and left_count > right_count:
                current_index -= 1
                continue

            if left_count == right_count and left_count > current_count:
                if abs(current_index + 1 - clicked_index) <= abs(current_index - 1 - clicked_index):
                    current_index += 1
                else:
                    current_index -= 1
                continue

            break

        plateau_start = current_index
        plateau_end = current_index

        while (
            plateau_start > 0
            and counts[plateau_start - 1] == counts[current_index]
        ):
            plateau_start -= 1

        while (
            plateau_end < counts.size - 1
            and counts[plateau_end + 1] == counts[current_index]
        ):
            plateau_end += 1

        plateau_centers = centers[
            plateau_start : plateau_end + 1
        ]

        if plateau_centers.size == 0:
            return float(centers[current_index])

        return float(
            plateau_centers[
                int(
                    np.argmin(
                        np.abs(
                            plateau_centers - float(clicked_value)
                        )
                    )
                )
            ]
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all manually picked 1D peaks.

        Returns
        -------
        PeakProcessResult
            Empty peak result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared manual 1D peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
    ) -> dict[str, list[Any]]:
        """
        Build the graph annotation payload for selected 1D peaks.

        Parameters
        ----------
        peak_positions:
            Cumulative peak positions.

        Returns
        -------
        dict[str, list[Any]]
            Peak line payload.
        """
        return {
            "positions": [
                float(value)
                for value in peak_positions
            ],
            "labels": [
                f"Manual peak {index + 1}"
                for index in range(len(peak_positions))
            ],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }

    def extract_peak_positions_from_payload(
        self,
        peak_lines_payload: Any,
    ) -> list[float]:
        """
        Extract cumulative peak positions from an existing payload.

        Parameters
        ----------
        peak_lines_payload:
            Existing peak line payload.

        Returns
        -------
        list[float]
            Existing peak positions.
        """
        if not isinstance(peak_lines_payload, dict):
            return []

        peak_positions: list[float] = []

        for value in peak_lines_payload.get("positions") or []:
            try:
                peak_positions.append(
                    float(value),
                )

            except Exception:
                logger.debug(
                    "Ignoring non numeric manual 1D peak position value=%r",
                    value,
                )

        return peak_positions

    def extract_clicked_x_position(self, click_data: Any) -> float | None:
        """Extract a finite x coordinate from the first Plotly click point."""
        position = read_clicked_position(payload=click_data, axes=("x",))
        return position["x"] if position is not None else None

    def extract_selected_x_range(self, selected_data: Any) -> tuple[float, float] | None:
        """Extract the x bounds of the Plotly selection."""
        bounds = read_selected_ranges(payload=selected_data, axes=("x",))
        return bounds["x"] if bounds is not None else None


PROCESS = Manual1DClickProcess()
