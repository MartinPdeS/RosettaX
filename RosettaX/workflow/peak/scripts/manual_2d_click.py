
import logging
import numpy as np
from ..core.process_calls import standard_peak_action
from ._events import filter_finite_peak_events, read_peak_event_columns
from ._manual_controls import ManualPeakControls
from ._manual_selection import read_clicked_position, read_selected_ranges
from .base import (
    BasePeakProcess,
    PeakProcessResult,
    filter_edge_artifact_pairs,
    resolve_edge_artifact_filter_enabled,
)
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from typing import Any

logger = logging.getLogger(__name__)


class Manual2DClickProcess(ManualPeakControls, BasePeakProcess):
    """
    Manual 2D peak picking process.

    The user selects an x detector channel and a y detector channel, then clicks
    points in the 2D scatter plot to add peak positions.

    The graph receives the cumulative list of picked points. The calibration
    table receives only the current click delta through new_peak_positions.
    """

    process_name = "Manual 2D"
    process_label = "Manual 2D"
    description = "Click the two-dimensional scatter plot to add calibration peak positions."
    graph_type = "2d_scatter"
    sort_order = 30

    supports_manual_click = True
    supports_clear = True
    supports_automatic_action = False
    force_graph_visible = True

    detector_controls = (
        ("x", "X detector channel", "Select x channel"),
        ("y", "Y detector channel", "Select y channel"),
    )
    log_axes = ("x", "y")
    snap_mode_label = "density"
    default_snap_histogram_bins = 100

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
        Add one clicked 2D point to the cumulative peak payload.

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
        logger.debug(
            "Manual 2D add_clicked_peak called with click_data=%r selected_data=%r "
            "existing_peak_lines_payload=%r",
            click_data,
            selected_data,
            existing_peak_lines_payload,
        )

        clicked_peak_position = self.extract_clicked_xy_position(click_data)
        selected_xy_range = self.extract_selected_xy_range(selected_data)

        if clicked_peak_position is None and selected_xy_range is None:
            logger.debug("No valid 2D clicked peak position or selection could be extracted.")
            return None

        reference_peak_position = (
            dict(clicked_peak_position)
            if clicked_peak_position is not None
            else {
                "x": float(
                    0.5 * (
                        selected_xy_range["x"][0]
                        + selected_xy_range["x"][1]
                    )
                ),
                "y": float(
                    0.5 * (
                        selected_xy_range["y"][0]
                        + selected_xy_range["y"][1]
                    )
                ),
            }
        )

        snapped_peak_position = dict(
            reference_peak_position,
        )
        snap_was_applied = False

        if self._snap_to_local_mode_is_enabled(
            process_settings=process_settings,
        ):
            resolved_peak_position = self.snap_clicked_peak_position(
                backend=backend,
                detector_channels=detector_channels,
                clicked_peak_position=reference_peak_position,
                selected_xy_range=selected_xy_range,
                process_settings=process_settings,
                runtime_config_data=runtime_config_data,
                axis_scale_toggle_values=axis_scale_toggle_values,
            )

            if resolved_peak_position is not None:
                snapped_peak_position = resolved_peak_position
                snap_was_applied = not (
                    np.isclose(
                        snapped_peak_position["x"],
                        reference_peak_position["x"],
                        rtol=1e-6,
                        atol=0.0,
                    )
                    and np.isclose(
                        snapped_peak_position["y"],
                        reference_peak_position["y"],
                        rtol=1e-6,
                        atol=0.0,
                    )
                )

        existing_peak_positions = self.extract_peak_positions_from_payload(
            existing_peak_lines_payload,
        )

        for existing_peak_position in existing_peak_positions:
            if (
                np.isclose(
                    existing_peak_position["x"],
                    snapped_peak_position["x"],
                    rtol=1e-9,
                    atol=0.0,
                )
                and np.isclose(
                    existing_peak_position["y"],
                    snapped_peak_position["y"],
                    rtol=1e-9,
                    atol=0.0,
                )
            ):
                return PeakProcessResult(
                    peak_positions=existing_peak_positions,
                    peak_lines_payload=self.build_peak_lines_payload(
                        peak_positions=existing_peak_positions,
                    ),
                    status=(
                        "Peak at "
                        f"x={snapped_peak_position['x']:.6g}, "
                        f"y={snapped_peak_position['y']:.6g} is already selected."
                    ),
                    new_peak_positions=[],
                    clear_existing_table_peaks=False,
                )

        next_peak_positions = [
            *existing_peak_positions,
            snapped_peak_position,
        ]

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=next_peak_positions,
        )

        if snap_was_applied:
            status = (
                f"Added peak at "
                f"x={snapped_peak_position['x']:.6g}, "
                f"y={snapped_peak_position['y']:.6g} "
                f"(selected around x={reference_peak_position['x']:.6g}, "
                f"y={reference_peak_position['y']:.6g}). "
                f"{len(next_peak_positions)} peak(s) selected."
            )
        else:
            status = (
                f"Added peak at "
                f"x={snapped_peak_position['x']:.6g}, "
                f"y={snapped_peak_position['y']:.6g}. "
                f"{len(next_peak_positions)} peak(s) selected."
            )

        logger.debug(
            "Manual 2D click added clicked_peak_position=%r "
            "existing_peak_positions=%r next_peak_positions=%r "
            "peak_lines_payload=%r status=%r",
            snapped_peak_position,
            existing_peak_positions,
            next_peak_positions,
            peak_lines_payload,
            status,
        )

        return PeakProcessResult(
            peak_positions=next_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=[
                {
                    "x": float(snapped_peak_position["x"]),
                    "y": float(snapped_peak_position["y"]),
                }
            ],
            clear_existing_table_peaks=False,
        )

    def snap_clicked_peak_position(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any] | None,
        clicked_peak_position: dict[str, float],
        selected_xy_range: dict[str, tuple[float, float]] | None,
        process_settings: dict[str, Any] | None,
        runtime_config_data: Any,
        axis_scale_toggle_values: Any,
    ) -> dict[str, float] | None:
        """
        Snap one clicked 2D position to the local modal density nearby.
        """
        if backend is None or not hasattr(backend, "fcs_file_path"):
            return None

        resolved_detector_channels = detector_channels or {}
        x_detector_column = resolved_detector_channels.get("x")
        y_detector_column = resolved_detector_channels.get("y")

        if not str(x_detector_column or "").strip():
            return None

        if not str(y_detector_column or "").strip():
            return None

        max_events, configured_bins = self._resolve_snap_settings(runtime_config_data=runtime_config_data)
        columns = read_peak_event_columns(
            fcs_file_path=backend.fcs_file_path, detector_columns=(x_detector_column, y_detector_column),
            max_events=max_events,
        )
        x_values, y_values = columns
        if resolve_edge_artifact_filter_enabled(
            process_settings=process_settings,
            default=True,
        ):
            x_values, y_values = filter_edge_artifact_pairs(
                x_values=x_values,
                y_values=y_values,
                remove_x_min=True,
                remove_x_max=True,
                remove_y_min=True,
                remove_y_max=False,
            )
        else:
            (x_values, y_values), _ = filter_finite_peak_events(columns=columns)

        if x_values.size < 16 or y_values.size < 16:
            return None

        use_log_x = self._x_axis_is_log(
            process_settings=process_settings,
            axis_scale_toggle_values=axis_scale_toggle_values,
            axis="x",
            clicked_value=clicked_peak_position["x"],
        )
        use_log_y = self._x_axis_is_log(
            process_settings=process_settings,
            axis_scale_toggle_values=axis_scale_toggle_values,
            axis="y",
            clicked_value=clicked_peak_position["y"],
        )

        positive_mask = np.ones(
            x_values.shape,
            dtype=bool,
        )

        if use_log_x:
            positive_mask &= x_values > 0.0

        if use_log_y:
            positive_mask &= y_values > 0.0

        x_values = x_values[positive_mask]
        y_values = y_values[positive_mask]

        if x_values.size < 16 or y_values.size < 16:
            return None

        if use_log_x and clicked_peak_position["x"] <= 0.0:
            return None

        if use_log_y and clicked_peak_position["y"] <= 0.0:
            return None

        working_x_values = np.log10(x_values) if use_log_x else x_values
        working_y_values = np.log10(y_values) if use_log_y else y_values
        working_clicked_x = float(
            np.log10(clicked_peak_position["x"])
            if use_log_x
            else clicked_peak_position["x"]
        )
        working_clicked_y = float(
            np.log10(clicked_peak_position["y"])
            if use_log_y
            else clicked_peak_position["y"]
        )

        histogram_bins = max(24, min(160, configured_bins))
        histogram, x_edges, y_edges = np.histogram2d(
            working_x_values,
            working_y_values,
            bins=(histogram_bins, histogram_bins),
        )
        x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
        y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])

        if selected_xy_range is not None:
            working_selected_xy_range = {
                "x": (
                    float(
                        np.log10(selected_xy_range["x"][0])
                        if use_log_x
                        else selected_xy_range["x"][0]
                    ),
                    float(
                        np.log10(selected_xy_range["x"][1])
                        if use_log_x
                        else selected_xy_range["x"][1]
                    ),
                ),
                "y": (
                    float(
                        np.log10(selected_xy_range["y"][0])
                        if use_log_y
                        else selected_xy_range["y"][0]
                    ),
                    float(
                        np.log10(selected_xy_range["y"][1])
                        if use_log_y
                        else selected_xy_range["y"][1]
                    ),
                ),
            }

            snapped_working_point = self._find_histogram_peak_in_selected_range_2d(
                histogram=np.asarray(histogram, dtype=float),
                x_centers=np.asarray(x_centers, dtype=float),
                y_centers=np.asarray(y_centers, dtype=float),
                selected_xy_range=working_selected_xy_range,
                fallback_point={
                    "x": working_clicked_x,
                    "y": working_clicked_y,
                },
            )
        else:
            snapped_working_point = self._find_local_mode_2d(
                x_values=working_x_values,
                y_values=working_y_values,
                clicked_x=working_clicked_x,
                clicked_y=working_clicked_y,
            )

        if snapped_working_point is None:
            return None

        snapped_x = float(
            np.power(10.0, snapped_working_point["x"])
        ) if use_log_x else float(snapped_working_point["x"])
        snapped_y = float(
            np.power(10.0, snapped_working_point["y"])
        ) if use_log_y else float(snapped_working_point["y"])

        if not np.isfinite(snapped_x) or not np.isfinite(snapped_y):
            return None

        return {
            "x": snapped_x,
            "y": snapped_y,
        }

    def _x_axis_is_log(
        self,
        *,
        process_settings: dict[str, Any] | None,
        axis_scale_toggle_values: Any,
        axis: str,
        clicked_value: float,
    ) -> bool:
        """
        Return whether one manual 2D axis is currently log scaled.
        """
        if clicked_value <= 0.0:
            return False

        if isinstance(process_settings, dict):
            process_value = process_settings.get(
                f"{axis}_log_scale",
                None,
            )

            if isinstance(process_value, str):
                return process_value == "enabled"

            if isinstance(process_value, (list, tuple, set)):
                return "enabled" in process_value

            if isinstance(process_value, bool):
                return process_value

        expected_toggle = (
            Scatter2DGraph.x_log_value
            if axis == "x"
            else Scatter2DGraph.y_log_value
        )

        if isinstance(axis_scale_toggle_values, str):
            return axis_scale_toggle_values in (
                "log",
                expected_toggle,
            )

        if isinstance(axis_scale_toggle_values, (list, tuple, set)):
            return (
                "log" in axis_scale_toggle_values
                or expected_toggle in axis_scale_toggle_values
            )

        return False

    def _find_local_mode_2d(
        self,
        *,
        x_values: np.ndarray,
        y_values: np.ndarray,
        clicked_x: float,
        clicked_y: float,
    ) -> dict[str, float] | None:
        """
        Estimate a local 2D mode near the clicked position.
        """
        x_values = np.asarray(
            x_values,
            dtype=float,
        )
        y_values = np.asarray(
            y_values,
            dtype=float,
        )

        finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
        x_values = x_values[finite_mask]
        y_values = y_values[finite_mask]

        if x_values.size < 16 or not np.isfinite(clicked_x) or not np.isfinite(clicked_y):
            return None

        distances = np.hypot(
            x_values - float(clicked_x),
            y_values - float(clicked_y),
        )
        neighbor_count = max(
            128,
            min(
                x_values.size,
                int(x_values.size * 0.03),
                4096,
            ),
        )

        radius = float(
            np.partition(
                distances,
                neighbor_count - 1,
            )[neighbor_count - 1]
        )

        if radius <= 0.0 or not np.isfinite(radius):
            radius = float(
                max(
                    np.std(x_values) * 0.02,
                    np.std(y_values) * 0.02,
                    np.finfo(float).eps,
                )
            )

        local_mask = distances <= radius
        local_x_values = x_values[local_mask]
        local_y_values = y_values[local_mask]

        if local_x_values.size < 16:
            return {
                "x": float(clicked_x),
                "y": float(clicked_y),
            }

        x_lower = float(np.min(local_x_values))
        x_upper = float(np.max(local_x_values))
        y_lower = float(np.min(local_y_values))
        y_upper = float(np.max(local_y_values))

        if x_lower == x_upper or y_lower == y_upper:
            return {
                "x": float(np.median(local_x_values)),
                "y": float(np.median(local_y_values)),
            }

        bins_per_axis = int(
            max(
                16,
                min(
                    48,
                    np.sqrt(local_x_values.size),
                ),
            )
        )

        histogram, x_edges, y_edges = np.histogram2d(
            local_x_values,
            local_y_values,
            bins=(bins_per_axis, bins_per_axis),
            range=[
                [x_lower, x_upper],
                [y_lower, y_upper],
            ],
        )

        if histogram.size == 0:
            return {
                "x": float(clicked_x),
                "y": float(clicked_y),
            }

        modal_x_index, modal_y_index = np.unravel_index(
            int(np.argmax(histogram)),
            histogram.shape,
        )

        x_left = float(x_edges[modal_x_index])
        x_right = float(x_edges[modal_x_index + 1])
        y_lower_edge = float(y_edges[modal_y_index])
        y_upper_edge = float(y_edges[modal_y_index + 1])

        x_mask = (
            (local_x_values >= x_left)
            & (
                (local_x_values <= x_right)
                if modal_x_index == histogram.shape[0] - 1
                else (local_x_values < x_right)
            )
        )
        y_mask = (
            (local_y_values >= y_lower_edge)
            & (
                (local_y_values <= y_upper_edge)
                if modal_y_index == histogram.shape[1] - 1
                else (local_y_values < y_upper_edge)
            )
        )
        modal_mask = x_mask & y_mask

        if not np.any(modal_mask):
            return {
                "x": 0.5 * (x_left + x_right),
                "y": 0.5 * (y_lower_edge + y_upper_edge),
            }

        return {
            "x": float(np.median(local_x_values[modal_mask])),
            "y": float(np.median(local_y_values[modal_mask])),
        }

    def _find_histogram_peak_in_selected_range_2d(
        self,
        *,
        histogram: np.ndarray,
        x_centers: np.ndarray,
        y_centers: np.ndarray,
        selected_xy_range: dict[str, tuple[float, float]],
        fallback_point: dict[str, float],
    ) -> dict[str, float] | None:
        """
        Return the densest histogram bin center inside the selected 2D ROI.
        """
        histogram = np.asarray(histogram, dtype=float)
        x_centers = np.asarray(x_centers, dtype=float)
        y_centers = np.asarray(y_centers, dtype=float)

        if (
            histogram.ndim != 2
            or histogram.shape != (x_centers.size, y_centers.size)
            or x_centers.size == 0
            or y_centers.size == 0
        ):
            return None

        x_lower = float(min(selected_xy_range["x"]))
        x_upper = float(max(selected_xy_range["x"]))
        y_lower = float(min(selected_xy_range["y"]))
        y_upper = float(max(selected_xy_range["y"]))

        x_mask = (
            np.isfinite(x_centers)
            & (x_centers >= x_lower)
            & (x_centers <= x_upper)
        )
        y_mask = (
            np.isfinite(y_centers)
            & (y_centers >= y_lower)
            & (y_centers <= y_upper)
        )

        if not np.any(x_mask) or not np.any(y_mask):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        x_indices = np.flatnonzero(x_mask)
        y_indices = np.flatnonzero(y_mask)
        roi_histogram = histogram[np.ix_(x_indices, y_indices)]

        if roi_histogram.size == 0 or not np.any(np.isfinite(roi_histogram)):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        roi_maximum = float(np.nanmax(roi_histogram))

        if not np.isfinite(roi_maximum):
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        candidate_offsets = np.argwhere(
            np.isclose(
                roi_histogram,
                roi_maximum,
                rtol=1e-9,
                atol=0.0,
            )
        )

        if candidate_offsets.size == 0:
            return {
                "x": float(fallback_point["x"]),
                "y": float(fallback_point["y"]),
            }

        candidate_points = [
            (
                float(x_centers[x_indices[offset_x]]),
                float(y_centers[y_indices[offset_y]]),
            )
            for offset_x, offset_y in candidate_offsets
        ]

        chosen_x, chosen_y = min(
            candidate_points,
            key=lambda point: (
                (point[0] - float(fallback_point["x"])) ** 2
                + (point[1] - float(fallback_point["y"])) ** 2
            ),
        )

        return {
            "x": chosen_x,
            "y": chosen_y,
        }

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all manually picked 2D peaks.

        Returns
        -------
        PeakProcessResult
            Empty peak result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared manual 2D peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
    ) -> dict[str, list[Any]]:
        """
        Build the graph annotation payload for selected 2D peaks.

        Parameters
        ----------
        peak_positions:
            Cumulative 2D peak positions.

        Returns
        -------
        dict[str, list[Any]]
            Peak annotation payload.
        """
        x_positions = [
            float(position["x"])
            for position in peak_positions
        ]

        y_positions = [
            float(position["y"])
            for position in peak_positions
        ]

        labels = [
            f"Manual 2D peak {index + 1}"
            for index in range(len(peak_positions))
        ]

        return {
            "positions": x_positions,
            "x_positions": x_positions,
            "y_positions": y_positions,
            "points": [
                {
                    "x": float(position["x"]),
                    "y": float(position["y"]),
                }
                for position in peak_positions
            ],
            "labels": labels,
        }

    def extract_peak_positions_from_payload(
        self,
        peak_lines_payload: Any,
    ) -> list[dict[str, float]]:
        """
        Extract cumulative 2D peak positions from an existing payload.

        Parameters
        ----------
        peak_lines_payload:
            Existing peak line payload.

        Returns
        -------
        list[dict[str, float]]
            Existing 2D peak positions.
        """
        if not isinstance(peak_lines_payload, dict):
            return []

        points = peak_lines_payload.get("points")

        if isinstance(points, list):
            return self.extract_peak_positions_from_point_payload(
                points,
            )

        return self.extract_peak_positions_from_xy_payload(
            x_values=peak_lines_payload.get("x_positions"),
            y_values=peak_lines_payload.get("y_positions"),
        )

    def extract_peak_positions_from_point_payload(
        self,
        points: list[Any],
    ) -> list[dict[str, float]]:
        """
        Extract 2D peak positions from a list of point dictionaries.

        Parameters
        ----------
        points:
            Point payload list.

        Returns
        -------
        list[dict[str, float]]
            Parsed 2D peak positions.
        """
        peak_positions: list[dict[str, float]] = []

        for point in points:
            if not isinstance(point, dict):
                logger.debug(
                    "Ignoring non mapping 2D peak point=%r",
                    point,
                )
                continue

            try:
                peak_positions.append(
                    {
                        "x": float(point["x"]),
                        "y": float(point["y"]),
                    }
                )

            except Exception:
                logger.debug(
                    "Ignoring invalid 2D peak point=%r",
                    point,
                )

        return peak_positions

    def extract_peak_positions_from_xy_payload(
        self,
        *,
        x_values: Any,
        y_values: Any,
    ) -> list[dict[str, float]]:
        """
        Extract 2D peak positions from separate x and y arrays.

        Parameters
        ----------
        x_values:
            X coordinate values.

        y_values:
            Y coordinate values.

        Returns
        -------
        list[dict[str, float]]
            Parsed 2D peak positions.
        """
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            return []

        peak_positions: list[dict[str, float]] = []

        for x_value, y_value in zip(
            x_values,
            y_values,
            strict=False,
        ):
            try:
                peak_positions.append(
                    {
                        "x": float(x_value),
                        "y": float(y_value),
                    }
                )

            except Exception:
                logger.debug(
                    "Ignoring invalid 2D peak coordinate x=%r y=%r",
                    x_value,
                    y_value,
                )

        return peak_positions

    def extract_clicked_xy_position(self, click_data: Any) -> dict[str, float] | None:
        """Extract finite x and y coordinates from the first Plotly click point."""
        return read_clicked_position(payload=click_data, axes=("x", "y"))

    def extract_selected_xy_range(self, selected_data: Any) -> dict[str, tuple[float, float]] | None:
        """Extract the x and y bounds of the Plotly selection."""
        return read_selected_ranges(payload=selected_data, axes=("x", "y"))


PROCESS = Manual2DClickProcess()
