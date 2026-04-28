# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess, PeakProcessResult
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class SmoothedHistogramProminence1DPeakProcess(BasePeakProcess):
    """
    Smoothed histogram prominence 1D peak registration.

    This process is intended for calibration peak detection when populations may
    have very different event counts.

    The process gates the signal with quantiles, builds a histogram, smooths the
    histogram counts, finds local maxima, filters them by prominence and count,
    then returns peak centers in the original detector units.
    """

    process_name = "Prominence 1D"
    process_label = "Prominence 1D"
    description = (
        "Gate one detector signal with quantiles, smooth the histogram, then "
        "detect local maxima using prominence and minimum distance criteria."
    )
    graph_type = "1d_histogram"
    sort_order = 40

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        """
        Return logical detector channels used by this process.
        """
        return [
            "x_axis",
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user visible detector labels.
        """
        return {
            "x_axis": "Signal channel",
        }

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return configurable process settings.
        """
        return [
            {
                "name": "maximum_peak_count",
                "label": "Max peak count",
                "kind": "integer",
                "default_value": 6,
                "min_value": 1,
                "max_value": 50,
                "step": 1,
                "help": (
                    "Maximum number of peaks returned by the detector. "
                    "The strongest candidates are selected first, then sorted by position. "
                    "Increase this when you expect many bead populations. Decrease it when "
                    "weak shoulders or noise peaks are being returned."
                ),
            },
            {
                "name": "number_of_bins",
                "label": "Detection bins",
                "kind": "integer",
                "default_value": 512,
                "min_value": 32,
                "max_value": 20000,
                "step": 32,
                "help": (
                    "Number of histogram bins used internally for peak detection. "
                    "More bins improve position resolution but make the histogram noisier. "
                    "Fewer bins smooth the distribution but can merge nearby peaks."
                ),
            },
            {
                "name": "smoothing_window_size",
                "label": "Smoothing window",
                "kind": "integer",
                "default_value": 9,
                "min_value": 1,
                "max_value": 501,
                "step": 2,
                "help": (
                    "Moving average window applied to histogram counts before peak detection. "
                    "Increase it to suppress noisy bin to bin fluctuations. Decrease it when "
                    "nearby peaks are being merged or shifted too much."
                ),
            },
            {
                "name": "minimum_prominence_fraction",
                "label": "Min prominence fraction",
                "kind": "float",
                "default_value": 0.03,
                "min_value": 0.0,
                "max_value": 1.0,
                "step": 0.005,
                "help": (
                    "Minimum peak prominence expressed as a fraction of the highest smoothed "
                    "histogram count. Prominence measures how much a peak rises above its "
                    "surrounding valleys. Increase it to reject weak shoulders and noise. "
                    "Decrease it to recover small populations."
                ),
            },
            {
                "name": "minimum_count_fraction",
                "label": "Min count fraction",
                "kind": "float",
                "default_value": 0.01,
                "min_value": 0.0,
                "max_value": 1.0,
                "step": 0.005,
                "help": (
                    "Minimum smoothed count at a peak, expressed as a fraction of the highest "
                    "smoothed histogram count. This rejects very low density maxima even if "
                    "their local prominence is nonzero. Increase it to ignore tiny populations "
                    "or noise. Decrease it when true calibration peaks have few events."
                ),
            },
            {
                "name": "minimum_distance_bins",
                "label": "Min distance bins",
                "kind": "integer",
                "default_value": 8,
                "min_value": 1,
                "max_value": 1000,
                "step": 1,
                "help": (
                    "Minimum separation between accepted peaks in histogram bin units. "
                    "If two candidate peaks are closer than this, only the more prominent "
                    "one is kept. Increase it to merge nearby shoulders. Decrease it to allow "
                    "closely spaced populations."
                ),
            },
            {
                "name": "x_axis_lower_gate_quantile",
                "label": "Lower gate quantile",
                "kind": "float",
                "default_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
                "help": (
                    "Lower quantile used to remove the lowest signal values before detection. "
                    "A value of 0.0 keeps the full lower tail. Increase it to remove low end "
                    "background, debris, or extreme outliers before building the histogram."
                ),
            },
            {
                "name": "x_axis_upper_gate_quantile",
                "label": "Upper gate quantile",
                "kind": "float",
                "default_value": 1.0,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
                "help": (
                    "Upper quantile used to remove the highest signal values before detection. "
                    "A value of 1.0 keeps the full upper tail. Decrease it to remove saturated "
                    "events, rare extreme outliers, or very bright contaminants."
                ),
            },
            {
                "name": "use_log_transform",
                "label": "Log transform",
                "kind": "select",
                "default_value": "yes",
                "options": [
                    {
                        "label": "Yes",
                        "value": "yes",
                    },
                    {
                        "label": "No",
                        "value": "no",
                    },
                ],
                "help": (
                    "Detect peaks in log10 signal space instead of linear signal space. "
                    "Use log transform for cytometry signals spanning several orders of "
                    "magnitude. Disable it when values can be zero or negative, or when "
                    "the relevant populations are better separated linearly."
                ),
            },
        ]

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        process_settings: dict[str, Any],
        peak_count: Any = None,
        max_events_for_analysis: Any = None,
        max_events_for_plots: Any = None,
        **_kwargs: Any,
    ) -> Optional[PeakProcessResult]:
        """
        Run smoothed histogram prominence peak detection.
        """
        if backend is None or not hasattr(backend, "fcs_file_path"):
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="The backend does not expose fcs_file_path.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        x_axis_column = detector_channels.get(
            "x_axis",
        )

        if not str(x_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a signal channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        settings = SmoothedHistogramProminence1DSettings.from_process_settings(
            process_settings=process_settings,
            peak_count=peak_count,
        )

        maximum_events = resolve_integer_value(
            value=max_events_for_analysis
            if max_events_for_analysis is not None
            else max_events_for_plots,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        x_axis_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(x_axis_column),
                dtype=float,
                n=maximum_events,
            ),
            dtype=float,
        )

        result = compute_smoothed_histogram_prominence_peaks(
            x_axis_values=x_axis_values,
            settings=settings,
        )

        peak_positions = deduplicate_1d_peak_positions(
            peak_positions=result.peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
            prominences=result.prominences,
            peak_counts=result.peak_counts,
            x_axis_lower_gate=result.x_axis_lower_gate,
            x_axis_upper_gate=result.x_axis_upper_gate,
        )

        status = (
            f"Smoothed histogram prominence found {len(peak_positions)} peak(s) "
            f"from {result.gated_event_count} gated event(s). "
            f"Gate=[{result.x_axis_lower_gate:.6g}, {result.x_axis_upper_gate:.6g}]."
        )

        logger.debug(
            "Smoothed histogram prominence completed with x_axis_column=%r "
            "settings=%r gated_event_count=%r peak_positions=%r prominences=%r",
            x_axis_column,
            settings,
            result.gated_event_count,
            peak_positions,
            result.prominences,
        )

        return PeakProcessResult(
            peak_positions=peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=peak_positions,
            clear_existing_table_peaks=False,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear graph overlays without modifying the calibration table.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared smoothed histogram prominence graph overlays. Table values were preserved.",
            new_peak_positions=[],
            clear_existing_table_peaks=False,
        )

    def build_empty_peak_lines_payload(self) -> dict[str, Any]:
        """
        Build an empty peak payload.
        """
        return {
            "positions": [],
            "x_positions": [],
            "points": [],
            "labels": [],
            "prominences": [],
            "peak_counts": [],
            "x_axis_lower_gate": 0.0,
            "x_axis_upper_gate": 0.0,
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
        prominences: list[float],
        peak_counts: list[float],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
    ) -> dict[str, Any]:
        """
        Build graph annotation payload.
        """
        labels = [
            f"Peak {index + 1} | prominence={prominences[index]:.4g}"
            if index < len(prominences)
            else f"Peak {index + 1}"
            for index in range(len(peak_positions))
        ]

        return {
            "positions": [
                float(position)
                for position in peak_positions
            ],
            "x_positions": [
                float(position)
                for position in peak_positions
            ],
            "points": [
                {
                    "x": float(position),
                }
                for position in peak_positions
            ],
            "labels": labels,
            "prominences": [
                float(prominence)
                for prominence in prominences
            ],
            "peak_counts": [
                float(peak_count)
                for peak_count in peak_counts
            ],
            "x_axis_lower_gate": float(x_axis_lower_gate),
            "x_axis_upper_gate": float(x_axis_upper_gate),
        }


