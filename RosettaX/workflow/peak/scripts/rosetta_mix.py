# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess
from .base import PeakProcessResult
from RosettaX.utils.io import column_copy

logger = logging.getLogger(__name__)


class FluorescenceGuidedScatterPeakProcess(BasePeakProcess):
    """
    Automatic 2D peak process guided by green fluorescence.

    This process is intended for bead mixtures where the graph is shown as:

    - x axis: scattering channel
    - y axis: green fluorescence channel

    The process does not try to find arbitrary 2D density maxima. Instead it:

    1. estimates a fluorescence positive threshold from the green fluorescence channel
    2. estimates the scattering limit of detection from the fluorescence negative background
    3. detects visible scattering peaks above the limit of detection
    4. returns 2D marker positions for display and x values for table insertion
    """

    process_name = "Rosetta"
    process_label = "Rosetta"
    description = (
        "Use the green fluorescence channel to guide automatic detection of "
        "visible peaks in the scattering channel."
    )
    graph_type = "2d_scatter"
    sort_order = 20

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        """
        Return the detector channels required by this process.
        """
        return [
            "scattering",
            "green_fluorescence",
        ]

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return process settings shown in the UI.
        """
        return [
            {
                "name": "peak_count",
                "kind": "integer",
                "label": "Maximum number of scatter peaks",
                "default_value": 6,
                "min_value": 1,
                "max_value": 20,
                "step": 1,
            },
            {
                "name": "fluorescence_background_quantile",
                "kind": "float",
                "label": "Fluorescence background quantile",
                "default_value": 0.995,
                "min_value": 0.90,
                "max_value": 0.9999,
                "step": 0.001,
            },
            {
                "name": "scatter_background_quantile",
                "kind": "float",
                "label": "Scatter background quantile for LOD",
                "default_value": 0.999,
                "min_value": 0.95,
                "max_value": 0.99999,
                "step": 0.001,
            },
            {
                "name": "minimum_peak_fraction",
                "kind": "float",
                "label": "Minimum peak height fraction",
                "default_value": 0.08,
                "min_value": 0.01,
                "max_value": 0.50,
                "step": 0.01,
            },
        ]

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> Optional[PeakProcessResult]:
        """
        Run automatic fluorescence guided scatter peak detection.
        """
        if backend is None:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="The backend is not available.",
                clear_existing_table_peaks=False,
            )

        scattering_column = detector_channels.get(
            "scattering",
        )
        green_fluorescence_column = detector_channels.get(
            "green_fluorescence",
        )

        if not str(scattering_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a scattering channel first.",
                clear_existing_table_peaks=False,
            )

        if not str(green_fluorescence_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a green fluorescence channel first.",
                clear_existing_table_peaks=False,
            )

        resolved_peak_count = resolve_integer(
            value=peak_count,
            default=6,
            minimum=1,
            maximum=20,
        )

        resolved_max_events_for_analysis = resolve_integer(
            value=max_events_for_analysis,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        fluorescence_background_quantile = resolve_float(
            value=process_settings.get("fluorescence_background_quantile"),
            default=0.995,
            minimum=0.90,
            maximum=0.9999,
        )

        scatter_background_quantile = resolve_float(
            value=process_settings.get("scatter_background_quantile"),
            default=0.999,
            minimum=0.95,
            maximum=0.99999,
        )

        minimum_peak_fraction = resolve_float(
            value=process_settings.get("minimum_peak_fraction"),
            default=0.08,
            minimum=0.01,
            maximum=0.50,
        )

        scattering_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(scattering_column),
                dtype=float,
                n=resolved_max_events_for_analysis,
            ),
            dtype=float,
        )

        green_fluorescence_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(green_fluorescence_column),
                dtype=float,
                n=resolved_max_events_for_analysis,
            ),
            dtype=float,
        )

        finite_mask = np.isfinite(scattering_values) & np.isfinite(green_fluorescence_values)

        scattering_values = scattering_values[finite_mask]
        green_fluorescence_values = green_fluorescence_values[finite_mask]

        if scattering_values.size == 0:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="No finite events are available for automatic detection.",
                clear_existing_table_peaks=False,
            )

        fluorescence_positive_threshold = estimate_fluorescence_positive_threshold(
            green_fluorescence_values=green_fluorescence_values,
            fluorescence_background_quantile=fluorescence_background_quantile,
        )

        scattering_limit_of_detection = estimate_scattering_limit_of_detection(
            scattering_values=scattering_values,
            green_fluorescence_values=green_fluorescence_values,
            fluorescence_positive_threshold=fluorescence_positive_threshold,
            scatter_background_quantile=scatter_background_quantile,
        )

        fluorescence_positive_mask = green_fluorescence_values >= fluorescence_positive_threshold
        visible_scattering_mask = (
            fluorescence_positive_mask
            & np.isfinite(scattering_values)
            & (scattering_values > 0.0)
            & (scattering_values >= scattering_limit_of_detection)
        )

        visible_scattering_values = scattering_values[
            visible_scattering_mask
        ]
        visible_green_fluorescence_values = green_fluorescence_values[
            visible_scattering_mask
        ]

        if visible_scattering_values.size < 5:
            peak_lines_payload = {
                "positions": [],
                "x_positions": [],
                "y_positions": [],
                "points": [],
                "labels": [],
                "limit_of_detection_x": float(scattering_limit_of_detection),
            }

            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=peak_lines_payload,
                status=(
                    "No visible scattering peaks were found above the estimated "
                    "limit of detection."
                ),
                clear_existing_table_peaks=False,
            )

        detected_scatter_peak_positions = detect_scattering_peak_positions(
            scattering_values=visible_scattering_values,
            peak_count=resolved_peak_count,
            minimum_peak_fraction=minimum_peak_fraction,
        )

        if not detected_scatter_peak_positions:
            peak_lines_payload = {
                "positions": [],
                "x_positions": [],
                "y_positions": [],
                "points": [],
                "labels": [],
                "limit_of_detection_x": float(scattering_limit_of_detection),
            }

            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=peak_lines_payload,
                status="No distinct scattering peaks could be resolved.",
                clear_existing_table_peaks=False,
            )

        peak_points = build_peak_display_points(
            scattering_values=visible_scattering_values,
            green_fluorescence_values=visible_green_fluorescence_values,
            scatter_peak_positions=detected_scatter_peak_positions,
        )

        labels = [
            f"Scatter peak {index + 1}"
            for index in range(len(peak_points))
        ]

        peak_lines_payload = {
            "positions": [
                float(point["x"])
                for point in peak_points
            ],
            "x_positions": [
                float(point["x"])
                for point in peak_points
            ],
            "y_positions": [
                float(point["y"])
                for point in peak_points
            ],
            "points": [
                {
                    "x": float(point["x"]),
                    "y": float(point["y"]),
                }
                for point in peak_points
            ],
            "labels": labels,
            "limit_of_detection_x": float(scattering_limit_of_detection),
        }

        status = (
            f"Detected {len(peak_points)} scatter peak(s). "
            f"Fluorescence threshold={fluorescence_positive_threshold:.6g}. "
            f"Scatter LOD={scattering_limit_of_detection:.6g}."
        )

        return PeakProcessResult(
            peak_positions=[
                {
                    "x": float(point["x"]),
                    "y": float(point["y"]),
                }
                for point in peak_points
            ],
            peak_lines_payload=peak_lines_payload,
            status=status,
            clear_existing_table_peaks=False,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all detected peaks.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared fluorescence guided scatter peaks.",
            clear_existing_table_peaks=True,
        )

    def build_empty_peak_lines_payload(self) -> dict[str, Any]:
        """
        Build an empty peak payload.
        """
        return {
            "positions": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
            "labels": [],
        }


def resolve_integer(
    *,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve an integer setting.
    """
    try:
        resolved_value = int(value)

    except (TypeError, ValueError):
        resolved_value = int(default)

    resolved_value = max(
        int(minimum),
        min(
            int(maximum),
            int(resolved_value),
        ),
    )

    return resolved_value


