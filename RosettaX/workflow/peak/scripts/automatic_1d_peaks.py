# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np

from .base import BasePeakProcess
from .base import PeakProcessResult
from RosettaX.utils.io import column_copy

logger = logging.getLogger(__name__)


class Automatic1DPeaksProcess(BasePeakProcess):
    """
    Automatic 1D peak detection process.

    The user selects one detector channel and chooses how many peaks to detect.

    The graph receives the detected peak positions. The calibration table
    receives the current detection result through new_peak_positions.

    The peak detection method uses a smoothed histogram with prominence based
    local maxima. For positive skewed data, the detector works in log10 space
    and maps the detected centers back to the original scale.
    """

    process_name = "1D automatic peaks"
    process_label = "1D automatic peaks"
    graph_type = "1d_histogram"
    sort_order = 20

    supports_manual_click = False
    supports_clear = False
    supports_automatic_action = True
    force_graph_visible = False

    dropdown_option_height_px = 50
    dropdown_menu_max_height_px = 500

    default_peak_count = 3
    default_histogram_bin_count = 512
    default_smoothing_window_fraction = 0.012
    default_minimum_prominence_fraction = 0.035
    default_minimum_distance_fraction = 0.035

    def get_required_detector_channels(self) -> list[str]:
        """
        Return detector channels required by this process.

        Returns
        -------
        list[str]
            Required channel names.
        """
        return [
            "primary",
        ]

    def build_controls(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build Dash controls for automatic 1D peak detection.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Process controls.
        """
        return dash.html.Div(
            [
                self._build_detector_dropdown_block(
                    ids=ids,
                    label="Detector channel",
                    channel_name="primary",
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_peak_count_block(ids=ids),
                self._build_vertical_spacer(height_px=16),
                self._build_action_row(ids=ids),
            ],
            id=ids.process_controls_container(
                process_name=self.process_name,
            ),
            style={
                "display": "none",
                "width": "100%",
                "maxWidth": "100%",
            },
        )

    def _build_vertical_spacer(
        self,
        *,
        height_px: int,
    ) -> dash.html.Div:
        """
        Build a vertical spacer.

        Parameters
        ----------
        height_px:
            Spacer height in pixels.

        Returns
        -------
        dash.html.Div
            Spacer.
        """
        return dash.html.Div(
            style={
                "height": f"{height_px}px",
            },
        )

    def _build_detector_dropdown_block(
        self,
        *,
        ids: Any,
        label: str,
        channel_name: str,
    ) -> dash.html.Div:
        """
        Build one full-width detector dropdown block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        label:
            Display label.

        channel_name:
            Logical detector channel name.

        Returns
        -------
        dash.html.Div
            Detector dropdown block.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    label,
                    style={
                        "marginBottom": "6px",
                        "fontWeight": 500,
                    },
                ),
                dash.dcc.Dropdown(
                    id=ids.process_detector_dropdown(
                        process_name=self.process_name,
                        channel_name=channel_name,
                    ),
                    placeholder="Select detector channel",
                    optionHeight=self.dropdown_option_height_px,
                    maxHeight=self.dropdown_menu_max_height_px,
                    searchable=True,
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                    style={
                        "width": "100%",
                    },
                ),
            ],
            style={
                "width": "100%",
                "maxWidth": "100%",
                "display": "block",
            },
        )

    def _build_peak_count_block(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build the peak count input block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Peak count input block.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    "Number of peaks to look for",
                    style={
                        "marginBottom": "6px",
                        "fontWeight": 500,
                    },
                ),
                dash.dcc.Input(
                    id=ids.peak_count_input,
                    type="number",
                    min=1,
                    step=1,
                    value=self.default_peak_count,
                    debounce=True,
                    persistence=True,
                    persistence_type="session",
                    style={
                        "width": "140px",
                    },
                ),
            ],
            style={
                "width": "100%",
                "display": "block",
            },
        )

    def _build_action_row(
        self,
        *,
        ids: Any,
    ) -> dash.html.Div:
        """
        Build action controls and status output.

        Parameters
        ----------
        ids:
            Peak section id factory.

        Returns
        -------
        dash.html.Div
            Action row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Find peaks",
                    id=ids.process_action_button(
                        process_name=self.process_name,
                        action_name="run",
                    ),
                    n_clicks=0,
                    color="secondary",
                    outline=True,
                    size="sm",
                ),
                self.build_status_component(
                    ids=ids,
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "flexWrap": "wrap",
                "width": "100%",
            },
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
        Run automatic 1D peak detection.

        Parameters
        ----------
        backend:
            Backend compatible with the selected page.

        detector_channels:
            Mapping from channel name to selected detector column.

        peak_count:
            Number of peaks to find.

        max_events_for_analysis:
            Maximum number of events to use.

        Returns
        -------
        Optional[PeakProcessResult]
            Peak process result, or None.
        """
        detector_column = detector_channels.get("primary")

        if backend is None:
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Backend is not initialized.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        if detector_column is None or str(detector_column).strip() == "":
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a detector first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        resolved_peak_count = self.resolve_peak_count(
            peak_count,
        )

        values = self.read_detector_values(
            backend=backend,
            detector_column=str(detector_column),
            max_events_for_analysis=max_events_for_analysis,
        )

        peak_positions = self.estimate_peak_positions(
            values=values,
            peak_count=resolved_peak_count,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
        )

        logger.debug(
            "Automatic 1D detected peak_positions=%r detector_column=%r "
            "peak_count=%r max_events_for_analysis=%r",
            peak_positions,
            detector_column,
            resolved_peak_count,
            max_events_for_analysis,
        )

        status = (
            f"Detected {len(peak_positions)} peak(s)."
            if peak_positions
            else "No peaks detected."
        )

        return PeakProcessResult(
            peak_positions=peak_positions,
            peak_lines_payload=peak_lines_payload,
            status=status,
            new_peak_positions=[
                float(value)
                for value in peak_positions
            ],
            clear_existing_table_peaks=False,
        )

    def resolve_peak_count(
        self,
        peak_count: Any,
    ) -> int:
        """
        Resolve the requested number of peaks.

        Parameters
        ----------
        peak_count:
            Raw peak count value.

        Returns
        -------
        int
            Resolved peak count.
        """
        try:
            resolved_peak_count = int(peak_count)

        except Exception:
            resolved_peak_count = self.default_peak_count

        return max(
            1,
            min(
                100,
                resolved_peak_count,
            ),
        )

    def read_detector_values(
        self,
        *,
        backend: Any,
        detector_column: str,
        max_events_for_analysis: int,
    ) -> np.ndarray:
        """
        Read detector values from a backend.

        The preferred backend API is column_copy. If absent, the method falls
        back to build_histogram and uses the values stored in the histogram
        result.

        Parameters
        ----------
        backend:
            Backend object.

        detector_column:
            Detector column name.

        max_events_for_analysis:
            Maximum number of events.

        Returns
        -------
        np.ndarray
            Detector values.
        """
        values = column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(detector_column),
            dtype=float,
            n=int(max_events_for_analysis),
        )

        return np.asarray(
            values,
            dtype=float,
        ).reshape(-1)

    def estimate_peak_positions(
        self,
        *,
        values: np.ndarray,
        peak_count: int,
    ) -> list[float]:
        """
        Estimate peak positions from one dimensional event values.

        Parameters
        ----------
        values:
            Detector values.

        peak_count:
            Maximum number of peaks to return.

        Returns
        -------
        list[float]
            Estimated peak positions in original detector units.
        """
        finite_values = self.prepare_finite_values(
            values,
        )

        if finite_values.size == 0:
            return []

        working_values, inverse_transform = self.build_peak_detection_axis(
            finite_values,
        )

        if working_values.size == 0:
            return []

        counts, bin_edges = np.histogram(
            working_values,
            bins=self.default_histogram_bin_count,
        )

        if counts.size == 0:
            return []

        smoothed_counts = self.smooth_histogram_counts(
            counts=counts,
            window_fraction=self.default_smoothing_window_fraction,
        )

        peak_indices = self.find_prominent_peak_indices(
            counts=smoothed_counts,
            peak_count=peak_count,
            minimum_prominence_fraction=self.default_minimum_prominence_fraction,
            minimum_distance_fraction=self.default_minimum_distance_fraction,
        )

        if peak_indices.size == 0:
            return []

        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        peak_positions_working_axis = bin_centers[peak_indices]
        peak_positions = inverse_transform(
            peak_positions_working_axis,
        )

        peak_positions = np.asarray(
            peak_positions,
            dtype=float,
        )

        peak_positions = peak_positions[np.isfinite(peak_positions)]
        peak_positions = np.sort(peak_positions)

        return [
            float(value)
            for value in peak_positions[: int(peak_count)]
        ]

    def prepare_finite_values(
        self,
        values: np.ndarray,
    ) -> np.ndarray:
        """
        Keep finite detector values only.

        Parameters
        ----------
        values:
            Raw detector values.

        Returns
        -------
        np.ndarray
            Finite values.
        """
        values = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)

        return values[np.isfinite(values)]

    def build_peak_detection_axis(
        self,
        values: np.ndarray,
    ) -> tuple[np.ndarray, Any]:
        """
        Build the working axis used for peak detection.

        Positive skewed data are detected in log10 space. Values are converted
        back to the original scale before returning peak positions.

        Parameters
        ----------
        values:
            Finite detector values.

        Returns
        -------
        tuple[np.ndarray, Any]
            Working values and inverse transform callable.
        """
        positive_values = values[values > 0.0]

        if positive_values.size >= max(10, int(0.80 * values.size)):
            working_values = np.log10(
                positive_values,
            )

            return working_values, self.inverse_log10_transform

        return values, self.identity_transform

    def inverse_log10_transform(
        self,
        values: np.ndarray,
    ) -> np.ndarray:
        """
        Convert log10 values back to linear units.

        Parameters
        ----------
        values:
            Values in log10 units.

        Returns
        -------
        np.ndarray
            Values in linear units.
        """
        return np.power(
            10.0,
            values,
        )

    def identity_transform(
        self,
        values: np.ndarray,
    ) -> np.ndarray:
        """
        Return values unchanged.

        Parameters
        ----------
        values:
            Input values.

        Returns
        -------
        np.ndarray
            Same values.
        """
        return np.asarray(
            values,
            dtype=float,
        )

    def smooth_histogram_counts(
        self,
        *,
        counts: np.ndarray,
        window_fraction: float,
    ) -> np.ndarray:
        """
        Smooth histogram counts using a compact Gaussian-like kernel.

        This avoids requiring SciPy while still suppressing bin-scale noise.

        Parameters
        ----------
        counts:
            Histogram counts.

        window_fraction:
            Kernel width as a fraction of the histogram length.

        Returns
        -------
        np.ndarray
            Smoothed counts.
        """
        counts = np.asarray(
            counts,
            dtype=float,
        )

        if counts.size < 3:
            return counts

        half_window_size = max(
            2,
            int(round(counts.size * float(window_fraction))),
        )

        kernel_x = np.arange(
            -half_window_size,
            half_window_size + 1,
            dtype=float,
        )

        sigma = max(
            1.0,
            half_window_size / 2.0,
        )

        kernel = np.exp(
            -0.5 * (kernel_x / sigma) ** 2,
        )

        kernel_sum = float(np.sum(kernel))

        if kernel_sum <= 0.0:
            return counts

        kernel = kernel / kernel_sum

        return np.convolve(
            counts,
            kernel,
            mode="same",
        )

    def find_prominent_peak_indices(
        self,
        *,
        counts: np.ndarray,
        peak_count: int,
        minimum_prominence_fraction: float,
        minimum_distance_fraction: float,
    ) -> np.ndarray:
        """
        Find prominent local maxima in smoothed histogram counts.

        Parameters
        ----------
        counts:
            Smoothed histogram counts.

        peak_count:
            Maximum number of peaks.

        minimum_prominence_fraction:
            Minimum prominence relative to the maximum count.

        minimum_distance_fraction:
            Minimum distance between peaks relative to histogram length.

        Returns
        -------
        np.ndarray
            Selected peak indices.
        """
        counts = np.asarray(
            counts,
            dtype=float,
        )

        if counts.size < 3:
            return np.asarray(
                [],
                dtype=int,
            )

        maximum_count = float(
            np.max(counts),
        )

        if maximum_count <= 0.0:
            return np.asarray(
                [],
                dtype=int,
            )

        candidate_indices = self.find_local_maxima_indices(
            counts=counts,
        )

        if candidate_indices.size == 0:
            return np.asarray(
                [],
                dtype=int,
            )

        prominences = self.estimate_peak_prominences(
            counts=counts,
            candidate_indices=candidate_indices,
        )

        minimum_prominence = maximum_count * float(minimum_prominence_fraction)

        prominence_mask = prominences >= minimum_prominence

        candidate_indices = candidate_indices[prominence_mask]
        prominences = prominences[prominence_mask]

        if candidate_indices.size == 0:
            return np.asarray(
                [],
                dtype=int,
            )

        minimum_distance = max(
            1,
            int(round(counts.size * float(minimum_distance_fraction))),
        )

        selected_indices = self.select_peaks_by_prominence_and_distance(
            candidate_indices=candidate_indices,
            prominences=prominences,
            peak_count=peak_count,
            minimum_distance=minimum_distance,
        )

        return np.sort(
            selected_indices,
        )

    def find_local_maxima_indices(
        self,
        *,
        counts: np.ndarray,
    ) -> np.ndarray:
        """
        Find local maxima indices in a one dimensional array.

        Parameters
        ----------
        counts:
            Smoothed histogram counts.

        Returns
        -------
        np.ndarray
            Local maximum indices.
        """
        candidate_indices: list[int] = []

        for index in range(1, counts.size - 1):
            if counts[index] > counts[index - 1] and counts[index] >= counts[index + 1]:
                candidate_indices.append(index)

        return np.asarray(
            candidate_indices,
            dtype=int,
        )

    def estimate_peak_prominences(
        self,
        *,
        counts: np.ndarray,
        candidate_indices: np.ndarray,
    ) -> np.ndarray:
        """
        Estimate local peak prominences without SciPy.

        This estimates prominence as the peak height above the larger of the
        nearest left and right valley minima.

        Parameters
        ----------
        counts:
            Smoothed histogram counts.

        candidate_indices:
            Candidate local maximum indices.

        Returns
        -------
        np.ndarray
            Estimated prominences.
        """
        prominences: list[float] = []

        for candidate_index in candidate_indices:
            left_minimum = self.find_left_valley_minimum(
                counts=counts,
                peak_index=int(candidate_index),
            )

            right_minimum = self.find_right_valley_minimum(
                counts=counts,
                peak_index=int(candidate_index),
            )

            baseline = max(
                left_minimum,
                right_minimum,
            )

            prominence = float(counts[int(candidate_index)] - baseline)

            prominences.append(
                max(0.0, prominence),
            )

        return np.asarray(
            prominences,
            dtype=float,
        )

    def find_left_valley_minimum(
        self,
        *,
        counts: np.ndarray,
        peak_index: int,
    ) -> float:
        """
        Find the minimum count between a peak and the previous higher boundary.

        Parameters
        ----------
        counts:
            Smoothed histogram counts.

        peak_index:
            Peak index.

        Returns
        -------
        float
            Left valley minimum.
        """
        peak_height = float(
            counts[peak_index],
        )

        left_index = peak_index

        while left_index > 0 and counts[left_index] <= peak_height:
            left_index -= 1

            if counts[left_index] > peak_height:
                break

        left_slice = counts[left_index: peak_index + 1]

        if left_slice.size == 0:
            return 0.0

        return float(
            np.min(left_slice),
        )

    def find_right_valley_minimum(
        self,
        *,
        counts: np.ndarray,
        peak_index: int,
    ) -> float:
        """
        Find the minimum count between a peak and the next higher boundary.

        Parameters
        ----------
        counts:
            Smoothed histogram counts.

        peak_index:
            Peak index.

        Returns
        -------
        float
            Right valley minimum.
        """
        peak_height = float(
            counts[peak_index],
        )

        right_index = peak_index

        while right_index < counts.size - 1 and counts[right_index] <= peak_height:
            right_index += 1

            if counts[right_index] > peak_height:
                break

        right_slice = counts[peak_index: right_index + 1]

        if right_slice.size == 0:
            return 0.0

        return float(
            np.min(right_slice),
        )

    def select_peaks_by_prominence_and_distance(
        self,
        *,
        candidate_indices: np.ndarray,
        prominences: np.ndarray,
        peak_count: int,
        minimum_distance: int,
    ) -> np.ndarray:
        """
        Select peaks by descending prominence while enforcing minimum distance.

        Parameters
        ----------
        candidate_indices:
            Candidate peak indices.

        prominences:
            Candidate prominences.

        peak_count:
            Maximum number of peaks.

        minimum_distance:
            Minimum distance in histogram bins.

        Returns
        -------
        np.ndarray
            Selected peak indices.
        """
        order = np.argsort(prominences)[::-1]

        selected_indices: list[int] = []

        for ordered_index in order:
            candidate_index = int(
                candidate_indices[int(ordered_index)],
            )

            is_far_enough = all(
                abs(candidate_index - selected_index) >= int(minimum_distance)
                for selected_index in selected_indices
            )

            if not is_far_enough:
                continue

            selected_indices.append(
                candidate_index,
            )

            if len(selected_indices) >= int(peak_count):
                break

        return np.asarray(
            selected_indices,
            dtype=int,
        )

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[float],
    ) -> dict[str, list[Any]]:
        """
        Build the graph annotation payload for detected 1D peaks.

        Parameters
        ----------
        peak_positions:
            Detected peak positions.

        Returns
        -------
        dict[str, list[Any]]
            Peak annotation payload.
        """
        return {
            "positions": [
                float(value)
                for value in peak_positions
            ],
            "labels": [
                f"Peak {index + 1}"
                for index in range(len(peak_positions))
            ],
            "x_positions": [],
            "y_positions": [],
            "points": [],
        }


PROCESS = Automatic1DPeaksProcess()