class SmoothedHistogramProminence1DSettings:
    """
    Settings for smoothed histogram prominence 1D peak detection.
    """

    def __init__(
        self,
        *,
        maximum_peak_count: int,
        number_of_bins: int,
        smoothing_window_size: int,
        minimum_prominence_fraction: float,
        minimum_count_fraction: float,
        minimum_distance_bins: int,
        x_axis_lower_gate_quantile: float,
        x_axis_upper_gate_quantile: float,
        use_log_transform: bool,
    ) -> None:
        self.maximum_peak_count = maximum_peak_count
        self.number_of_bins = number_of_bins
        self.smoothing_window_size = smoothing_window_size
        self.minimum_prominence_fraction = minimum_prominence_fraction
        self.minimum_count_fraction = minimum_count_fraction
        self.minimum_distance_bins = minimum_distance_bins
        self.x_axis_lower_gate_quantile = x_axis_lower_gate_quantile
        self.x_axis_upper_gate_quantile = x_axis_upper_gate_quantile
        self.use_log_transform = use_log_transform

    @classmethod
    def from_process_settings(
        cls,
        *,
        process_settings: dict[str, Any],
        peak_count: Any = None,
    ) -> "SmoothedHistogramProminence1DSettings":
        """
        Build settings from Dash process settings.
        """
        maximum_peak_count = resolve_integer_setting(
            settings=process_settings,
            name="maximum_peak_count",
            default=6,
            minimum=1,
            maximum=50,
        )

        if peak_count is not None:
            maximum_peak_count = resolve_integer_value(
                value=peak_count,
                default=maximum_peak_count,
                minimum=1,
                maximum=50,
            )

        x_axis_lower_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="x_axis_lower_gate_quantile",
            default=0.0,
            minimum=0.0,
            maximum=0.499,
        )

        x_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="x_axis_upper_gate_quantile",
            default=1.0,
            minimum=0.501,
            maximum=1.0,
        )

        if x_axis_lower_gate_quantile >= x_axis_upper_gate_quantile:
            x_axis_lower_gate_quantile = 0.0
            x_axis_upper_gate_quantile = 1.0

        return cls(
            maximum_peak_count=maximum_peak_count,
            number_of_bins=resolve_integer_setting(
                settings=process_settings,
                name="number_of_bins",
                default=512,
                minimum=32,
                maximum=20000,
            ),
            smoothing_window_size=resolve_integer_setting(
                settings=process_settings,
                name="smoothing_window_size",
                default=9,
                minimum=1,
                maximum=501,
            ),
            minimum_prominence_fraction=resolve_float_setting(
                settings=process_settings,
                name="minimum_prominence_fraction",
                default=0.03,
                minimum=0.0,
                maximum=1.0,
            ),
            minimum_count_fraction=resolve_float_setting(
                settings=process_settings,
                name="minimum_count_fraction",
                default=0.01,
                minimum=0.0,
                maximum=1.0,
            ),
            minimum_distance_bins=resolve_integer_setting(
                settings=process_settings,
                name="minimum_distance_bins",
                default=8,
                minimum=1,
                maximum=1000,
            ),
            x_axis_lower_gate_quantile=x_axis_lower_gate_quantile,
            x_axis_upper_gate_quantile=x_axis_upper_gate_quantile,
            use_log_transform=resolve_yes_no_setting(
                settings=process_settings,
                name="use_log_transform",
                default=True,
            ),
        )

    def __repr__(self) -> str:
        """
        Return a compact debug representation.
        """
        return (
            "SmoothedHistogramProminence1DSettings("
            f"maximum_peak_count={self.maximum_peak_count!r}, "
            f"number_of_bins={self.number_of_bins!r}, "
            f"smoothing_window_size={self.smoothing_window_size!r}, "
            f"minimum_prominence_fraction={self.minimum_prominence_fraction!r}, "
            f"minimum_count_fraction={self.minimum_count_fraction!r}, "
            f"minimum_distance_bins={self.minimum_distance_bins!r}, "
            f"x_axis_lower_gate_quantile={self.x_axis_lower_gate_quantile!r}, "
            f"x_axis_upper_gate_quantile={self.x_axis_upper_gate_quantile!r}, "
            f"use_log_transform={self.use_log_transform!r})"
        )