def resolve_float(
    *,
    value: Any,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Resolve a floating point setting.
    """
    try:
        resolved_value = float(value)

    except (TypeError, ValueError):
        resolved_value = float(default)

    if not np.isfinite(resolved_value):
        resolved_value = float(default)

    resolved_value = max(
        float(minimum),
        min(
            float(maximum),
            float(resolved_value),
        ),
    )

    return resolved_value


def estimate_fluorescence_positive_threshold(
    *,
    green_fluorescence_values: np.ndarray,
    fluorescence_background_quantile: float,
) -> float:
    """
    Estimate the fluorescence positive threshold.

    The method first tries to find a valley between two fluorescence modes in
    log space. If that fails, it falls back to a high background quantile.
    """
    green_fluorescence_values = np.asarray(
        green_fluorescence_values,
        dtype=float,
    )

    positive_values = green_fluorescence_values[
        np.isfinite(green_fluorescence_values)
        & (green_fluorescence_values > 0.0)
    ]

    if positive_values.size == 0:
        return 0.0

    log_values = np.log10(
        positive_values,
    )

    histogram_bin_count = min(
        256,
        max(
            64,
            int(np.sqrt(log_values.size)),
        ),
    )

    counts, bin_edges = np.histogram(
        log_values,
        bins=histogram_bin_count,
    )

    smoothed_counts = smooth_counts(
        counts=np.asarray(counts, dtype=float),
        window_size=9,
    )

    local_maxima_indices = find_local_maxima_indices(
        values=smoothed_counts,
    )

    if len(local_maxima_indices) >= 2:
        strongest_peak_indices = sorted(
            local_maxima_indices,
            key=lambda index: smoothed_counts[index],
            reverse=True,
        )[:2]

        left_peak_index, right_peak_index = sorted(
            strongest_peak_indices,
        )

        valley_slice = smoothed_counts[
            left_peak_index:right_peak_index + 1
        ]

        if valley_slice.size > 0:
            valley_index = left_peak_index + int(
                np.argmin(valley_slice)
            )

            valley_center = 0.5 * (
                bin_edges[valley_index]
                + bin_edges[valley_index + 1]
            )

            return float(
                10.0 ** valley_center
            )

    return float(
        np.quantile(
            positive_values,
            fluorescence_background_quantile,
        )
    )


def estimate_scattering_limit_of_detection(
    *,
    scattering_values: np.ndarray,
    green_fluorescence_values: np.ndarray,
    fluorescence_positive_threshold: float,
    scatter_background_quantile: float,
) -> float:
    """
    Estimate the scattering limit of detection from the fluorescence negative
    background population.
    """
    scattering_values = np.asarray(
        scattering_values,
        dtype=float,
    )

    green_fluorescence_values = np.asarray(
        green_fluorescence_values,
        dtype=float,
    )

    valid_scattering_mask = np.isfinite(scattering_values) & (scattering_values > 0.0)

    if not np.isfinite(fluorescence_positive_threshold):
        background_scattering_values = scattering_values[
            valid_scattering_mask
        ]

    else:
        fluorescence_negative_mask = green_fluorescence_values < fluorescence_positive_threshold

        background_scattering_values = scattering_values[
            valid_scattering_mask
            & fluorescence_negative_mask
        ]

        if background_scattering_values.size < 32:
            sorted_green_fluorescence_values = np.sort(
                green_fluorescence_values[
                    np.isfinite(green_fluorescence_values)
                ]
            )

            if sorted_green_fluorescence_values.size > 0:
                fallback_threshold_index = int(
                    0.7 * (sorted_green_fluorescence_values.size - 1)
                )

                fallback_threshold = sorted_green_fluorescence_values[
                    fallback_threshold_index
                ]

                background_scattering_values = scattering_values[
                    valid_scattering_mask
                    & (green_fluorescence_values <= fallback_threshold)
                ]

    if background_scattering_values.size == 0:
        valid_scattering_values = scattering_values[
            valid_scattering_mask
        ]

        if valid_scattering_values.size == 0:
            return 0.0

        return float(
            np.quantile(
                valid_scattering_values,
                scatter_background_quantile,
            )
        )

    return float(
        np.quantile(
            background_scattering_values,
            scatter_background_quantile,
        )
    )


def detect_scattering_peak_positions(
    *,
    scattering_values: np.ndarray,
    peak_count: int,
    minimum_peak_fraction: float,
) -> list[float]:
    """
    Detect peaks along the scattering axis.

    Peak detection is done on a one dimensional histogram in log space because
    the actual quantity of interest is the x axis peak location.
    """
    scattering_values = np.asarray(
        scattering_values,
        dtype=float,
    )

    scattering_values = scattering_values[
        np.isfinite(scattering_values)
        & (scattering_values > 0.0)
    ]

    if scattering_values.size == 0:
        return []

    log_scattering_values = np.log10(
        scattering_values,
    )

    histogram_bin_count = min(
        256,
        max(
            64,
            int(np.sqrt(log_scattering_values.size)),
        ),
    )

    counts, bin_edges = np.histogram(
        log_scattering_values,
        bins=histogram_bin_count,
    )

    if counts.size == 0:
        return []

    smoothed_counts = smooth_counts(
        counts=np.asarray(counts, dtype=float),
        window_size=7,
    )

    candidate_peak_indices = find_local_maxima_indices(
        values=smoothed_counts,
    )

    if not candidate_peak_indices:
        candidate_peak_indices = [
            int(index)
            for index in np.argsort(smoothed_counts)[-int(peak_count):]
        ]

    maximum_count = float(
        np.max(smoothed_counts)
    )

    candidate_peak_indices = [
        index
        for index in candidate_peak_indices
        if smoothed_counts[index] >= maximum_count * float(minimum_peak_fraction)
    ]

    if not candidate_peak_indices:
        return []

    selected_peak_indices = select_well_separated_peak_indices(
        candidate_peak_indices=candidate_peak_indices,
        weights=smoothed_counts,
        peak_count=peak_count,
        minimum_index_distance=6,
    )

    log_bin_centers = 0.5 * (
        bin_edges[:-1]
        + bin_edges[1:]
    )

    scatter_peak_positions = [
        float(
            10.0 ** log_bin_centers[index]
        )
        for index in sorted(selected_peak_indices)
        if 0 <= index < log_bin_centers.size
    ]

    return scatter_peak_positions


def build_peak_display_points(
    *,
    scattering_values: np.ndarray,
    green_fluorescence_values: np.ndarray,
    scatter_peak_positions: list[float],
) -> list[dict[str, float]]:
    """
    Build 2D display points for the detected scatter peaks.

    The x position is the detected scatter peak. The y position is the median
    green fluorescence value of nearby events.
    """
    scattering_values = np.asarray(
        scattering_values,
        dtype=float,
    )

    green_fluorescence_values = np.asarray(
        green_fluorescence_values,
        dtype=float,
    )

    valid_mask = (
        np.isfinite(scattering_values)
        & np.isfinite(green_fluorescence_values)
        & (scattering_values > 0.0)
    )

    scattering_values = scattering_values[
        valid_mask
    ]
    green_fluorescence_values = green_fluorescence_values[
        valid_mask
    ]

    if scattering_values.size == 0:
        return []

    log_scattering_values = np.log10(
        scattering_values,
    )

    peak_points: list[dict[str, float]] = []

    for scatter_peak_position in scatter_peak_positions:
        if scatter_peak_position <= 0.0:
            continue

        target_log_scattering = np.log10(
            float(scatter_peak_position)
        )

        local_mask = np.abs(
            log_scattering_values - target_log_scattering
        ) <= 0.05

        if np.count_nonzero(local_mask) >= 5:
            representative_green_fluorescence = np.median(
                green_fluorescence_values[local_mask]
            )

        else:
            nearest_indices = np.argsort(
                np.abs(log_scattering_values - target_log_scattering)
            )[: min(25, log_scattering_values.size)]

            representative_green_fluorescence = np.median(
                green_fluorescence_values[nearest_indices]
            )

        peak_points.append(
            {
                "x": float(scatter_peak_position),
                "y": float(representative_green_fluorescence),
            }
        )

    return peak_points


def select_well_separated_peak_indices(
    *,
    candidate_peak_indices: list[int],
    weights: np.ndarray,
    peak_count: int,
    minimum_index_distance: int,
) -> list[int]:
    """
    Select the strongest peaks while enforcing a minimum separation.
    """
    ordered_candidate_peak_indices = sorted(
        candidate_peak_indices,
        key=lambda index: float(weights[index]),
        reverse=True,
    )

    selected_peak_indices: list[int] = []

    for candidate_peak_index in ordered_candidate_peak_indices:
        if any(
            abs(candidate_peak_index - selected_peak_index) < int(minimum_index_distance)
            for selected_peak_index in selected_peak_indices
        ):
            continue

        selected_peak_indices.append(
            int(candidate_peak_index),
        )

        if len(selected_peak_indices) >= int(peak_count):
            break

    return sorted(
        selected_peak_indices,
    )


def smooth_counts(
    *,
    counts: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth histogram counts with a moving average.
    """
    counts = np.asarray(
        counts,
        dtype=float,
    )

    if counts.size < 3:
        return counts

    resolved_window_size = max(
        3,
        int(window_size),
    )

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    if counts.size < resolved_window_size:
        resolved_window_size = counts.size

        if resolved_window_size % 2 == 0:
            resolved_window_size -= 1

    if resolved_window_size < 3:
        return counts

    kernel = np.ones(
        resolved_window_size,
        dtype=float,
    ) / float(resolved_window_size)

    return np.convolve(
        counts,
        kernel,
        mode="same",
    )


def find_local_maxima_indices(
    *,
    values: np.ndarray,
) -> list[int]:
    """
    Find local maxima in a one dimensional array.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    maxima_indices: list[int] = []

    for index in range(
        1,
        values.size - 1,
    ):
        if values[index] >= values[index - 1] and values[index] >= values[index + 1]:
            maxima_indices.append(
                index,
            )

    return maxima_indices


PROCESS = FluorescenceGuidedScatterPeakProcess()