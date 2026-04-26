# -*- coding: utf-8 -*-

from typing import Any
import logging

import numpy as np

from .base import BasePeakProcess
from .base import PeakProcessResult
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class Automatic2DPeakProcess(BasePeakProcess):
    """
    Automatic 2D peak detection process.

    The user selects an x detector channel and a y detector channel. The process
    builds a 2D histogram and detects local maxima in that histogram.

    The graph receives all detected 2D points. The calibration table receives
    the x coordinates through the page specific adapter.
    """

    process_name = "2D automatic detection"
    process_label = "2D automatic detection"
    graph_type = "2d_scatter"
    sort_order = 40

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

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
                "default_value": 3,
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
                "default_value": 160,
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
                "default_value": 5,
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
                "default_value": 8,
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
            default=3,
            minimum=1,
            maximum=100,
        )

        histogram_bins = resolve_integer_setting(
            settings=process_settings,
            name="histogram_bins",
            default=160,
            minimum=20,
            maximum=1000,
        )

        smoothing_window = resolve_integer_setting(
            settings=process_settings,
            name="smoothing_window",
            default=5,
            minimum=1,
            maximum=31,
        )

        minimum_separation_bins = resolve_integer_setting(
            settings=process_settings,
            name="minimum_separation_bins",
            default=8,
            minimum=1,
            maximum=100,
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

        detected_peak_positions = find_2d_histogram_peak_positions(
            x_values=x_values,
            y_values=y_values,
            peak_count=peak_count,
            histogram_bins=histogram_bins,
            smoothing_window=smoothing_window,
            minimum_separation_bins=minimum_separation_bins,
        )

        detected_peak_positions = self.deduplicate_2d_peak_positions(
            peak_positions=detected_peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=detected_peak_positions,
        )

        status = (
            f"Detected {len(detected_peak_positions)} automatic 2D peak(s)."
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
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
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
        }


def find_2d_histogram_peak_positions(
    *,
    x_values: Any,
    y_values: Any,
    peak_count: int,
    histogram_bins: int,
    smoothing_window: int,
    minimum_separation_bins: int,
) -> list[dict[str, float]]:
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

    finite_mask = np.isfinite(x_values) & np.isfinite(y_values)

    x_values = x_values[finite_mask]
    y_values = y_values[finite_mask]

    if x_values.size == 0 or y_values.size == 0:
        return []

    x_lower, x_upper = np.quantile(
        x_values,
        [
            0.001,
            0.999,
        ],
    )

    y_lower, y_upper = np.quantile(
        y_values,
        [
            0.001,
            0.999,
        ],
    )

    range_mask = (
        (x_values >= x_lower)
        & (x_values <= x_upper)
        & (y_values >= y_lower)
        & (y_values <= y_upper)
    )

    x_values = x_values[range_mask]
    y_values = y_values[range_mask]

    if x_values.size == 0 or y_values.size == 0:
        return []

    histogram, x_edges, y_edges = np.histogram2d(
        x_values,
        y_values,
        bins=int(histogram_bins),
    )

    if histogram.size == 0:
        return []

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

    y_centers = 0.5 * (
        y_edges[:-1] + y_edges[1:]
    )

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

    return peak_positions


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


def resolve_integer_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve an integer process setting from a setting dictionary.
    """
    return resolve_integer_value(
        value=settings.get(
            name,
        ),
        default=default,
        minimum=minimum,
        maximum=maximum,
    )


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
        resolved_value = int(
            value,
        )

    except (TypeError, ValueError):
        resolved_value = int(
            default,
        )

    resolved_value = max(
        int(minimum),
        resolved_value,
    )

    resolved_value = min(
        int(maximum),
        resolved_value,
    )

    return resolved_value


PROCESS = Automatic2DPeakProcess()