class SmoothedHistogramProminence1DResult:
    """
    Result from smoothed histogram prominence peak detection.
    """

    def __init__(
        self,
        *,
        peak_positions: list[float],
        prominences: list[float],
        peak_counts: list[float],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        gated_event_count: int,
    ) -> None:
        self.peak_positions = peak_positions
        self.prominences = prominences
        self.peak_counts = peak_counts
        self.x_axis_lower_gate = x_axis_lower_gate
        self.x_axis_upper_gate = x_axis_upper_gate
        self.gated_event_count = gated_event_count


def compute_smoothed_histogram_prominence_peaks(
    *,
    x_axis_values: Any,
    settings: SmoothedHistogramProminence1DSettings,
) -> SmoothedHistogramProminence1DResult:
    """
    Compute 1D peaks from a smoothed histogram and prominence criteria.
    """
    original_values, transformed_values = prepare_axis_values(
        x_axis_values=x_axis_values,
        use_log_transform=settings.use_log_transform,
    )

    if original_values.size == 0:
        return build_empty_result()

    x_axis_lower_gate, x_axis_upper_gate = compute_quantile_gate(
        values=original_values,
        lower_quantile=settings.x_axis_lower_gate_quantile,
        upper_quantile=settings.x_axis_upper_gate_quantile,
    )

    gate_mask = (
        (original_values >= x_axis_lower_gate)
        & (original_values <= x_axis_upper_gate)
    )

    gated_original_values = original_values[
        gate_mask
    ]

    gated_transformed_values = transformed_values[
        gate_mask
    ]

    if gated_original_values.size == 0:
        return SmoothedHistogramProminence1DResult(
            peak_positions=[],
            prominences=[],
            peak_counts=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            gated_event_count=0,
        )

    counts, bin_edges = np.histogram(
        gated_transformed_values,
        bins=int(settings.number_of_bins),
    )

    counts = np.asarray(
        counts,
        dtype=float,
    )

    bin_centers = 0.5 * (
        bin_edges[:-1]
        + bin_edges[1:]
    )

    smoothed_counts = smooth_counts(
        counts=counts,
        window_size=settings.smoothing_window_size,
    )

    candidate_indices = find_local_maxima_indices(
        values=smoothed_counts,
    )

    maximum_count = float(
        np.max(smoothed_counts),
    ) if smoothed_counts.size else 0.0

    minimum_prominence = settings.minimum_prominence_fraction * maximum_count
    minimum_count = settings.minimum_count_fraction * maximum_count

    candidates = []

    for candidate_index in candidate_indices:
        prominence = compute_peak_prominence(
            values=smoothed_counts,
            peak_index=candidate_index,
        )

        peak_count = float(
            smoothed_counts[candidate_index],
        )

        if prominence < minimum_prominence:
            continue

        if peak_count < minimum_count:
            continue

        candidates.append(
            PeakCandidate(
                index=int(candidate_index),
                transformed_position=float(bin_centers[candidate_index]),
                count=peak_count,
                prominence=float(prominence),
            )
        )

    candidates = enforce_minimum_distance_between_candidates(
        candidates=candidates,
        minimum_distance_bins=settings.minimum_distance_bins,
    )

    candidates = sorted(
        candidates,
        key=lambda candidate: candidate.prominence,
        reverse=True,
    )

    candidates = candidates[
        : int(settings.maximum_peak_count)
    ]

    candidates = sorted(
        candidates,
        key=lambda candidate: candidate.transformed_position,
    )

    peak_positions = [
        inverse_transform_position(
            transformed_position=candidate.transformed_position,
            use_log_transform=settings.use_log_transform,
        )
        for candidate in candidates
    ]

    prominences = [
        float(candidate.prominence)
        for candidate in candidates
    ]

    peak_counts = [
        float(candidate.count)
        for candidate in candidates
    ]

    return SmoothedHistogramProminence1DResult(
        peak_positions=peak_positions,
        prominences=prominences,
        peak_counts=peak_counts,
        x_axis_lower_gate=float(x_axis_lower_gate),
        x_axis_upper_gate=float(x_axis_upper_gate),
        gated_event_count=int(gated_original_values.size),
    )


