# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess, PeakProcessResult
from RosettaX.utils.io import column_copy


logger = logging.getLogger(__name__)


class SmoothedDensityProminence2DPeakProcess(BasePeakProcess):
    """
    Smoothed density prominence 2D peak registration.

    This process is intended for 2D cytometry clouds where populations may have
    very different event counts.

    The process gates x and y with quantiles, builds a 2D histogram density map,
    smooths the density map, finds local density maxima, filters them by
    prominence and minimum density, then returns peak centers in the original
    detector units.

    Compared with K means, this detects local density modes instead of forcing
    every event into a fixed number of clusters.
    """

    process_name = "Prominence 2D"
    process_label = "Prominence 2D"
    description = (
        "Gate two detector signals with quantiles, build a smoothed 2D density "
        "map, then detect local density maxima using prominence and minimum "
        "distance criteria."
    )
    graph_type = "2d_scatter"
    sort_order = 41

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
            "y_axis",
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user visible detector labels.
        """
        return {
            "x_axis": "X axis channel",
            "y_axis": "Y axis channel",
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
                    "Maximum number of 2D density peaks returned by the detector. "
                    "Use the expected number of calibration populations. Increase it "
                    "when you expect more populations. Decrease it when weak shoulders "
                    "or noisy local maxima are being returned."
                ),
            },
            {
                "name": "x_axis_bins",
                "label": "X bins",
                "kind": "integer",
                "default_value": 256,
                "min_value": 32,
                "max_value": 2000,
                "step": 32,
                "help": (
                    "Number of histogram bins used on the x axis for the internal 2D "
                    "density map. More bins improve x resolution but make the density "
                    "map noisier. Fewer bins smooth the density map but can merge "
                    "nearby populations."
                ),
            },
            {
                "name": "y_axis_bins",
                "label": "Y bins",
                "kind": "integer",
                "default_value": 256,
                "min_value": 32,
                "max_value": 2000,
                "step": 32,
                "help": (
                    "Number of histogram bins used on the y axis for the internal 2D "
                    "density map. More bins improve y resolution but increase sparse "
                    "bin noise. Fewer bins make detection more stable but reduce the "
                    "ability to separate close populations."
                ),
            },
            {
                "name": "smoothing_window_size",
                "label": "Smoothing window",
                "kind": "integer",
                "default_value": 5,
                "min_value": 1,
                "max_value": 101,
                "step": 2,
                "help": (
                    "Width of the separable moving average filter applied to the 2D "
                    "density map before local maximum detection. Increase it to suppress "
                    "isolated noisy bins. Decrease it when close populations are being "
                    "merged or peak centers are being shifted too much."
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
                    "Minimum local prominence required for a density maximum, expressed "
                    "as a fraction of the highest smoothed density value. Prominence "
                    "measures how much a peak rises above its surrounding density valley. "
                    "Increase it to reject weak shoulders and noise. Decrease it to recover "
                    "small but real populations."
                ),
            },
            {
                "name": "minimum_density_fraction",
                "label": "Min density fraction",
                "kind": "float",
                "default_value": 0.01,
                "min_value": 0.0,
                "max_value": 1.0,
                "step": 0.005,
                "help": (
                    "Minimum density required at a peak, expressed as a fraction of the "
                    "highest smoothed density value. This rejects very sparse local maxima. "
                    "Increase it to ignore low density artifacts. Decrease it when real "
                    "populations contain few events."
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
                    "Minimum Euclidean separation between accepted density peaks, expressed "
                    "in 2D histogram bin units. If two candidate peaks are closer than this, "
                    "only the more prominent one is kept. Increase it to merge shoulders. "
                    "Decrease it to allow close populations."
                ),
            },
            {
                "name": "neighborhood_radius_bins",
                "label": "Neighborhood radius bins",
                "kind": "integer",
                "default_value": 1,
                "min_value": 1,
                "max_value": 20,
                "step": 1,
                "help": (
                    "Radius, in histogram bins, used to decide whether a bin is a local "
                    "maximum. A radius of 1 compares each bin to its immediate neighbors. "
                    "Increase it to make peak detection stricter and suppress tiny local "
                    "ripples. Decrease it to detect finer local structure."
                ),
            },
            {
                "name": "x_axis_lower_gate_quantile",
                "label": "X lower gate quantile",
                "kind": "float",
                "default_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
                "help": (
                    "Lower x axis quantile used to remove the lowest x values before "
                    "building the density map. A value of 0.0 keeps the full lower tail. "
                    "Increase it to remove low end background, debris, or extreme outliers."
                ),
            },
            {
                "name": "x_axis_upper_gate_quantile",
                "label": "X upper gate quantile",
                "kind": "float",
                "default_value": 1.0,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
                "help": (
                    "Upper x axis quantile used to remove the highest x values before "
                    "building the density map. A value of 1.0 keeps the full upper tail. "
                    "Decrease it to remove saturated events, rare bright outliers, or "
                    "x axis contaminants."
                ),
            },
            {
                "name": "y_axis_lower_gate_quantile",
                "label": "Y lower gate quantile",
                "kind": "float",
                "default_value": 0.0,
                "min_value": 0.0,
                "max_value": 0.499,
                "step": 0.001,
                "help": (
                    "Lower y axis quantile used to remove the lowest y values before "
                    "building the density map. A value of 0.0 keeps the full lower tail. "
                    "Increase it to remove low end background, debris, or extreme outliers."
                ),
            },
            {
                "name": "y_axis_upper_gate_quantile",
                "label": "Y upper gate quantile",
                "kind": "float",
                "default_value": 1.0,
                "min_value": 0.501,
                "max_value": 1.0,
                "step": 0.001,
                "help": (
                    "Upper y axis quantile used to remove the highest y values before "
                    "building the density map. A value of 1.0 keeps the full upper tail. "
                    "Decrease it to remove saturated events, rare bright outliers, or "
                    "y axis contaminants."
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
                    "Build the internal density map in log10 space instead of linear "
                    "space. Use log transform for cytometry signals spanning several "
                    "orders of magnitude. Disable it when values can be zero or negative, "
                    "or when populations are better separated linearly."
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
        Run smoothed 2D density prominence peak detection.
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

        y_axis_column = detector_channels.get(
            "y_axis",
        )

        if not str(x_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select an x axis channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        if not str(y_axis_column or "").strip():
            return PeakProcessResult(
                peak_positions=[],
                peak_lines_payload=self.build_empty_peak_lines_payload(),
                status="Select a y axis channel first.",
                new_peak_positions=[],
                clear_existing_table_peaks=False,
            )

        settings = SmoothedDensityProminence2DSettings.from_process_settings(
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

        y_axis_values = np.asarray(
            column_copy(
                fcs_file_path=backend.fcs_file_path,
                detector_column=str(y_axis_column),
                dtype=float,
                n=maximum_events,
            ),
            dtype=float,
        )

        result = compute_smoothed_density_prominence_peaks(
            x_axis_values=x_axis_values,
            y_axis_values=y_axis_values,
            settings=settings,
        )

        peak_positions = deduplicate_2d_peak_positions(
            peak_positions=result.peak_positions,
        )

        peak_lines_payload = self.build_peak_lines_payload(
            peak_positions=peak_positions,
            prominences=result.prominences,
            peak_densities=result.peak_densities,
            x_axis_lower_gate=result.x_axis_lower_gate,
            x_axis_upper_gate=result.x_axis_upper_gate,
            y_axis_lower_gate=result.y_axis_lower_gate,
            y_axis_upper_gate=result.y_axis_upper_gate,
        )

        status = (
            f"Smoothed 2D density prominence found {len(peak_positions)} peak(s) "
            f"from {result.gated_event_count} gated event(s). "
            f"X gate=[{result.x_axis_lower_gate:.6g}, {result.x_axis_upper_gate:.6g}], "
            f"Y gate=[{result.y_axis_lower_gate:.6g}, {result.y_axis_upper_gate:.6g}]."
        )

        logger.debug(
            "Smoothed 2D density prominence completed with x_axis_column=%r "
            "y_axis_column=%r settings=%r gated_event_count=%r peak_positions=%r "
            "prominences=%r",
            x_axis_column,
            y_axis_column,
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
            status="Cleared smoothed 2D density prominence graph overlays. Table values were preserved.",
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
            "y_positions": [],
            "points": [],
            "labels": [],
            "prominences": [],
            "peak_densities": [],
            "x_axis_lower_gate": 0.0,
            "x_axis_upper_gate": 0.0,
            "y_axis_lower_gate": 0.0,
            "y_axis_upper_gate": 0.0,
        }

    def build_peak_lines_payload(
        self,
        *,
        peak_positions: list[dict[str, float]],
        prominences: list[float],
        peak_densities: list[float],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
    ) -> dict[str, Any]:
        """
        Build graph annotation payload.
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
            f"Peak {index + 1} | prominence={prominences[index]:.4g}"
            if index < len(prominences)
            else f"Peak {index + 1}"
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
            "prominences": [
                float(prominence)
                for prominence in prominences
            ],
            "peak_densities": [
                float(peak_density)
                for peak_density in peak_densities
            ],
            "x_axis_lower_gate": float(x_axis_lower_gate),
            "x_axis_upper_gate": float(x_axis_upper_gate),
            "y_axis_lower_gate": float(y_axis_lower_gate),
            "y_axis_upper_gate": float(y_axis_upper_gate),
        }


