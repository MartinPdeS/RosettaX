# -*- coding: utf-8 -*-

import json
import logging
from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np

from .base import BasePeakProcess, PeakProcessResult
from .base import (
    filter_edge_artifact_values,
    resolve_edge_artifact_filter_enabled,
    resolve_float_setting,
    resolve_integer_setting,
    resolve_integer_value,
)
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

    process_name = "Automatic 1D"
    process_label = "Automatic 1D"
    graph_type = "1d_histogram"
    sort_order = 20

    supports_manual_click = False
    supports_clear = False
    supports_automatic_action = True
    force_graph_visible = False

    dropdown_option_height_px = 50
    dropdown_menu_max_height_px = 500

    default_peak_count = 5
    default_histogram_bin_count = 500
    default_smoothing_window_fraction = 0.001
    default_minimum_prominence_fraction = 0.035
    default_minimum_distance_fraction = 0.035

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return configurable process settings.
        """
        return [
            {
                "name": "histogram_bins",
                "label": "Detection bins",
                "kind": "integer",
                "default_value": self.default_histogram_bin_count,
                "min_value": 64,
                "max_value": 4000,
                "step": 1,
                "help": (
                    "Number of histogram bins used for automatic peak detection. "
                    "Increase it for better separation of nearby peaks. Decrease it "
                    "if weak peaks are unstable due to noisy bins."
                ),
            },
            {
                "name": "smoothing_window_fraction",
                "label": "Smoothing fraction",
                "kind": "float",
                "default_value": self.default_smoothing_window_fraction,
                "min_value": 0.000001,
                "max_value": 0.08,
                "step": 0.000001,
                "help": (
                    "Gaussian-like smoothing width relative to histogram length. "
                    "Increase it to suppress bin noise. Decrease it when close peaks "
                    "are merged."
                ),
            },
            {
                "name": "minimum_prominence_fraction",
                "label": "Min prominence fraction",
                "kind": "float",
                "default_value": self.default_minimum_prominence_fraction,
                "min_value": 0.0,
                "max_value": 1.0,
                "step": 0.005,
                "help": (
                    "Minimum peak prominence relative to the tallest smoothed bin. "
                    "Decrease this to recover weaker first peaks."
                ),
            },
            {
                "name": "minimum_distance_fraction",
                "label": "Min distance fraction",
                "kind": "float",
                "default_value": self.default_minimum_distance_fraction,
                "min_value": 0.0,
                "max_value": 0.5,
                "step": 0.005,
                "help": (
                    "Minimum spacing between accepted peaks as a fraction of bins. "
                    "Decrease this when nearby populations are merged."
                ),
            },
            {
                "name": "log_transform_mode",
                "label": "Log transform mode",
                "kind": "select",
                "default_value": "auto",
                "options": [
                    {"label": "Auto", "value": "auto"},
                    {"label": "Yes", "value": "yes"},
                    {"label": "No", "value": "no"},
                ],
                "help": (
                    "Auto uses log10 only when most values are positive. "
                    "Force Yes or No to debug left-edge peak behavior."
                ),
            },
        ]

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
                    tooltip_text=(
                        "Detector signal used to build the 1D histogram. "
                        "Choose the channel where the calibration populations are most clearly separated. "
                        "For bead calibration, this is usually the fluorescence or scattering channel being calibrated."
                    ),
                ),
                self._build_vertical_spacer(height_px=16),
                self._build_peak_count_block(
                    ids=ids,
                    tooltip_text=(
                        "Maximum number of peaks to return. "
                        "Use the expected number of calibration populations. "
                        "If this value is too high, weak shoulders or noise maxima may be returned. "
                        "If it is too low, true populations may be omitted."
                    ),
                ),
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
        tooltip_text: str = "",
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

        tooltip_text:
            Text displayed on hover.

        Returns
        -------
        dash.html.Div
            Detector dropdown block.
        """
        dropdown_id = ids.process_detector_dropdown(
            process_name=self.process_name,
            channel_name=channel_name,
        )

        tooltip_target_id = self._build_tooltip_target_id(
            component_id=dropdown_id,
            suffix="help",
        )

        return dash.html.Div(
            [
                self._build_label_with_tooltip(
                    label=label,
                    tooltip_text=tooltip_text,
                    tooltip_target_id=tooltip_target_id,
                ),
                dash.dcc.Dropdown(
                    id=dropdown_id,
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
        tooltip_text: str = "",
    ) -> dash.html.Div:
        """
        Build the peak count input block.

        Parameters
        ----------
        ids:
            Peak section id factory.

        tooltip_text:
            Text displayed on hover.

        Returns
        -------
        dash.html.Div
            Peak count input block.
        """
        tooltip_target_id = self._build_tooltip_target_id(
            component_id=ids.peak_count_input,
            suffix="help",
        )

        return dash.html.Div(
            [
                self._build_label_with_tooltip(
                    label="Number of peaks to look for",
                    tooltip_text=tooltip_text,
                    tooltip_target_id=tooltip_target_id,
                ),
                dash.dcc.Input(
                    id=ids.peak_count_input,
                    type="text",
                    inputMode="numeric",
                    value=str(self.default_peak_count),
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

    def _build_label_with_tooltip(
        self,
        *,
        label: str,
        tooltip_text: str,
        tooltip_target_id: str,
    ) -> dash.html.Div:
        """
        Build a label with an optional hover tooltip.

        Parameters
        ----------
        label:
            Label text.

        tooltip_text:
            Tooltip content.

        tooltip_target_id:
            HTML id attached to the help marker.

        Returns
        -------
        dash.html.Div
            Label row.
        """
        tooltip_text = str(
            tooltip_text or "",
        ).strip()

        children: list[Any] = [
            dash.html.Div(
                label,
                style={
                    "fontWeight": 500,
                },
            )
        ]

        if tooltip_text:
            children.extend(
                [
                    dash.html.Span(
                        "ⓘ",
                        id=tooltip_target_id,
                        style={
                            "marginLeft": "6px",
                            "cursor": "help",
                            "fontSize": "0.82rem",
                            "opacity": 0.75,
                            "userSelect": "none",
                        },
                    ),
                    dbc.Tooltip(
                        tooltip_text,
                        target=tooltip_target_id,
                        placement="top",
                    ),
                ]
            )

        return dash.html.Div(
            children,
            style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "6px",
            },
        )

    def _build_tooltip_target_id(
        self,
        *,
        component_id: Any,
        suffix: str,
    ) -> str:
        """
        Build a string tooltip target id from a Dash component id.

        Parameters
        ----------
        component_id:
            Source component id.

        suffix:
            Extra suffix appended to the tooltip id.

        Returns
        -------
        str
            String id safe for dbc.Tooltip target lookup.
        """
        if isinstance(component_id, dict):
            base_identifier = json.dumps(
                component_id,
                sort_keys=True,
                separators=(",", ":"),
            )

        else:
            base_identifier = str(
                component_id,
            )

        safe_identifier = (
            base_identifier
            .replace("{", "")
            .replace("}", "")
            .replace('"', "")
            .replace(":", "-")
            .replace(",", "-")
            .replace(" ", "-")
            .replace(".", "-")
            .replace("/", "-")
        )

        return f"{safe_identifier}-{suffix}"

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
        process_settings: Optional[dict[str, Any]] = None,
        peak_count: Any = None,
        max_events_for_analysis: Any = None,
        max_events_for_plots: Any = None,
        **_kwargs: Any,
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

        resolved_settings = self.resolve_settings(
            process_settings=process_settings,
            peak_count=peak_count,
        )

        resolved_max_events = resolve_integer_value(
            value=max_events_for_analysis
            if max_events_for_analysis is not None
            else max_events_for_plots,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        values = self.read_detector_values(
            backend=backend,
            detector_column=str(detector_column),
            max_events_for_analysis=resolved_max_events,
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

        peak_positions, detection_debug = self.estimate_peak_positions(
            values=values,
            settings=resolved_settings,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
            debug_info=detection_debug,
        )

        logger.debug(
            "Automatic 1D detected peak_positions=%r detector_column=%r "
            "settings=%r max_events_for_analysis=%r detection_debug=%r",
            peak_positions,
            detector_column,
            resolved_settings,
            resolved_max_events,
            detection_debug,
        )

        status = (
            f"Detected {len(peak_positions)} peak(s)."
            if peak_positions
            else "No peaks detected."
        )

        if resolved_settings.advanced_mode:
            status = (
                f"{status} Debug: finite={detection_debug.get('finite_value_count', 0)}, "
                f"working={detection_debug.get('working_value_count', 0)}, "
                f"candidates={detection_debug.get('candidate_count', 0)}, "
                f"after_prom={detection_debug.get('post_prominence_count', 0)}, "
                f"selected={detection_debug.get('selected_count', 0)}, "
                f"log={detection_debug.get('used_log_transform', False)}"
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
        settings: "Automatic1DRunSettings",
    ) -> tuple[list[float], dict[str, Any]]:
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
        tuple[list[float], dict[str, Any]]
            Estimated peak positions and debug metadata.
        """
        finite_values = self.prepare_finite_values(
            values,
        )

        debug_info: dict[str, Any] = {
            "input_value_count": int(np.asarray(values).reshape(-1).size),
            "finite_value_count": int(finite_values.size),
            "peak_details": [],
        }

        if finite_values.size == 0:
            return [], debug_info

        working_values, inverse_transform, axis_debug = self.build_peak_detection_axis(
            values=finite_values,
            log_transform_mode=settings.log_transform_mode,
        )

        debug_info.update(axis_debug)

        if working_values.size == 0:
            return [], debug_info

        counts, bin_edges = np.histogram(
            working_values,
            bins=settings.histogram_bins,
        )

        debug_info["working_value_count"] = int(working_values.size)
        debug_info["histogram_bin_count"] = int(counts.size)

        if counts.size == 0:
            return [], debug_info

        smoothed_counts = self.smooth_histogram_counts(
            counts=counts,
            window_fraction=settings.smoothing_window_fraction,
        )

        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        debug_bin_centers = inverse_transform(
            bin_centers,
        )

        debug_info["histogram_bin_centers"] = [
            float(value)
            for value in np.asarray(debug_bin_centers, dtype=float)
            if np.isfinite(value)
        ]

        debug_info["smoothed_counts"] = [
            float(value)
            for value in np.asarray(smoothed_counts, dtype=float)
            if np.isfinite(value)
        ]

        peak_indices, prominence_debug, selected_prominences = self.find_prominent_peak_indices(
            counts=smoothed_counts,
            peak_count=settings.peak_count,
            minimum_prominence_fraction=settings.minimum_prominence_fraction,
            minimum_distance_fraction=settings.minimum_distance_fraction,
        )

        debug_info.update(prominence_debug)

        if peak_indices.size == 0:
            return [], debug_info

        peak_positions_working_axis = bin_centers[peak_indices]
        selected_peak_counts = np.asarray(
            [
                float(smoothed_counts[int(index)])
                for index in peak_indices
            ],
            dtype=float,
        )
        peak_positions = inverse_transform(
            peak_positions_working_axis,
        )

        peak_positions = np.asarray(
            peak_positions,
            dtype=float,
        )

        finite_peak_mask = np.isfinite(peak_positions)
        peak_positions = peak_positions[finite_peak_mask]
        selected_prominences = selected_prominences[finite_peak_mask]
        selected_peak_counts = selected_peak_counts[finite_peak_mask]

        order = np.argsort(peak_positions)

        peak_positions = peak_positions[order]
        selected_prominences = selected_prominences[order]
        selected_peak_counts = selected_peak_counts[order]

        peak_positions = peak_positions[: int(settings.peak_count)]
        selected_prominences = selected_prominences[: int(settings.peak_count)]
        selected_peak_counts = selected_peak_counts[: int(settings.peak_count)]

        debug_info["selected_count"] = int(peak_positions.size)
        debug_info["peak_details"] = [
            {
                "count": float(selected_peak_counts[index]),
                "prominence": float(selected_prominences[index]),
            }
            for index in range(int(peak_positions.size))
        ]

        return (
            [
                float(value)
                for value in peak_positions
            ],
            debug_info,
        )

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
        *,
        values: np.ndarray,
        log_transform_mode: str,
    ) -> tuple[np.ndarray, Any, dict[str, Any]]:
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
        tuple[np.ndarray, Any, dict[str, Any]]
            Working values, inverse transform callable, and debug metadata.
        """
        positive_values = values[values > 0.0]
        non_positive_count = int(values.size - positive_values.size)

        if log_transform_mode == "yes":
            if positive_values.size == 0:
                return (
                    np.asarray([], dtype=float),
                    self.inverse_log10_transform,
                    {
                        "used_log_transform": True,
                        "dropped_non_positive_values": non_positive_count,
                    },
                )

            return (
                np.log10(positive_values),
                self.inverse_log10_transform,
                {
                    "used_log_transform": True,
                    "dropped_non_positive_values": non_positive_count,
                },
            )

        if log_transform_mode == "no":
            return (
                values,
                self.identity_transform,
                {
                    "used_log_transform": False,
                    "dropped_non_positive_values": 0,
                },
            )

        if positive_values.size >= max(10, int(0.80 * values.size)):
            working_values = np.log10(
                positive_values,
            )

            return (
                working_values,
                self.inverse_log10_transform,
                {
                    "used_log_transform": True,
                    "dropped_non_positive_values": non_positive_count,
                },
            )

        return (
            values,
            self.identity_transform,
            {
                "used_log_transform": False,
                "dropped_non_positive_values": 0,
            },
        )

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
    ) -> tuple[np.ndarray, dict[str, Any], np.ndarray]:
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
        tuple[np.ndarray, dict[str, Any], np.ndarray]
            Selected peak indices, debug metadata, and selected prominences.
        """
        counts = np.asarray(
            counts,
            dtype=float,
        )

        debug_info: dict[str, Any] = {
            "candidate_count": 0,
            "post_prominence_count": 0,
            "selected_count": 0,
        }

        if counts.size < 3:
            return np.asarray([], dtype=int), debug_info, np.asarray([], dtype=float)

        maximum_count = float(
            np.max(counts),
        )

        if maximum_count <= 0.0:
            return np.asarray([], dtype=int), debug_info, np.asarray([], dtype=float)

        candidate_indices = self.find_local_maxima_indices(
            counts=counts,
        )

        if candidate_indices.size == 0:
            return np.asarray([], dtype=int), debug_info, np.asarray([], dtype=float)

        debug_info["candidate_count"] = int(candidate_indices.size)

        prominences = self.estimate_peak_prominences(
            counts=counts,
            candidate_indices=candidate_indices,
        )

        minimum_prominence = maximum_count * float(minimum_prominence_fraction)
        debug_info["minimum_prominence"] = float(minimum_prominence)

        prominence_mask = prominences >= minimum_prominence

        candidate_indices = candidate_indices[prominence_mask]
        prominences = prominences[prominence_mask]

        if candidate_indices.size == 0:
            return np.asarray([], dtype=int), debug_info, np.asarray([], dtype=float)

        debug_info["post_prominence_count"] = int(candidate_indices.size)

        minimum_distance = max(
            1,
            int(round(counts.size * float(minimum_distance_fraction))),
        )

        debug_info["minimum_distance_bins"] = int(minimum_distance)

        selected_indices = self.select_peaks_by_prominence_and_distance(
            candidate_indices=candidate_indices,
            prominences=prominences,
            peak_count=peak_count,
            minimum_distance=minimum_distance,
        )

        selected_indices = np.sort(
            selected_indices,
        )

        prominence_by_index = {
            int(candidate_indices[index]): float(prominences[index])
            for index in range(len(candidate_indices))
        }

        selected_prominences = np.asarray(
            [
                prominence_by_index.get(int(selected_index), 0.0)
                for selected_index in selected_indices
            ],
            dtype=float,
        )

        debug_info["selected_count"] = int(selected_indices.size)

        return selected_indices, debug_info, selected_prominences

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

        if counts.size == 0:
            return np.asarray(
                candidate_indices,
                dtype=int,
            )

        if counts.size == 1:
            return np.asarray(
                [0],
                dtype=int,
            )

        if counts[0] > counts[1]:
            candidate_indices.append(0)

        for index in range(1, counts.size - 1):
            if counts[index] > counts[index - 1] and counts[index] > counts[index + 1]:
                candidate_indices.append(index)

        if counts[-1] > counts[-2]:
            candidate_indices.append(counts.size - 1)

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

            valley_minima = [
                float(value)
                for value in (
                    left_minimum,
                    right_minimum,
                )
                if value is not None and np.isfinite(value)
            ]

            if not valley_minima:
                baseline = 0.0
            else:
                baseline = max(
                    valley_minima,
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
    ) -> Optional[float]:
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
            return None

        return float(
            np.min(left_slice),
        )

    def find_right_valley_minimum(
        self,
        *,
        counts: np.ndarray,
        peak_index: int,
    ) -> Optional[float]:
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

        if peak_index >= counts.size - 1:
            return None

        right_index = peak_index

        while right_index < counts.size - 1 and counts[right_index] <= peak_height:
            right_index += 1

            if counts[right_index] > peak_height:
                break

        right_slice = counts[peak_index: right_index + 1]

        if right_slice.size == 0:
            return None

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
        debug_info: Optional[dict[str, Any]] = None,
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
            "debug": dict(debug_info or {}),
        }

    def build_empty_peak_lines_payload(self) -> dict[str, list[Any]]:
        """
        Build an empty graph annotation payload.

        Returns
        -------
        dict[str, list[Any]]
            Empty payload.
        """
        return {
            "positions": [],
            "labels": [],
            "x_positions": [],
            "y_positions": [],
            "points": [],
            "debug": {},
        }

    def resolve_settings(
        self,
        *,
        process_settings: Optional[dict[str, Any]],
        peak_count: Any,
    ) -> "Automatic1DRunSettings":
        """
        Resolve effective process settings from Dash payloads.
        """
        settings = process_settings if isinstance(process_settings, dict) else {}

        log_transform_mode = str(
            settings.get("log_transform_mode", "auto")
        ).strip().lower()

        if log_transform_mode not in {"auto", "yes", "no"}:
            log_transform_mode = "auto"

        return Automatic1DRunSettings(
            peak_count=self.resolve_peak_count(
                peak_count,
            ),
            histogram_bins=resolve_integer_setting(
                settings=settings,
                name="histogram_bins",
                default=self.default_histogram_bin_count,
                minimum=64,
                maximum=4000,
            ),
            smoothing_window_fraction=resolve_float_setting(
                settings=settings,
                name="smoothing_window_fraction",
                default=self.default_smoothing_window_fraction,
                minimum=0.000001,
                maximum=0.08,
            ),
            minimum_prominence_fraction=resolve_float_setting(
                settings=settings,
                name="minimum_prominence_fraction",
                default=self.default_minimum_prominence_fraction,
                minimum=0.0,
                maximum=1.0,
            ),
            minimum_distance_fraction=resolve_float_setting(
                settings=settings,
                name="minimum_distance_fraction",
                default=self.default_minimum_distance_fraction,
                minimum=0.0,
                maximum=0.5,
            ),
            log_transform_mode=log_transform_mode,
            advanced_mode=self._resolve_advanced_mode(settings=settings),
        )

    def _resolve_advanced_mode(
        self,
        *,
        settings: dict[str, Any],
    ) -> bool:
        """
        Resolve advanced mode from callback-provided process settings.
        """
        value = settings.get("advanced_mode", None)

        if isinstance(value, str):
            return value == "enabled"

        if isinstance(value, (list, tuple, set)):
            return "enabled" in value

        if isinstance(value, bool):
            return value

        return False


class Automatic1DRunSettings:
    """
    Effective settings for one Automatic 1D detection run.
    """

    def __init__(
        self,
        *,
        peak_count: int,
        histogram_bins: int,
        smoothing_window_fraction: float,
        minimum_prominence_fraction: float,
        minimum_distance_fraction: float,
        log_transform_mode: str,
        advanced_mode: bool,
    ) -> None:
        self.peak_count = int(peak_count)
        self.histogram_bins = int(histogram_bins)
        self.smoothing_window_fraction = float(smoothing_window_fraction)
        self.minimum_prominence_fraction = float(minimum_prominence_fraction)
        self.minimum_distance_fraction = float(minimum_distance_fraction)
        self.log_transform_mode = str(log_transform_mode)
        self.advanced_mode = bool(advanced_mode)

    def __repr__(self) -> str:
        """
        Return compact representation for debug logging.
        """
        return (
            "Automatic1DRunSettings("
            f"peak_count={self.peak_count!r}, "
            f"histogram_bins={self.histogram_bins!r}, "
            f"smoothing_window_fraction={self.smoothing_window_fraction!r}, "
            f"minimum_prominence_fraction={self.minimum_prominence_fraction!r}, "
            f"minimum_distance_fraction={self.minimum_distance_fraction!r}, "
            f"log_transform_mode={self.log_transform_mode!r}, "
            f"advanced_mode={self.advanced_mode!r})"
        )


PROCESS = Automatic1DPeaksProcess()
