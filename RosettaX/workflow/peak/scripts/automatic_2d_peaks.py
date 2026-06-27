# -*- coding: utf-8 -*-

from typing import Any
import logging

import numpy as np

from .base import BasePeakProcess, PeakProcessResult, resolve_integer_setting, resolve_integer_value
from RosettaX.utils.io import column_copy
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph


logger = logging.getLogger(__name__)


class Automatic2DPeakProcess(BasePeakProcess):
    """
    Automatic 2D peak detection process.

    The user selects an x detector channel and a y detector channel. The process
    builds a 2D histogram and detects local maxima in that histogram.

    The graph receives all detected 2D points. The calibration table receives
    the x coordinates through the page specific adapter.
    """

    process_name = "Automatic 2D"
    process_label = "Automatic 2D"
    graph_type = "2d_scatter"
    sort_order = 40

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

    default_peak_count = 5
    default_histogram_bins = 500
    default_smoothing_window = 5
    default_minimum_separation_bins = 1
    default_detection_space = "log"

    def get_required_detector_channels(self) -> list[str]:
        """
        Return detector channels required by this process.
        """
        return [
            "x",
            "y",
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user visible detector labels.
        """
        return {
            "x": "X axis channel",
            "y": "Y axis channel",
        }

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return configurable process settings.
        """
        return [
            {
                "name": "peak_count",
                "label": "Peak count",
                "kind": "integer",
                "default_value": self.default_peak_count,
                "min_value": 1,
                "max_value": 100,
                "step": 1,
                "help": (
                    "Maximum number of 2D density peaks returned by the detector. "
                    "Use the expected number of calibration populations. Increase it "
                    "when you expect more populations. Decrease it when weak shoulders "
                    "or noise maxima are being returned."
                ),
            },
            {
                "name": "histogram_bins",
                "label": "2D bins",
                "kind": "integer",
                "default_value": self.default_histogram_bins,
                "min_value": 20,
                "max_value": 1000,
                "step": 10,
                "help": (
                    "Number of bins used on each axis to build the 2D density histogram. "
                    "More bins improve spatial resolution but make the density map noisier. "
                    "Fewer bins make the density map smoother but can merge nearby populations."
                ),
            },
            {
                "name": "smoothing_window",
                "label": "Smoothing",
                "kind": "integer",
                "default_value": self.default_smoothing_window,
                "min_value": 1,
                "max_value": 31,
                "step": 2,
                "help": (
                    "Square moving average window applied to the 2D histogram before "
                    "local maxima detection. Increase it to suppress noisy isolated bins. "
                    "Decrease it when nearby populations are being merged or shifted."
                ),
            },
            {
                "name": "minimum_separation_bins",
                "label": "Min separation",
                "kind": "integer",
                "default_value": self.default_minimum_separation_bins,
                "min_value": 1,
                "max_value": 100,
                "step": 1,
                "help": (
                    "Minimum Euclidean separation between accepted 2D peaks, expressed "
                    "in histogram bin units. If two candidate peaks are closer than this, "
                    "only the stronger one is kept. Increase it to merge nearby shoulders. "
                    "Decrease it to allow close populations."
                ),
            },
            {
                "name": "detection_space",
                "label": "Detection space",
                "kind": "select",
                "default_value": self.default_detection_space,
                "options": [
                    {"label": "Log", "value": "log"},
                    {"label": "Linear", "value": "linear"},
                ],
                "help": (
                    "Coordinate space used to build the 2D detection histogram. "
                    "Log usually works better for bead populations spread across decades. "
                    "Linear can help when the data are naturally linear."
                ),
            },
        ]

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        process_settings: dict[str, Any],
        max_events_for_analysis: Any = None,
        max_events_for_plots: Any = None,
        **_kwargs: Any,
    ) -> PeakProcessResult:
        """
        Run automatic 2D peak detection.
        """
        if backend is None or not hasattr(backend, "fcs_file_path"):
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="The backend does not expose fcs_file_path.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        x_detector_column = detector_channels.get(
            "x",
        )

        y_detector_column = detector_channels.get(
            "y",
        )

        if not x_detector_column or not y_detector_column:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select both x and y detector channels first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        peak_count = resolve_integer_setting(
            settings=process_settings,
            name="peak_count",
            default=self.default_peak_count,
            minimum=1,
            maximum=100,
        )

        histogram_bins = resolve_integer_setting(
            settings=process_settings,
            name="histogram_bins",
            default=self.default_histogram_bins,
            minimum=20,
            maximum=1000,
        )

        smoothing_window = resolve_integer_setting(
            settings=process_settings,
            name="smoothing_window",
            default=self.default_smoothing_window,
            minimum=1,
            maximum=31,
        )

        minimum_separation_bins = resolve_integer_setting(
            settings=process_settings,
            name="minimum_separation_bins",
            default=self.default_minimum_separation_bins,
            minimum=1,
            maximum=100,
        )
        advanced_mode = self._resolve_advanced_mode(
            process_settings=process_settings,
        )
        use_log_x, use_log_y = self._resolve_detection_space(
            process_settings=process_settings,
        )

        max_events = resolve_integer_value(
            value=max_events_for_analysis
            if max_events_for_analysis is not None
            else max_events_for_plots,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        x_values = column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(x_detector_column),
            dtype=float,
            n=max_events,
        )

        y_values = column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(y_detector_column),
            dtype=float,
            n=max_events,
        )

        detected_peak_positions, detection_debug = find_2d_histogram_peak_positions(
            x_values=x_values,
            y_values=y_values,
            peak_count=peak_count,
            histogram_bins=histogram_bins,
            smoothing_window=smoothing_window,
            minimum_separation_bins=minimum_separation_bins,
            use_log_x=use_log_x,
            use_log_y=use_log_y,
            include_debug_grid=advanced_mode,
        )

        detected_peak_positions = self.deduplicate_2d_peak_positions(
            peak_positions=detected_peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=detected_peak_positions,
            debug_info=detection_debug,
        )

        status = (
            f"Detected {len(detected_peak_positions)} automatic 2D peak(s)."
        )

        if advanced_mode:
            status = (
                f"{status} Debug: finite={detection_debug.get('finite_value_count', 0)}, "
                f"positive={detection_debug.get('positive_value_count', 0)}, "
                f"roi={detection_debug.get('range_filtered_value_count', 0)}, "
                f"candidates={detection_debug.get('candidate_count', 0)}, "
                f"selected={detection_debug.get('selected_count', 0)}"
            )

        logger.debug(
            "Automatic 2D detection completed with peak_count=%r "
            "histogram_bins=%r smoothing_window=%r "
            "minimum_separation_bins=%r detected_peak_positions=%r",
            peak_count,
            histogram_bins,
            smoothing_window,
            minimum_separation_bins,
            detected_peak_positions,
        )

        return PeakProcessResult(
            peak_positions=detected_peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=detected_peak_positions,
            clear_existing_table_peaks=False,
        )

    def _resolve_advanced_mode(
        self,
        *,
        process_settings: dict[str, Any],
    ) -> bool:
        """
        Resolve advanced mode from callback-provided process settings.
        """
        value = process_settings.get("advanced_mode", None)

        if isinstance(value, str):
            return value == "enabled"

        if isinstance(value, (list, tuple, set)):
            return "enabled" in value

        if isinstance(value, bool):
            return value

        return False

    def _resolve_detection_space(
        self,
        *,
        process_settings: dict[str, Any],
    ) -> tuple[bool, bool]:
        """
        Resolve whether the detector should analyze the 2D histogram in log space.
        """
        detection_space = str(
            process_settings.get(
                "detection_space",
                self.default_detection_space,
            )
            or self.default_detection_space
        ).strip().lower()

        if detection_space == "linear":
            return False, False

        if detection_space == "log":
            return True, True

        toggle_values = process_settings.get("axis_scale_toggle_values", None)

        if isinstance(toggle_values, str):
            return (
                toggle_values == Scatter2DGraph.x_log_value,
                toggle_values == Scatter2DGraph.y_log_value,
            )

        if isinstance(toggle_values, (list, tuple, set)):
            return (
                Scatter2DGraph.x_log_value in toggle_values,
                Scatter2DGraph.y_log_value in toggle_values,
            )

        return True, True

    def deduplicate_2d_peak_positions(
        self,
        *,
        peak_positions: list[dict[str, float]],
        decimal_places: int = 12,
    ) -> list[dict[str, float]]:
        """
        Remove duplicate 2D peak positions while preserving order.

        This protects the table and graph payload from receiving the same detected
        peak more than once.
        """
        unique_peak_positions: list[dict[str, float]] = []
        seen_keys: set[tuple[float, float]] = set()

        for peak_position in peak_positions:
            try:
                x_value = float(
                    peak_position["x"],
                )
                y_value = float(
                    peak_position["y"],
                )

            except (KeyError, TypeError, ValueError):
                continue

            if not np.isfinite(x_value) or not np.isfinite(y_value):
                continue

            key = (
                round(
                    x_value,
                    int(decimal_places),
                ),
                round(
                    y_value,
                    int(decimal_places),
                ),
            )

            if key in seen_keys:
                continue

            seen_keys.add(
                key,
            )

            unique_peak_positions.append(
                {
                    "x": x_value,
                    "y": y_value,
                }
            )

        return unique_peak_positions

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear automatically detected 2D peaks.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared automatic 2D peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_empty_peak_lines_payload(self) -> dict[str, list[Any]]:
        """
        Build an empty graph annotation payload.
        """
        return {
            "positions": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
            "labels": [],
            "debug": {},
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
        debug_info: dict[str, Any] | None = None,
    ) -> dict[str, list[Any]]:
        """
        Build graph annotation payload for detected 2D peaks.
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
            f"Automatic 2D peak {index + 1}"
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
            "debug": dict(debug_info or {}),
        }


def find_2d_histogram_peak_positions(
    *,
    x_values: Any,
    y_values: Any,
    peak_count: int,
    histogram_bins: int,
    smoothing_window: int,
    minimum_separation_bins: int,
    use_log_x: bool = False,
    use_log_y: bool = False,
    include_debug_grid: bool = False,
) -> tuple[list[dict[str, float]], dict[str, Any]]:
    """
    Detect 2D peak positions from a smoothed 2D histogram.
    """
    x_values = np.asarray(
        x_values,
        dtype=float,
    )

    y_values = np.asarray(
        y_values,
        dtype=float,
    )

    debug_info: dict[str, Any] = {
        "input_value_count": int(min(x_values.size, y_values.size)),
        "finite_value_count": 0,
        "positive_value_count": 0,
        "range_filtered_value_count": 0,
        "candidate_count": 0,
        "selected_count": 0,
        "candidate_points": [],
        "selected_bin_indices": [],
        "use_log_x": bool(use_log_x),
        "use_log_y": bool(use_log_y),
    }

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)

    x_values = x_values[finite_mask]
    y_values = y_values[finite_mask]
    debug_info["finite_value_count"] = int(x_values.size)

    if x_values.size == 0 or y_values.size == 0:
        return [], debug_info

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
    debug_info["positive_value_count"] = int(x_values.size)

    if x_values.size == 0 or y_values.size == 0:
        return [], debug_info

    histogram_x_values = np.log10(x_values) if use_log_x else x_values
    histogram_y_values = np.log10(y_values) if use_log_y else y_values

    x_lower, x_upper = np.quantile(
        histogram_x_values,
        [
            0.001,
            0.999,
        ],
    )

    y_lower, y_upper = np.quantile(
        histogram_y_values,
        [
            0.001,
            0.999,
        ],
    )

    range_mask = (
        (histogram_x_values >= x_lower)
        & (histogram_x_values <= x_upper)
        & (histogram_y_values >= y_lower)
        & (histogram_y_values <= y_upper)
    )

    histogram_x_values = histogram_x_values[range_mask]
    histogram_y_values = histogram_y_values[range_mask]
    debug_info["range_filtered_value_count"] = int(histogram_x_values.size)
    debug_info["x_lower_quantile"] = float(10 ** x_lower) if use_log_x else float(x_lower)
    debug_info["x_upper_quantile"] = float(10 ** x_upper) if use_log_x else float(x_upper)
    debug_info["y_lower_quantile"] = float(10 ** y_lower) if use_log_y else float(y_lower)
    debug_info["y_upper_quantile"] = float(10 ** y_upper) if use_log_y else float(y_upper)

    if histogram_x_values.size == 0 or histogram_y_values.size == 0:
        return [], debug_info

    histogram, x_edges, y_edges = np.histogram2d(
        histogram_x_values,
        histogram_y_values,
        bins=int(histogram_bins),
    )
    debug_info["histogram_shape"] = [
        int(histogram.shape[0]),
        int(histogram.shape[1]),
    ]

    if histogram.size == 0:
        return [], debug_info

    smoothed_histogram = smooth_2d_array(
        values=histogram,
        window_size=smoothing_window,
    )

    candidate_indices = find_local_maxima_2d_indices(
        values=smoothed_histogram,
    )

    if not candidate_indices:
        candidate_indices = [
            tuple(index_pair)
            for index_pair in np.argwhere(
                smoothed_histogram == np.nanmax(smoothed_histogram)
            )
        ]

    debug_info["candidate_count"] = int(len(candidate_indices))

    candidate_indices = sorted(
        candidate_indices,
        key=lambda index_pair: smoothed_histogram[index_pair[0], index_pair[1]],
        reverse=True,
    )

    selected_indices = select_separated_peak_indices(
        candidate_indices=candidate_indices,
        values=smoothed_histogram,
        peak_count=peak_count,
        minimum_separation_bins=minimum_separation_bins,
    )

    x_centers = 0.5 * (
        x_edges[:-1] + x_edges[1:]
    )
    if use_log_x:
        x_centers = np.power(
            10.0,
            x_centers,
        )

    y_centers = 0.5 * (
        y_edges[:-1] + y_edges[1:]
    )
    if use_log_y:
        y_centers = np.power(
            10.0,
            y_centers,
        )

    debug_info["candidate_points"] = [
        {
            "x": float(x_centers[x_index]),
            "y": float(y_centers[y_index]),
            "density": float(smoothed_histogram[x_index, y_index]),
        }
        for x_index, y_index in candidate_indices
        if 0 <= x_index < x_centers.size and 0 <= y_index < y_centers.size
    ]
    debug_info["selected_bin_indices"] = [
        [int(x_index), int(y_index)]
        for x_index, y_index in selected_indices
    ]
    debug_info["selected_count"] = int(len(selected_indices))

    if include_debug_grid:
        debug_info["debug_grid"] = {
            "x_centers": [
                float(value)
                for value in np.asarray(x_centers, dtype=float)
                if np.isfinite(value)
            ],
            "y_centers": [
                float(value)
                for value in np.asarray(y_centers, dtype=float)
                if np.isfinite(value)
            ],
            "smoothed_histogram": np.asarray(
                smoothed_histogram,
                dtype=float,
            ).tolist(),
        }

    peak_positions: list[dict[str, float]] = []

    for x_index, y_index in selected_indices:
        if x_index < 0 or x_index >= x_centers.size:
            continue

        if y_index < 0 or y_index >= y_centers.size:
            continue

        peak_positions.append(
            {
                "x": float(x_centers[x_index]),
                "y": float(y_centers[y_index]),
            }
        )

    return peak_positions, debug_info


def smooth_2d_array(
    *,
    values: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth a 2D array with a simple square moving average.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    resolved_window_size = max(
        1,
        int(window_size),
    )

    if resolved_window_size <= 1:
        return values

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    radius = resolved_window_size // 2

    padded_values = np.pad(
        values,
        pad_width=radius,
        mode="edge",
    )

    smoothed_values = np.zeros_like(
        values,
        dtype=float,
    )

    for row_index in range(values.shape[0]):
        for column_index in range(values.shape[1]):
            local_window = padded_values[
                row_index : row_index + resolved_window_size,
                column_index : column_index + resolved_window_size,
            ]

            smoothed_values[row_index, column_index] = float(
                np.mean(local_window)
            )

    return smoothed_values


def find_local_maxima_2d_indices(
    *,
    values: np.ndarray,
) -> list[tuple[int, int]]:
    """
    Find local maxima in a 2D array.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    maxima_indices: list[tuple[int, int]] = []

    if values.shape[0] < 3 or values.shape[1] < 3:
        return maxima_indices

    for row_index in range(
        1,
        values.shape[0] - 1,
    ):
        for column_index in range(
            1,
            values.shape[1] - 1,
        ):
            center_value = values[
                row_index,
                column_index,
            ]

            local_window = values[
                row_index - 1 : row_index + 2,
                column_index - 1 : column_index + 2,
            ]

            if center_value <= 0:
                continue

            if center_value >= np.max(
                local_window,
            ):
                maxima_indices.append(
                    (
                        row_index,
                        column_index,
                    )
                )

    return maxima_indices


def select_separated_peak_indices(
    *,
    candidate_indices: list[tuple[int, int]],
    values: np.ndarray,
    peak_count: int,
    minimum_separation_bins: int,
) -> list[tuple[int, int]]:
    """
    Select strongest candidates while enforcing a minimum separation.
    """
    selected_indices: list[tuple[int, int]] = []

    for candidate_index in candidate_indices:
        if len(selected_indices) >= int(peak_count):
            break

        candidate_is_far_enough = True

        for selected_index in selected_indices:
            separation = np.hypot(
                float(candidate_index[0] - selected_index[0]),
                float(candidate_index[1] - selected_index[1]),
            )

            if separation < float(minimum_separation_bins):
                candidate_is_far_enough = False
                break

        if not candidate_is_far_enough:
            continue

        selected_indices.append(
            candidate_index,
        )

    return selected_indices


PROCESS = Automatic2DPeakProcess()