class SmoothedDensityProminence2DSettings:
    """
    Settings for smoothed density prominence 2D peak detection.
    """

    def __init__(
        self,
        *,
        maximum_peak_count: int,
        x_axis_bins: int,
        y_axis_bins: int,
        smoothing_window_size: int,
        minimum_prominence_fraction: float,
        minimum_density_fraction: float,
        minimum_distance_bins: int,
        neighborhood_radius_bins: int,
        x_axis_lower_gate_quantile: float,
        x_axis_upper_gate_quantile: float,
        y_axis_lower_gate_quantile: float,
        y_axis_upper_gate_quantile: float,
        use_log_transform: bool,
    ) -> None:
        self.maximum_peak_count = maximum_peak_count
        self.x_axis_bins = x_axis_bins
        self.y_axis_bins = y_axis_bins
        self.smoothing_window_size = smoothing_window_size
        self.minimum_prominence_fraction = minimum_prominence_fraction
        self.minimum_density_fraction = minimum_density_fraction
        self.minimum_distance_bins = minimum_distance_bins
        self.neighborhood_radius_bins = neighborhood_radius_bins
        self.x_axis_lower_gate_quantile = x_axis_lower_gate_quantile
        self.x_axis_upper_gate_quantile = x_axis_upper_gate_quantile
        self.y_axis_lower_gate_quantile = y_axis_lower_gate_quantile
        self.y_axis_upper_gate_quantile = y_axis_upper_gate_quantile
        self.use_log_transform = use_log_transform

    @classmethod
    def from_process_settings(
        cls,
        *,
        process_settings: dict[str, Any],
        peak_count: Any = None,
    ) -> "SmoothedDensityProminence2DSettings":
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

        y_axis_lower_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_lower_gate_quantile",
            default=0.0,
            minimum=0.0,
            maximum=0.499,
        )

        y_axis_upper_gate_quantile = resolve_float_setting(
            settings=process_settings,
            name="y_axis_upper_gate_quantile",
            default=1.0,
            minimum=0.501,
            maximum=1.0,
        )

        if x_axis_lower_gate_quantile >= x_axis_upper_gate_quantile:
            x_axis_lower_gate_quantile = 0.0
            x_axis_upper_gate_quantile = 1.0

        if y_axis_lower_gate_quantile >= y_axis_upper_gate_quantile:
            y_axis_lower_gate_quantile = 0.0
            y_axis_upper_gate_quantile = 1.0

        return cls(
            maximum_peak_count=maximum_peak_count,
            x_axis_bins=resolve_integer_setting(
                settings=process_settings,
                name="x_axis_bins",
                default=256,
                minimum=32,
                maximum=2000,
            ),
            y_axis_bins=resolve_integer_setting(
                settings=process_settings,
                name="y_axis_bins",
                default=256,
                minimum=32,
                maximum=2000,
            ),
            smoothing_window_size=resolve_integer_setting(
                settings=process_settings,
                name="smoothing_window_size",
                default=5,
                minimum=1,
                maximum=101,
            ),
            minimum_prominence_fraction=resolve_float_setting(
                settings=process_settings,
                name="minimum_prominence_fraction",
                default=0.03,
                minimum=0.0,
                maximum=1.0,
            ),
            minimum_density_fraction=resolve_float_setting(
                settings=process_settings,
                name="minimum_density_fraction",
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
            neighborhood_radius_bins=resolve_integer_setting(
                settings=process_settings,
                name="neighborhood_radius_bins",
                default=1,
                minimum=1,
                maximum=20,
            ),
            x_axis_lower_gate_quantile=x_axis_lower_gate_quantile,
            x_axis_upper_gate_quantile=x_axis_upper_gate_quantile,
            y_axis_lower_gate_quantile=y_axis_lower_gate_quantile,
            y_axis_upper_gate_quantile=y_axis_upper_gate_quantile,
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
            "SmoothedDensityProminence2DSettings("
            f"maximum_peak_count={self.maximum_peak_count!r}, "
            f"x_axis_bins={self.x_axis_bins!r}, "
            f"y_axis_bins={self.y_axis_bins!r}, "
            f"smoothing_window_size={self.smoothing_window_size!r}, "
            f"minimum_prominence_fraction={self.minimum_prominence_fraction!r}, "
            f"minimum_density_fraction={self.minimum_density_fraction!r}, "
            f"minimum_distance_bins={self.minimum_distance_bins!r}, "
            f"neighborhood_radius_bins={self.neighborhood_radius_bins!r}, "
            f"x_axis_lower_gate_quantile={self.x_axis_lower_gate_quantile!r}, "
            f"x_axis_upper_gate_quantile={self.x_axis_upper_gate_quantile!r}, "
            f"y_axis_lower_gate_quantile={self.y_axis_lower_gate_quantile!r}, "
            f"y_axis_upper_gate_quantile={self.y_axis_upper_gate_quantile!r}, "
            f"use_log_transform={self.use_log_transform!r})"
        )


class SmoothedDensityProminence2DResult:
    """
    Result from smoothed density prominence peak detection.
    """

    def __init__(
        self,
        *,
        peak_positions: list[dict[str, float]],
        prominences: list[float],
        peak_densities: list[float],
        x_axis_lower_gate: float,
        x_axis_upper_gate: float,
        y_axis_lower_gate: float,
        y_axis_upper_gate: float,
        gated_event_count: int,
    ) -> None:
        self.peak_positions = peak_positions
        self.prominences = prominences
        self.peak_densities = peak_densities
        self.x_axis_lower_gate = x_axis_lower_gate
        self.x_axis_upper_gate = x_axis_upper_gate
        self.y_axis_lower_gate = y_axis_lower_gate
        self.y_axis_upper_gate = y_axis_upper_gate
        self.gated_event_count = gated_event_count


class DensityPeakCandidate:
    """
    One local maximum candidate from the smoothed 2D density map.
    """

    def __init__(
        self,
        *,
        x_index: int,
        y_index: int,
        transformed_x_position: float,
        transformed_y_position: float,
        density: float,
        prominence: float,
    ) -> None:
        self.x_index = int(x_index)
        self.y_index = int(y_index)
        self.transformed_x_position = float(transformed_x_position)
        self.transformed_y_position = float(transformed_y_position)
        self.density = float(density)
        self.prominence = float(prominence)


def compute_smoothed_density_prominence_peaks(
    *,
    x_axis_values: Any,
    y_axis_values: Any,
    settings: SmoothedDensityProminence2DSettings,
) -> SmoothedDensityProminence2DResult:
    """
    Compute 2D peaks from a smoothed density map and prominence criteria.
    """
    original_x_values, original_y_values, transformed_x_values, transformed_y_values = prepare_axis_values(
        x_axis_values=x_axis_values,
        y_axis_values=y_axis_values,
        use_log_transform=settings.use_log_transform,
    )

    if original_x_values.size == 0:
        return build_empty_result()

    x_axis_lower_gate, x_axis_upper_gate = compute_quantile_gate(
        values=original_x_values,
        lower_quantile=settings.x_axis_lower_gate_quantile,
        upper_quantile=settings.x_axis_upper_gate_quantile,
    )

    y_axis_lower_gate, y_axis_upper_gate = compute_quantile_gate(
        values=original_y_values,
        lower_quantile=settings.y_axis_lower_gate_quantile,
        upper_quantile=settings.y_axis_upper_gate_quantile,
    )

    gate_mask = (
        (original_x_values >= x_axis_lower_gate)
        & (original_x_values <= x_axis_upper_gate)
        & (original_y_values >= y_axis_lower_gate)
        & (original_y_values <= y_axis_upper_gate)
    )

    gated_transformed_x_values = transformed_x_values[
        gate_mask
    ]

    gated_transformed_y_values = transformed_y_values[
        gate_mask
    ]

    if gated_transformed_x_values.size == 0:
        return SmoothedDensityProminence2DResult(
            peak_positions=[],
            prominences=[],
            peak_densities=[],
            x_axis_lower_gate=float(x_axis_lower_gate),
            x_axis_upper_gate=float(x_axis_upper_gate),
            y_axis_lower_gate=float(y_axis_lower_gate),
            y_axis_upper_gate=float(y_axis_upper_gate),
            gated_event_count=0,
        )

    density, x_edges, y_edges = np.histogram2d(
        gated_transformed_x_values,
        gated_transformed_y_values,
        bins=[
            int(settings.x_axis_bins),
            int(settings.y_axis_bins),
        ],
    )

    density = np.asarray(
        density,
        dtype=float,
    )

    smoothed_density = smooth_density_map(
        density=density,
        window_size=settings.smoothing_window_size,
    )

    x_centers = 0.5 * (
        x_edges[:-1]
        + x_edges[1:]
    )

    y_centers = 0.5 * (
        y_edges[:-1]
        + y_edges[1:]
    )

    maximum_density = float(
        np.max(smoothed_density),
    ) if smoothed_density.size else 0.0

    minimum_prominence = settings.minimum_prominence_fraction * maximum_density
    minimum_density = settings.minimum_density_fraction * maximum_density

    local_maxima_indices = find_local_maxima_2d_indices(
        values=smoothed_density,
        neighborhood_radius_bins=settings.neighborhood_radius_bins,
    )

    candidates: list[DensityPeakCandidate] = []

    for x_index, y_index in local_maxima_indices:
        density_value = float(
            smoothed_density[x_index, y_index],
        )

        if density_value < minimum_density:
            continue

        prominence = compute_local_density_prominence(
            values=smoothed_density,
            x_index=x_index,
            y_index=y_index,
            radius_bins=max(
                settings.minimum_distance_bins,
                settings.neighborhood_radius_bins,
            ),
        )

        if prominence < minimum_prominence:
            continue

        candidates.append(
            DensityPeakCandidate(
                x_index=x_index,
                y_index=y_index,
                transformed_x_position=float(x_centers[x_index]),
                transformed_y_position=float(y_centers[y_index]),
                density=density_value,
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
        key=lambda candidate: candidate.transformed_x_position,
    )

    peak_positions = [
        {
            "x": inverse_transform_position(
                transformed_position=candidate.transformed_x_position,
                use_log_transform=settings.use_log_transform,
            ),
            "y": inverse_transform_position(
                transformed_position=candidate.transformed_y_position,
                use_log_transform=settings.use_log_transform,
            ),
        }
        for candidate in candidates
    ]

    prominences = [
        float(candidate.prominence)
        for candidate in candidates
    ]

    peak_densities = [
        float(candidate.density)
        for candidate in candidates
    ]

    return SmoothedDensityProminence2DResult(
        peak_positions=peak_positions,
        prominences=prominences,
        peak_densities=peak_densities,
        x_axis_lower_gate=float(x_axis_lower_gate),
        x_axis_upper_gate=float(x_axis_upper_gate),
        y_axis_lower_gate=float(y_axis_lower_gate),
        y_axis_upper_gate=float(y_axis_upper_gate),
        gated_event_count=int(gated_transformed_x_values.size),
    )


def prepare_axis_values(
    *,
    x_axis_values: Any,
    y_axis_values: Any,
    use_log_transform: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert input values to finite original and transformed arrays.
    """
    original_x_values = np.asarray(
        x_axis_values,
        dtype=float,
    ).reshape(-1)

    original_y_values = np.asarray(
        y_axis_values,
        dtype=float,
    ).reshape(-1)

    common_size = min(
        original_x_values.size,
        original_y_values.size,
    )

    original_x_values = original_x_values[
        :common_size
    ]

    original_y_values = original_y_values[
        :common_size
    ]

    finite_mask = np.isfinite(original_x_values) & np.isfinite(original_y_values)

    if use_log_transform:
        finite_mask = finite_mask & (original_x_values > 0.0) & (original_y_values > 0.0)

    original_x_values = original_x_values[
        finite_mask
    ]

    original_y_values = original_y_values[
        finite_mask
    ]

    if use_log_transform:
        transformed_x_values = np.log10(
            original_x_values,
        )

        transformed_y_values = np.log10(
            original_y_values,
        )

    else:
        transformed_x_values = original_x_values.copy()
        transformed_y_values = original_y_values.copy()

    return (
        original_x_values,
        original_y_values,
        transformed_x_values,
        transformed_y_values,
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


def smooth_density_map(
    *,
    density: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth a 2D density map using a separable moving average.
    """
    density = np.asarray(
        density,
        dtype=float,
    )

    if density.size == 0:
        return density

    resolved_window_size = max(
        1,
        int(window_size),
    )

    if resolved_window_size <= 1:
        return density

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    resolved_window_size = min(
        resolved_window_size,
        density.shape[0],
        density.shape[1],
    )

    if resolved_window_size % 2 == 0:
        resolved_window_size -= 1

    if resolved_window_size < 3:
        return density

    kernel = np.ones(
        resolved_window_size,
        dtype=float,
    ) / float(resolved_window_size)

    smoothed_density = np.apply_along_axis(
        lambda values: np.convolve(values, kernel, mode="same"),
        axis=0,
        arr=density,
    )

    smoothed_density = np.apply_along_axis(
        lambda values: np.convolve(values, kernel, mode="same"),
        axis=1,
        arr=smoothed_density,
    )

    return smoothed_density


def find_local_maxima_2d_indices(
    *,
    values: np.ndarray,
    neighborhood_radius_bins: int,
) -> list[tuple[int, int]]:
    """
    Find local maxima in a 2D density map.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    if values.ndim != 2:
        return []

    if values.shape[0] < 3 or values.shape[1] < 3:
        return []

    radius = max(
        1,
        int(neighborhood_radius_bins),
    )

    maxima_indices: list[tuple[int, int]] = []

    for x_index in range(
        radius,
        values.shape[0] - radius,
    ):
        for y_index in range(
            radius,
            values.shape[1] - radius,
        ):
            center_value = float(
                values[x_index, y_index],
            )

            local_window = values[
                x_index - radius : x_index + radius + 1,
                y_index - radius : y_index + radius + 1,
            ]

            if center_value <= 0.0:
                continue

            if center_value < float(np.max(local_window)):
                continue

            if np.count_nonzero(local_window == center_value) > 1:
                continue

            maxima_indices.append(
                (
                    int(x_index),
                    int(y_index),
                )
            )

    return maxima_indices


def compute_local_density_prominence(
    *,
    values: np.ndarray,
    x_index: int,
    y_index: int,
    radius_bins: int,
) -> float:
    """
    Estimate local 2D peak prominence from the surrounding density valley.
    """
    values = np.asarray(
        values,
        dtype=float,
    )

    x_index = int(
        x_index,
    )

    y_index = int(
        y_index,
    )

    radius = max(
        1,
        int(radius_bins),
    )

    x_minimum = max(
        0,
        x_index - radius,
    )

    x_maximum = min(
        values.shape[0],
        x_index + radius + 1,
    )

    y_minimum = max(
        0,
        y_index - radius,
    )

    y_maximum = min(
        values.shape[1],
        y_index + radius + 1,
    )

    local_window = values[
        x_minimum:x_maximum,
        y_minimum:y_maximum,
    ]

    peak_value = float(
        values[x_index, y_index],
    )

    if local_window.size == 0:
        return 0.0

    valley_value = float(
        np.min(local_window),
    )

    return max(
        0.0,
        peak_value - valley_value,
    )


def enforce_minimum_distance_between_candidates(
    *,
    candidates: list[DensityPeakCandidate],
    minimum_distance_bins: int,
) -> list[DensityPeakCandidate]:
    """
    Keep the strongest candidates while enforcing a minimum Euclidean bin distance.
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: candidate.prominence,
        reverse=True,
    )

    selected_candidates: list[DensityPeakCandidate] = []

    for candidate in sorted_candidates:
        is_too_close = any(
            compute_candidate_distance(
                first_candidate=candidate,
                second_candidate=selected_candidate,
            )
            < float(minimum_distance_bins)
            for selected_candidate in selected_candidates
        )

        if is_too_close:
            continue

        selected_candidates.append(
            candidate,
        )

    return selected_candidates


def compute_candidate_distance(
    *,
    first_candidate: DensityPeakCandidate,
    second_candidate: DensityPeakCandidate,
) -> float:
    """
    Compute Euclidean distance between two density peak candidates in bin units.
    """
    delta_x = float(
        first_candidate.x_index - second_candidate.x_index,
    )

    delta_y = float(
        first_candidate.y_index - second_candidate.y_index,
    )

    return float(
        np.sqrt(delta_x * delta_x + delta_y * delta_y),
    )


def build_empty_result() -> SmoothedDensityProminence2DResult:
    """
    Build an empty result.
    """
    return SmoothedDensityProminence2DResult(
        peak_positions=[],
        prominences=[],
        peak_densities=[],
        x_axis_lower_gate=0.0,
        x_axis_upper_gate=0.0,
        y_axis_lower_gate=0.0,
        y_axis_upper_gate=0.0,
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
    Resolve a bounded float setting.
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


PROCESS = SmoothedDensityProminence2DPeakProcess()