class PeakCandidate:
    """
    One local maximum candidate from the smoothed histogram.
    """

    def __init__(
        self,
        *,
        index: int,
        transformed_position: float,
        count: float,
        prominence: float,
    ) -> None:
        self.index = int(index)
        self.transformed_position = float(transformed_position)
        self.count = float(count)
        self.prominence = float(prominence)


def prepare_axis_values(
    *,
    x_axis_values: Any,
    use_log_transform: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert input values to finite original and transformed arrays.
    """
    original_values = np.asarray(
        x_axis_values,
        dtype=float,
    ).reshape(-1)

    finite_mask = np.isfinite(
        original_values,
    )

    if use_log_transform:
        finite_mask = finite_mask & (
            original_values > 0.0
        )

    original_values = original_values[
        finite_mask
    ]

    if use_log_transform:
        transformed_values = np.log10(
            original_values,
        )
    else:
        transformed_values = original_values.copy()

    return (
        original_values,
        transformed_values,
    )


def inverse_transform_position(
    *,
    transformed_position: float,
    use_log_transform: bool,
) -> float:
    """
    Convert a transformed peak position back to original detector units.
    """
    if use_log_transform:
        return float(
            10.0 ** float(transformed_position),
        )

    return float(
        transformed_position,
    )


def compute_quantile_gate(
    *,
    values: np.ndarray,
    lower_quantile: float,
    upper_quantile: float,
) -> tuple[float, float]:
    """
    Compute lower and upper gate thresholds from quantiles.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if values.size == 0:
        return 0.0, 0.0

    lower_gate, upper_gate = np.quantile(
        values,
        [
            lower_quantile,
            upper_quantile,
        ],
    )

    return (
        float(lower_gate),
        float(upper_gate),
    )


def smooth_counts(
    *,
    counts: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth histogram counts using a moving average.
    """
    counts = np.asarray(
        counts,
        dtype=float,
    )

    if counts.size < 3:
        return counts

    resolved_window_size = max(
        1,
        int(window_size),
    )

    if resolved_window_size <= 1:
        return counts

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    if resolved_window_size > counts.size:
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
    Find local maxima indices in a one dimensional signal.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    if values.size < 3:
        return []

    maxima_indices: list[int] = []

    for index in range(
        1,
        values.size - 1,
    ):
        if values[index] >= values[index - 1] and values[index] >= values[index + 1]:
            if values[index] > values[index - 1] or values[index] > values[index + 1]:
                maxima_indices.append(
                    int(index),
                )

    return maxima_indices


def compute_peak_prominence(
    *,
    values: np.ndarray,
    peak_index: int,
) -> float:
    """
    Estimate peak prominence from the nearest lower valleys on both sides.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    if values.size == 0:
        return 0.0

    peak_index = int(
        peak_index,
    )

    peak_value = float(
        values[peak_index],
    )

    left_minimum = peak_value

    for index in range(
        peak_index,
        -1,
        -1,
    ):
        left_minimum = min(
            left_minimum,
            float(values[index]),
        )

        if index < peak_index and values[index] > peak_value:
            break

    right_minimum = peak_value

    for index in range(
        peak_index,
        values.size,
    ):
        right_minimum = min(
            right_minimum,
            float(values[index]),
        )

        if index > peak_index and values[index] > peak_value:
            break

    reference_valley = max(
        left_minimum,
        right_minimum,
    )

    return max(
        0.0,
        peak_value - reference_valley,
    )


def enforce_minimum_distance_between_candidates(
    *,
    candidates: list[PeakCandidate],
    minimum_distance_bins: int,
) -> list[PeakCandidate]:
    """
    Keep the strongest candidates while enforcing a minimum bin distance.
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: candidate.prominence,
        reverse=True,
    )

    selected_candidates: list[PeakCandidate] = []

    for candidate in sorted_candidates:
        is_too_close = any(
            abs(candidate.index - selected_candidate.index) < int(minimum_distance_bins)
            for selected_candidate in selected_candidates
        )

        if is_too_close:
            continue

        selected_candidates.append(
            candidate,
        )

    return selected_candidates


def build_empty_result() -> SmoothedHistogramProminence1DResult:
    """
    Build an empty result.
    """
    return SmoothedHistogramProminence1DResult(
        peak_positions=[],
        prominences=[],
        peak_counts=[],
        x_axis_lower_gate=0.0,
        x_axis_upper_gate=0.0,
        gated_event_count=0,
    )


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
        value=settings.get(
            name,
        ),
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
        resolved_value = float(
            settings.get(
                name,
                default,
            )
        )

    except (TypeError, ValueError):
        resolved_value = float(
            default,
        )

    if not np.isfinite(
        resolved_value,
    ):
        resolved_value = float(
            default,
        )

    resolved_value = max(
        float(minimum),
        resolved_value,
    )

    resolved_value = min(
        float(maximum),
        resolved_value,
    )

    return resolved_value


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


def resolve_yes_no_setting(
    *,
    settings: dict[str, Any],
    name: str,
    default: bool,
) -> bool:
    """
    Resolve a yes or no setting.
    """
    value = settings.get(
        name,
        None,
    )

    if value is None:
        return bool(
            default,
        )

    if isinstance(value, bool):
        return value

    return str(
        value,
    ).strip().lower() in (
        "yes",
        "true",
        "1",
        "on",
        "enabled",
    )


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
            x_value = float(
                peak_position,
            )

        except (TypeError, ValueError):
            continue

        if not np.isfinite(
            x_value,
        ):
            continue

        key = round(
            x_value,
            int(decimal_places),
        )

        if key in seen_keys:
            continue

        seen_keys.add(
            key,
        )

        unique_peak_positions.append(
            x_value,
        )

    return unique_peak_positions


PROCESS = SmoothedHistogramProminence1DPeakProcess()