# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from .base import BasePeakProcess
from .base import PeakProcessResult
from .base import build_edge_pileup_mask as shared_build_edge_pileup_mask
from .base import resolve_edge_artifact_filter_enabled
from RosettaX.utils.io import column_copy
from RosettaX.utils.reader import FCSFile

logger = logging.getLogger(__name__)


class FluorescenceGuidedScatterPeakProcess(BasePeakProcess):
    """
    Rosetta bead-mixture peak detection process.

    This process follows a fluorescence-guided workflow:

    1. Detect and validate fluorescence peaks in 1D.
    2. Resolve baseline fluorescence and fluorescent marker peaks.
    3. Gate marker events and detect corresponding scatter peaks.
    4. Gate non-fluorescent events from baseline fluorescence and detect
       non-fluorescent scatter peaks used for table insertion.
    """

    process_name = "Rosetta Script"
    process_label = "Rosetta Script"
    description = (
        "Fluorescence-guided scatter peak identification with per-peak "
        "validation for Rosetta bead mixtures."
    )
    graph_type = "2d_scatter"
    sort_order = 20

    supports_manual_click = False
    supports_clear = True
    supports_automatic_action = True
    force_graph_visible = True

    def get_required_detector_channels(self) -> list[str]:
        """
        Return required detector channels.
        """
        return [
            "scattering",
            "green_fluorescence",
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """
        Return user-visible detector channel labels for Rosetta Script.
        """
        return {
            "scattering": "Scattering channel",
            "green_fluorescence": "Green fluorescence channel",
        }

    def get_settings(self) -> list[dict[str, Any]]:
        """
        Return process settings shown in the UI.
        """
        return [
            {
                "name": "peak_count",
                "kind": "integer",
                "label": "Maximum number of scatter peaks",
                "default_value": 10,
                "min_value": 1,
                "max_value": 20,
                "step": 1,
            },
            {
                "name": "fit_r2_threshold",
                "kind": "float",
                "label": "Minimum fit R\u00b2",
                "help": (
                    "Minimum Gaussian fit quality for a peak to be accepted. "
                    "Lower values accept noisier peaks."
                ),
                "default_value": 0.85,
                "min_value": 0.00,
                "max_value": 0.999,
                "step": 0.01,
            },
            {
                "name": "baseline_sigma_multiplier",
                "kind": "float",
                "label": "Baseline gate width (\u03c3)",
                "help": (
                    "Events within this many standard deviations of the baseline "
                    "fluorescence peak are treated as non-fluorescent."
                ),
                "default_value": 3.0,
                "min_value": 0.5,
                "max_value": 5.0,
                "step": 0.5,
            },
            {
                "name": "fit_cv_threshold",
                "kind": "float",
                "label": "Maximum fluorescence peak CV",
                "help": (
                    "Maximum width allowed for fluorescence peaks during Rosetta "
                    "marker validation. CV is represented as std/mean, so 0.10 "
                    "corresponds to 10%."
                ),
                "default_value": 0.60,
                "min_value": 0.05,
                "max_value": 2.0,
                "step": 0.01,
            },
            {
                "name": "scatter_fit_r2_threshold",
                "kind": "float",
                "label": "Minimum scatter fit R\u00b2",
                "help": (
                    "Minimum Gaussian fit quality for scatter peaks. This is kept "
                    "separate from fluorescence so partially resolved scatter peaks "
                    "can still be accepted without relaxing fluorescence validation."
                ),
                "default_value": 0.70,
                "min_value": 0.00,
                "max_value": 0.999,
                "step": 0.01,
            },
            {
                "name": "scatter_fit_cv_threshold",
                "kind": "float",
                "label": "Maximum scatter peak CV",
                "help": (
                    "Maximum width allowed for scatter peaks during Rosetta "
                    "validation. CV is represented as std/mean, so 0.10 "
                    "corresponds to 10%."
                ),
                "default_value": 1.0,
                "min_value": 0.05,
                "max_value": 3.0,
                "step": 0.01,
            },
            {
                "name": "table_non_fluorescent_only",
                "kind": "boolean",
                "label": "Only output non-fluorescent peaks",
                "help": (
                    "When enabled, only baseline-gated non-fluorescent scatter peaks "
                    "are inserted into the table. Disable this to also insert "
                    "fluorescent marker-associated scatter peaks."
                ),
                "default_value": True,
            },
            {
                "name": "saturation_guard_enabled",
                "kind": "boolean",
                "label": "Enable saturation guard",
                "help": (
                    "When enabled, table peaks above saturation guard threshold "
                    "are excluded. Disable to keep all table peaks regardless of "
                    "saturation metadata."
                ),
                "default_value": True,
            },
            {
                "name": "saturation_guard_fraction",
                "kind": "float",
                "label": "Saturation guard (max / saturation)",
                "help": (
                    "Exclude table peaks above detector_saturation * this fraction "
                    "for the selected scatter channel when metadata includes "
                    "detector range values. This guard does not change detected "
                    "peaks or plotted events. Example: 0.25 means 4,000,000 "
                    "saturation becomes a 1,000,000 table threshold."
                ),
                "default_value": 0.25,
                "min_value": 0.0,
                "max_value": 1.0,
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
        Run the Rosetta peak identification workflow.
        """
        if backend is None:
            return self._empty_result(
                status="The backend is not available.",
                clear_existing_table_peaks=False,
            )

        scattering_column = detector_channels.get("scattering")
        green_fluorescence_column = detector_channels.get("green_fluorescence")

        if not str(scattering_column or "").strip():
            return self._empty_result(
                status="Select a scattering channel first.",
                clear_existing_table_peaks=False,
            )

        if not str(green_fluorescence_column or "").strip():
            return self._empty_result(
                status="Select a green fluorescence channel first.",
                clear_existing_table_peaks=False,
            )

        resolved_peak_count = resolve_integer(
            value=peak_count,
            default=10,
            minimum=1,
            maximum=20,
        )

        resolved_max_events_for_analysis = resolve_integer(
            value=max_events_for_analysis,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        # User-facing settings.
        fit_r2_threshold = resolve_float(
            value=process_settings.get("fit_r2_threshold"),
            default=0.85,
            minimum=0.00,
            maximum=0.999,
        )

        baseline_sigma_multiplier = resolve_float(
            value=process_settings.get("baseline_sigma_multiplier"),
            default=1.0,
            minimum=0.5,
            maximum=5.0,
        )

        fit_cv_threshold = resolve_float(
            value=process_settings.get("fit_cv_threshold"),
            default=0.60,
            minimum=0.05,
            maximum=2.0,
        )

        scatter_fit_r2_threshold = resolve_float(
            value=process_settings.get("scatter_fit_r2_threshold"),
            default=0.80,
            minimum=0.00,
            maximum=0.999,
        )

        scatter_fit_cv_threshold = resolve_float(
            value=process_settings.get("scatter_fit_cv_threshold"),
            default=1.0,
            minimum=0.05,
            maximum=3.0,
        )
        remove_saturated_events = resolve_edge_artifact_filter_enabled(
            process_settings=process_settings,
            default=True,
        )
        table_non_fluorescent_only = resolve_enabled_setting(
            value=process_settings.get("table_non_fluorescent_only"),
            default=True,
        )
        saturation_guard_enabled = resolve_enabled_setting(
            value=process_settings.get("saturation_guard_enabled"),
            default=True,
        )
        saturation_guard_fraction = resolve_float(
            value=process_settings.get("saturation_guard_fraction"),
            default=0.25,
            minimum=0.0,
            maximum=1.0,
        )

        # Internal algorithm constants (not user-configurable).
        minimum_peak_fraction = 0.03
        minimum_events_per_peak = 35
        fluorescence_saturation_quantile = 0.9995
        marker_gate_sigma_multiplier = 2.0

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

        removed_saturated_event_count = 0

        if remove_saturated_events:
            saturation_mask = build_saturated_event_mask(
                scattering_values=scattering_values,
                fluorescence_values=green_fluorescence_values,
            )
            removed_saturated_event_count = int(np.count_nonzero(saturation_mask))

            if removed_saturated_event_count > 0:
                keep_mask = ~saturation_mask
                scattering_values = scattering_values[keep_mask]
                green_fluorescence_values = green_fluorescence_values[keep_mask]

        if scattering_values.size == 0:
            return self._empty_result(
                status="No finite events are available for automatic detection.",
                clear_existing_table_peaks=False,
            )

        fluorescence_saturation_intensity = resolve_saturation_intensity(
            values=green_fluorescence_values,
            saturation_quantile=fluorescence_saturation_quantile,
        )

        fluorescence_analysis = find_fit_validate_peaks_1d(
            values=green_fluorescence_values,
            peak_count=3,
            minimum_peak_fraction=minimum_peak_fraction,
            minimum_events_per_peak=minimum_events_per_peak,
            fit_r2_threshold=fit_r2_threshold,
            fit_cv_threshold=fit_cv_threshold,
            saturation_intensity=fluorescence_saturation_intensity,
        )

        fluorescence_validated_peaks = fluorescence_analysis["validated_peaks"]
        fluorescence_diagnostic = build_peak_analysis_diagnostic_text(
            analysis=fluorescence_analysis,
            label="fluorescence",
        )

        if not fluorescence_validated_peaks:
            return self._build_stop_result(
                status=(
                    "No validated fluorescence peaks found. "
                    "Unable to identify fluorescent marker populations. "
                    f"{fluorescence_diagnostic}"
                ),
                fluorescence_analysis=fluorescence_analysis,
                plot_scattering_values=scattering_values,
                plot_fluorescence_values=green_fluorescence_values,
            )

        baseline_peak = resolve_baseline_peak(
            peaks=fluorescence_validated_peaks,
        )

        baseline_lower_gate = float(
            max(0.0, baseline_peak["mean"] - baseline_sigma_multiplier * max(baseline_peak["std"], 1e-12))
        )

        baseline_upper_gate = float(
            baseline_peak["mean"] + baseline_sigma_multiplier * max(baseline_peak["std"], 1e-12)
        )

        baseline_cutoff = float(baseline_upper_gate)

        marker_peaks = [
            peak
            for peak in fluorescence_validated_peaks
            if peak is not baseline_peak
        ]

        if len(marker_peaks) == 0:
            return self._build_stop_result(
                status=(
                    "0 fluorescent marker peaks found after removing baseline. "
                    "Stopping Rosetta workflow. "
                    f"{fluorescence_diagnostic}"
                ),
                fluorescence_analysis=fluorescence_analysis,
                baseline_lower_gate=baseline_lower_gate,
                baseline_upper_gate=baseline_upper_gate,
                plot_scattering_values=scattering_values,
                plot_fluorescence_values=green_fluorescence_values,
            )

        if len(marker_peaks) == 3:
            return self._build_stop_result(
                status=(
                    "3 fluorescent marker peaks found after removing baseline. "
                    "Stopping Rosetta workflow. "
                    f"{fluorescence_diagnostic}"
                ),
                fluorescence_analysis=fluorescence_analysis,
                baseline_lower_gate=baseline_lower_gate,
                baseline_upper_gate=baseline_upper_gate,
                plot_scattering_values=scattering_values,
                plot_fluorescence_values=green_fluorescence_values,
            )

        if len(marker_peaks) > 3:
            return self._build_stop_result(
                status=(
                    f"{len(marker_peaks)} fluorescent marker peaks found after removing baseline. "
                    "Stopping Rosetta workflow. "
                    f"{fluorescence_diagnostic}"
                ),
                fluorescence_analysis=fluorescence_analysis,
                baseline_lower_gate=baseline_lower_gate,
                baseline_upper_gate=baseline_upper_gate,
                plot_scattering_values=scattering_values,
                plot_fluorescence_values=green_fluorescence_values,
            )

        marker_classification = classify_marker_peaks(
            marker_peaks=marker_peaks,
        )

        marker_points: list[dict[str, float]] = []
        marker_scatter_guide_positions: list[float] = []

        for marker_peak in marker_classification:
            marker_gate_mask = build_sigma_gate_mask(
                values=green_fluorescence_values,
                mean_value=marker_peak["mean"],
                std_value=marker_peak["std"],
                sigma_multiplier=marker_gate_sigma_multiplier,
            )

            gated_scatter_values = scattering_values[marker_gate_mask]

            scatter_peak = select_primary_validated_peak(
                values=gated_scatter_values,
                peak_count=1,
                minimum_peak_fraction=minimum_peak_fraction,
                minimum_events_per_peak=minimum_events_per_peak,
                fit_r2_threshold=scatter_fit_r2_threshold,
                fit_cv_threshold=scatter_fit_cv_threshold,
            )

            if scatter_peak is None:
                continue

            marker_scatter_guide_positions.append(
                float(scatter_peak["mean"])
            )
            marker_points.append(
                {
                    "x": float(scatter_peak["mean"]),
                    "y": float(marker_peak["mean"]),
                    "kind": "marker",
                    "label": str(marker_peak["marker_role"]),
                }
            )

        non_fluorescent_mask = (
            np.isfinite(scattering_values)
            & np.isfinite(green_fluorescence_values)
            & (scattering_values > 0.0)
            & (green_fluorescence_values <= baseline_cutoff)
        )

        non_fluorescent_scattering_values = scattering_values[non_fluorescent_mask]
        non_fluorescent_fluorescence_values = green_fluorescence_values[non_fluorescent_mask]

        non_fluorescent_analysis = find_fit_validate_peaks_1d(
            values=non_fluorescent_scattering_values,
            peak_count=resolved_peak_count,
            minimum_peak_fraction=minimum_peak_fraction,
            minimum_events_per_peak=minimum_events_per_peak,
            fit_r2_threshold=scatter_fit_r2_threshold,
            fit_cv_threshold=scatter_fit_cv_threshold,
            saturation_intensity=float("inf"),
        )
        non_fluorescent_diagnostic = build_peak_analysis_diagnostic_text(
            analysis=non_fluorescent_analysis,
            label="scatter",
        )

        non_fluorescent_validated_peaks = non_fluorescent_analysis["validated_peaks"]

        if not non_fluorescent_validated_peaks:
            return self._build_stop_result(
                status=(
                    "No validated non-fluorescent scatter peaks found. "
                    "Stopping Rosetta workflow. "
                    f"{non_fluorescent_diagnostic}"
                ),
                fluorescence_analysis=fluorescence_analysis,
                baseline_lower_gate=baseline_lower_gate,
                baseline_upper_gate=baseline_upper_gate,
                marker_points=marker_points,
                plot_scattering_values=scattering_values,
                plot_fluorescence_values=green_fluorescence_values,
            )

        non_fluorescent_scatter_positions = [
            float(peak["mean"])
            for peak in non_fluorescent_validated_peaks
        ]

        non_fluorescent_points = build_peak_display_points(
            scattering_values=non_fluorescent_scattering_values,
            fluorescence_values=non_fluorescent_fluorescence_values,
            scatter_peak_positions=non_fluorescent_scatter_positions,
            default_y=float(baseline_peak["mean"]),
            kind="non_fluorescent",
        )

        labels: list[str] = []
        for index, _ in enumerate(non_fluorescent_points, start=1):
            labels.append(f"Non-fluorescent peak {index}")

        for marker_point in marker_points:
            labels.append(str(marker_point.get("label", "Marker peak")))

        all_points = [*non_fluorescent_points, *marker_points]
        scatter_guide_positions = unique_sorted_finite_values(
            [
                *non_fluorescent_scatter_positions,
                *marker_scatter_guide_positions,
            ]
        )
        fluorescence_guide_positions = unique_sorted_finite_values(
            [
                float(peak["mean"])
                for peak in marker_peaks
            ]
        )

        peak_lines_payload = {
            "positions": [float(point["x"]) for point in all_points],
            "x_positions": [float(point["x"]) for point in all_points],
            "y_positions": [float(point["y"]) for point in all_points],
            "plot_x_values": scattering_values.astype(float).tolist(),
            "plot_y_values": green_fluorescence_values.astype(float).tolist(),
            "points": [
                {
                    "x": float(point["x"]),
                    "y": float(point["y"]),
                    "kind": str(point.get("kind", "peak")),
                }
                for point in all_points
            ],
            "labels": labels,
            "scatter_guide_positions": scatter_guide_positions,
            "fluorescence_guide_positions": fluorescence_guide_positions,
            "baseline_cutoff": baseline_cutoff,
            "y_lower_gate": baseline_lower_gate,
            "y_upper_gate": baseline_upper_gate,
            "fluorescence_saturation_intensity": float(fluorescence_saturation_intensity),
        }

        status_lines = [
            (
                f"Fluorescence peaks: {len(fluorescence_validated_peaks)} total "
                f"(1 baseline + {len(marker_peaks)} marker); "
                f"non-fluorescent scatter peaks: {len(non_fluorescent_points)}."
            ),
            f"Baseline cutoff={baseline_cutoff:.6g}.",
            (
                "Only non-fluorescent scatter peaks are inserted into the table; "
                "marker peaks are shown for orientation."
                if table_non_fluorescent_only
                else
                "Both non-fluorescent scatter peaks and marker-associated scatter peaks "
                "are inserted into the table."
            ),
            non_fluorescent_diagnostic,
        ]

        if remove_saturated_events:
            status_lines.append(
                f"Saturated-event filter removed {removed_saturated_event_count} event(s)."
            )

        table_points = (
            non_fluorescent_points
            if table_non_fluorescent_only
            else all_points
        )

        if saturation_guard_enabled:
            (
                table_points,
                removed_saturation_guard_peak_count,
                saturation_guard_threshold,
                scattering_saturation_value,
                scattering_saturation_source,
            ) = (
                filter_table_points_by_saturation_guard(
                    table_points=table_points,
                    backend=backend,
                    scattering_column=str(scattering_column),
                    saturation_guard_fraction=saturation_guard_fraction,
                    scattering_values=scattering_values,
                )
            )
        else:
            removed_saturation_guard_peak_count = 0
            saturation_guard_threshold = None
            scattering_saturation_value = None
            scattering_saturation_source = None

        if removed_saturation_guard_peak_count > 0 and saturation_guard_threshold is not None:
            saturation_context_suffix = (
                (
                    f" (scatter saturation used={float(scattering_saturation_value):.6g}, "
                    f"guard fraction={float(saturation_guard_fraction):.6g}, "
                    f"channel={str(scattering_column)}, "
                    f"saturation source={str(scattering_saturation_source or 'unknown')})."
                )
                if scattering_saturation_value is not None
                else
                "."
            )

            status_lines.append(
                f"Saturation guard excluded {removed_saturation_guard_peak_count} table peak(s) "
                f"above {saturation_guard_threshold:.6g}{saturation_context_suffix}"
            )

        status = "\n".join(
            line
            for line in status_lines
            if str(line or "").strip()
        )

        return PeakProcessResult(
            peak_positions=[
                {
                    "x": float(point["x"]),
                    "y": float(point["y"]),
                }
                for point in table_points
            ],
            new_peak_positions=[
                float(point["x"])
                for point in table_points
            ],
            peak_lines_payload=peak_lines_payload,
            status=status,
            clear_existing_table_peaks=False,
            table_prefill_rows=[
                {
                    "measured_peak_position": float(point["x"]),
                    "particle_diameter_nm": float(index),
                }
                for index, point in enumerate(table_points, start=1)
            ],
        )

    def _build_stop_result(
        self,
        *,
        status: str,
        fluorescence_analysis: Optional[dict[str, Any]] = None,
        baseline_lower_gate: Optional[float] = None,
        baseline_upper_gate: Optional[float] = None,
        marker_points: Optional[list[dict[str, float]]] = None,
        plot_scattering_values: Optional[np.ndarray] = None,
        plot_fluorescence_values: Optional[np.ndarray] = None,
    ) -> PeakProcessResult:
        """
        Build a stop result with optional diagnostic payload.
        """
        payload = self.build_empty_peak_lines_payload()

        if fluorescence_analysis is not None:
            payload["fluorescence_peak_count"] = int(
                len(fluorescence_analysis.get("validated_peaks", []))
            )

        if baseline_lower_gate is not None and np.isfinite(baseline_lower_gate):
            payload["y_lower_gate"] = float(baseline_lower_gate)

        if baseline_upper_gate is not None and np.isfinite(baseline_upper_gate):
            payload["baseline_cutoff"] = float(baseline_upper_gate)
            payload["y_upper_gate"] = float(baseline_upper_gate)

        if marker_points:
            payload["points"] = [
                {
                    "x": float(point["x"]),
                    "y": float(point["y"]),
                    "kind": str(point.get("kind", "marker")),
                }
                for point in marker_points
            ]
            payload["x_positions"] = [float(point["x"]) for point in marker_points]
            payload["y_positions"] = [float(point["y"]) for point in marker_points]
            payload["positions"] = [float(point["x"]) for point in marker_points]
            payload["labels"] = [
                str(point.get("label", "Marker peak"))
                for point in marker_points
            ]
            payload["scatter_guide_positions"] = unique_sorted_finite_values(
                [float(point["x"]) for point in marker_points]
            )
            payload["fluorescence_guide_positions"] = unique_sorted_finite_values(
                [float(point["y"]) for point in marker_points]
            )

        if plot_scattering_values is not None and plot_fluorescence_values is not None:
            payload["plot_x_values"] = np.asarray(
                plot_scattering_values,
                dtype=float,
            ).tolist()
            payload["plot_y_values"] = np.asarray(
                plot_fluorescence_values,
                dtype=float,
            ).tolist()

        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=payload,
            status=status,
            new_peak_positions=[],
            clear_existing_table_peaks=False,
        )

    def _empty_result(
        self,
        *,
        status: str,
        clear_existing_table_peaks: bool,
    ) -> PeakProcessResult:
        """
        Build an empty process result.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status=status,
            new_peak_positions=[],
            clear_existing_table_peaks=clear_existing_table_peaks,
        )

    def clear_peaks(self) -> PeakProcessResult:
        """
        Clear all detected peaks.
        """
        return PeakProcessResult(
            peak_positions=[],
            peak_lines_payload=self.build_empty_peak_lines_payload(),
            status="Cleared Rosetta fluorescence-guided scatter peaks.",
            new_peak_positions=[],
            clear_existing_table_peaks=True,
        )

    def build_empty_peak_lines_payload(self) -> dict[str, Any]:
        """
        Build an empty payload.
        """
        return {
            "positions": [],
            "x_positions": [],
            "y_positions": [],
            "plot_x_values": [],
            "plot_y_values": [],
            "points": [],
            "labels": [],
            "scatter_guide_positions": [],
            "fluorescence_guide_positions": [],
        }


def unique_sorted_finite_values(values: list[float]) -> list[float]:
    """
    Return sorted unique finite floats with near-duplicate values collapsed.
    """
    resolved_values: list[float] = []

    for raw_value in values:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(value):
            continue

        if any(np.isclose(value, existing_value, rtol=0.0, atol=max(abs(existing_value) * 1e-6, 1e-9)) for existing_value in resolved_values):
            continue

        resolved_values.append(value)

    return sorted(resolved_values)


def resolve_integer(
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

    return max(int(minimum), min(int(maximum), int(resolved_value)))


def resolve_float(
    *,
    value: Any,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Resolve a bounded floating-point value.
    """
    try:
        resolved_value = float(value)
    except (TypeError, ValueError):
        resolved_value = float(default)

    if not np.isfinite(resolved_value):
        resolved_value = float(default)

    return max(float(minimum), min(float(maximum), float(resolved_value)))


def resolve_enabled_setting(
    *,
    value: Any,
    default: bool,
) -> bool:
    """
    Resolve one checkbox/switch style setting into a boolean.
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value == "enabled"

    if isinstance(value, (list, tuple, set)):
        return "enabled" in value

    return bool(default)


def resolve_saturation_intensity(
    *,
    values: np.ndarray,
    saturation_quantile: float,
) -> float:
    """
    Estimate saturation intensity from a high fluorescence quantile.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return float("inf")

    return float(np.quantile(values, float(saturation_quantile)))


def build_saturated_event_mask(
    *,
    scattering_values: np.ndarray,
    fluorescence_values: np.ndarray,
) -> np.ndarray:
    """
    Return a mask for obvious detector-floor and detector-ceiling pile-up events.

    Saturation is approximated from strong pile-ups at detector edges:
    - fluorescence minimum
    - scatter minimum
    - scatter maximum
    """
    scattering_values = np.asarray(scattering_values, dtype=float)
    fluorescence_values = np.asarray(fluorescence_values, dtype=float)

    if scattering_values.size == 0 or fluorescence_values.size == 0:
        return np.zeros_like(scattering_values, dtype=bool)

    fluorescence_floor_mask = build_edge_pileup_mask(
        values=fluorescence_values,
        edge="min",
    )
    scatter_floor_mask = build_edge_pileup_mask(
        values=scattering_values,
        edge="min",
    )
    scatter_ceiling_mask = build_edge_pileup_mask(
        values=scattering_values,
        edge="max",
    )

    return fluorescence_floor_mask | scatter_floor_mask | scatter_ceiling_mask


def filter_table_points_by_saturation_guard(
    *,
    table_points: list[dict[str, float]],
    backend: Any,
    scattering_column: str,
    saturation_guard_fraction: float,
    scattering_values: np.ndarray,
) -> tuple[list[dict[str, float]], int, float | None, float | None, str | None]:
    if not np.isfinite(float(saturation_guard_fraction)):
        return list(table_points), 0, None, None, None

    if float(saturation_guard_fraction) <= 0.0:
        return list(table_points), 0, None, None, None

    (
        scattering_saturation_value,
        scattering_saturation_source,
    ) = resolve_scattering_saturation_value_for_guard(
        backend=backend,
        detector_column=scattering_column,
        scattering_values=scattering_values,
    )

    if scattering_saturation_value is None:
        return list(table_points), 0, None, None, scattering_saturation_source

    saturation_guard_threshold = float(scattering_saturation_value) * float(saturation_guard_fraction)

    if not np.isfinite(saturation_guard_threshold) or saturation_guard_threshold <= 0.0:
        return (
            list(table_points),
            0,
            None,
            float(scattering_saturation_value),
            scattering_saturation_source,
        )

    filtered_table_points: list[dict[str, float]] = []
    removed_peak_count = 0

    for table_point in table_points:
        x_value = float(table_point.get("x", 0.0))

        if np.isfinite(x_value) and x_value > saturation_guard_threshold:
            removed_peak_count += 1
            continue

        filtered_table_points.append(dict(table_point))

    return (
        filtered_table_points,
        removed_peak_count,
        saturation_guard_threshold,
        float(scattering_saturation_value),
        scattering_saturation_source,
    )


def resolve_scattering_saturation_value_for_guard(
    *,
    backend: Any,
    detector_column: str,
    scattering_values: np.ndarray,
) -> tuple[float | None, str | None]:
    metadata_saturation_value = resolve_detector_channel_saturation_value_from_metadata(
        backend=backend,
        detector_column=detector_column,
    )

    data_saturation_value = resolve_scattering_saturation_value_from_data(
        scattering_values=scattering_values,
    )

    if metadata_saturation_value is None:
        return None, None

    if data_saturation_value is None:
        return float(metadata_saturation_value), "metadata"

    if metadata_saturation_value <= 1.0 and data_saturation_value > 1.0:
        logger.debug(
            "Ignoring suspicious scatter metadata saturation=%r for detector=%r; using data fallback=%r.",
            metadata_saturation_value,
            detector_column,
            data_saturation_value,
        )
        return float(data_saturation_value), "data-fallback"

    if metadata_saturation_value < (data_saturation_value * 0.05):
        logger.debug(
            "Ignoring low scatter metadata saturation=%r for detector=%r compared to data scale=%r; using data fallback.",
            metadata_saturation_value,
            detector_column,
            data_saturation_value,
        )
        return float(data_saturation_value), "data-fallback"

    return float(metadata_saturation_value), "metadata"


def resolve_scattering_saturation_value_from_data(
    *,
    scattering_values: np.ndarray,
) -> float | None:
    resolved_values = np.asarray(scattering_values, dtype=float)

    if resolved_values.size == 0:
        return None

    finite_values = resolved_values[np.isfinite(resolved_values)]

    if finite_values.size == 0:
        return None

    finite_maximum = float(np.max(finite_values))

    if not np.isfinite(finite_maximum) or finite_maximum <= 0.0:
        return None

    return finite_maximum


def resolve_detector_channel_saturation_value_from_metadata(
    *,
    backend: Any,
    detector_column: str,
) -> float | None:
    uploaded_fcs_path = str(
        getattr(backend, "fcs_file_path", "") or "",
    ).strip()

    if not uploaded_fcs_path:
        return None

    normalized_detector_column = str(detector_column or "").strip().lower()

    if not normalized_detector_column:
        return None

    try:
        with FCSFile(uploaded_fcs_path) as fcs_file:
            metadata = fcs_file.get_metadata()
    except Exception:
        logger.debug(
            "Could not read metadata saturation for detector_column=%r fcs=%r",
            detector_column,
            uploaded_fcs_path,
            exc_info=True,
        )
        return None

    for detector in metadata.detectors.values():
        detector_name = str(detector.get("N", "")).strip().lower()

        if detector_name != normalized_detector_column:
            continue

        try:
            detector_saturation_value = float(detector.get("R"))
        except (TypeError, ValueError):
            return None

        if not np.isfinite(detector_saturation_value) or detector_saturation_value <= 0.0:
            return None

        return float(detector_saturation_value)

    return None


def build_edge_pileup_mask(
    *,
    values: np.ndarray,
    edge: str,
    quantile: float = 0.9995,
    minimum_fraction: float = 0.001,
) -> np.ndarray:
    """
    Detect a pile-up at one detector edge and return the affected-event mask.
    """
    return shared_build_edge_pileup_mask(
        values=values,
        edge=edge,
        quantile=quantile,
        minimum_fraction=minimum_fraction,
    )


def build_peak_analysis_diagnostic_text(
    *,
    analysis: Optional[dict[str, Any]],
    label: str,
) -> str:
    """
    Build a short user-facing diagnostic summary for one peak analysis pass.
    """
    if not isinstance(analysis, dict):
        return ""

    all_peaks = analysis.get("all_peaks")
    validated_peaks = analysis.get("validated_peaks")

    if not isinstance(all_peaks, list):
        all_peaks = []

    if not isinstance(validated_peaks, list):
        validated_peaks = []

    rejected_peak_count = max(0, len(all_peaks) - len(validated_peaks))
    resolved_label = str(label).strip() or "signal"
    rejected_peak_details = build_rejected_peak_diagnostic_details(
        all_peaks=all_peaks,
    )

    diagnostic_text = (
        f"{resolved_label.title()} analysis: "
        f"{len(all_peaks)} candidate peak(s), "
        f"{len(validated_peaks)} validated, "
        f"{rejected_peak_count} rejected."
    )

    if rejected_peak_details:
        diagnostic_text = f"{diagnostic_text} Rejected: {rejected_peak_details}"

    return diagnostic_text


def build_rejected_peak_diagnostic_details(
    *,
    all_peaks: list[dict[str, Any]],
    maximum_peaks: int = 3,
) -> str:
    """
    Summarize why candidate peaks were rejected.
    """
    rejected_segments: list[str] = []

    for peak in all_peaks:
        if bool(peak.get("validated")):
            continue

        rejection_reasons = peak.get("rejection_reasons")

        if not isinstance(rejection_reasons, list) or not rejection_reasons:
            rejection_reasons = ["validation failed"]

        mean_value = float(peak.get("mean", 0.0))
        reason_text = ", ".join(str(reason) for reason in rejection_reasons if str(reason).strip())

        rejected_segments.append(
            f"peak at {mean_value:.3g} ({reason_text})"
        )

        if len(rejected_segments) >= int(maximum_peaks):
            break

    return "; ".join(rejected_segments)


def build_peak_rejection_reasons(
    *,
    fit_count: int,
    minimum_events_per_peak: int,
    fit_r2: float,
    fit_r2_threshold: float,
    fit_cv: float,
    fit_cv_threshold: float,
    fit_mean: float,
    saturation_intensity: float,
) -> list[str]:
    """
    Return user-facing validation failures for one fitted peak.
    """
    rejection_reasons: list[str] = []

    if fit_count < int(minimum_events_per_peak):
        rejection_reasons.append(
            f"count {fit_count} < {int(minimum_events_per_peak)}"
        )

    if fit_r2 < float(fit_r2_threshold):
        rejection_reasons.append(
            f"R2 {fit_r2:.2f} < {float(fit_r2_threshold):.2f}"
        )

    if fit_cv > float(fit_cv_threshold):
        rejection_reasons.append(
            f"CV {fit_cv:.2f} > {float(fit_cv_threshold):.2f}"
        )

    if fit_mean >= float(saturation_intensity):
        rejection_reasons.append(
            f"mean {fit_mean:.3g} >= saturation cutoff {float(saturation_intensity):.3g}"
        )

    return rejection_reasons


def find_fit_validate_peaks_1d(
    *,
    values: np.ndarray,
    peak_count: int,
    minimum_peak_fraction: float,
    minimum_prominence_fraction: float = 0.03,
    minimum_events_per_peak: int,
    fit_r2_threshold: float,
    fit_cv_threshold: float,
    saturation_intensity: float,
) -> dict[str, Any]:
    """
    Find, fit, and validate 1D peaks.

    Workflow:
    - Build a log-binned histogram and detect candidate peaks.
    - Build a region of interest around each candidate.
    - Build a linearly binned ROI histogram.
    - Fit a Gaussian using weighted moments and evaluate quality.
    - Validate using R2, CV, saturation, and minimum event count.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values > 0.0)]

    if values.size == 0:
        return {
            "all_peaks": [],
            "validated_peaks": [],
        }

    log_values = np.log10(values)

    histogram_bin_count = min(
        256,
        max(64, int(np.sqrt(log_values.size))),
    )

    counts, bin_edges = np.histogram(log_values, bins=histogram_bin_count)

    if counts.size == 0:
        return {
            "all_peaks": [],
            "validated_peaks": [],
        }

    smoothed_counts = smooth_counts(counts=np.asarray(counts, dtype=float), window_size=7)
    candidate_peak_indices = find_local_maxima_indices(values=smoothed_counts)

    if not candidate_peak_indices:
        candidate_peak_indices = [
            int(index)
            for index in np.argsort(smoothed_counts)[-int(peak_count):]
        ]

    maximum_count = float(np.max(smoothed_counts))

    candidate_peak_indices = [
        int(index)
        for index in candidate_peak_indices
        if smoothed_counts[int(index)] >= maximum_count * float(minimum_peak_fraction)
    ]

    candidate_peak_indices = filter_candidate_peak_indices_by_prominence(
        counts=smoothed_counts,
        candidate_peak_indices=candidate_peak_indices,
        minimum_prominence=maximum_count * float(minimum_prominence_fraction),
    )

    selected_peak_indices = select_well_separated_peak_indices(
        candidate_peak_indices=candidate_peak_indices,
        weights=smoothed_counts,
        peak_count=peak_count,
        minimum_index_distance=6,
    )

    all_peaks: list[dict[str, float]] = []

    for peak_index in selected_peak_indices:
        if peak_index < 0 or peak_index >= len(bin_edges) - 1:
            continue

        log_peak_center = 0.5 * (bin_edges[peak_index] + bin_edges[peak_index + 1])
        log_peak_half_width = estimate_log_peak_half_width(
            smoothed_counts=smoothed_counts,
            peak_index=peak_index,
            bin_edges=bin_edges,
            minimum_half_width=0.05,
        )

        log_roi_low = log_peak_center - 2.0 * log_peak_half_width
        log_roi_high = log_peak_center + 2.0 * log_peak_half_width

        roi_mask = (log_values >= log_roi_low) & (log_values <= log_roi_high)
        roi_values = values[roi_mask]

        gaussian_fit = fit_gaussian_from_values(
            values=roi_values,
            minimum_events=max(5, minimum_events_per_peak // 2),
            use_log_space=True,
        )

        if gaussian_fit is None:
            continue

        fit_mean = float(gaussian_fit["mean"])
        fit_std = float(gaussian_fit["std"])
        fit_cv = float(gaussian_fit["cv"])
        fit_r2 = float(gaussian_fit["r2"])
        fit_count = int(gaussian_fit["count"])
        rejection_reasons = build_peak_rejection_reasons(
            fit_count=fit_count,
            minimum_events_per_peak=minimum_events_per_peak,
            fit_r2=fit_r2,
            fit_r2_threshold=fit_r2_threshold,
            fit_cv=fit_cv,
            fit_cv_threshold=fit_cv_threshold,
            fit_mean=fit_mean,
            saturation_intensity=saturation_intensity,
        )

        is_valid = len(rejection_reasons) == 0

        all_peaks.append(
            {
                "mean": fit_mean,
                "std": fit_std,
                "cv": fit_cv,
                "r2": fit_r2,
                "count": fit_count,
                "validated": bool(is_valid),
                "rejection_reasons": rejection_reasons,
            }
        )

    all_peaks_sorted = sorted(all_peaks, key=lambda peak: float(peak["mean"]))

    validated_peaks = [
        peak
        for peak in all_peaks_sorted
        if bool(peak["validated"])
    ]

    return {
        "all_peaks": all_peaks_sorted,
        "validated_peaks": validated_peaks,
    }


def estimate_log_peak_half_width(
    *,
    smoothed_counts: np.ndarray,
    peak_index: int,
    bin_edges: np.ndarray,
    minimum_half_width: float,
) -> float:
    """
    Estimate half-width for one log-domain histogram peak.
    """
    peak_height = float(smoothed_counts[peak_index])

    if peak_height <= 0.0:
        return float(minimum_half_width)

    half_height = 0.5 * peak_height

    left_index = int(peak_index)
    while left_index > 0 and smoothed_counts[left_index] > half_height:
        left_index -= 1

    right_index = int(peak_index)
    max_right_index = int(smoothed_counts.size - 1)
    while right_index < max_right_index and smoothed_counts[right_index] > half_height:
        right_index += 1

    left_edge = float(bin_edges[max(0, left_index)])
    right_edge = float(bin_edges[min(len(bin_edges) - 1, right_index + 1)])

    half_width = 0.5 * max(right_edge - left_edge, 0.0)

    return float(max(half_width, float(minimum_half_width)))


def fit_gaussian_from_values(
    *,
    values: np.ndarray,
    minimum_events: int,
    use_log_space: bool = False,
) -> Optional[dict[str, float]]:
    """
    Fit a Gaussian to ROI values using histogram moments.

    When ``use_log_space`` is True the fit is performed on log10(values) and
    the mean and std are converted back to linear space afterwards.  This gives
    accurate R² values for log-normal scattering data where a linear-bin fit
    would always appear skewed.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size < int(minimum_events):
        return None

    if use_log_space:
        values = values[values > 0.0]
        if values.size < int(minimum_events):
            return None
        fit_values = np.log10(values)
    else:
        fit_values = values

    value_min = float(np.min(fit_values))
    value_max = float(np.max(fit_values))

    if not np.isfinite(value_min) or not np.isfinite(value_max) or value_max <= value_min:
        return None

    bin_count = int(min(128, max(20, int(np.sqrt(fit_values.size)))))
    counts, edges = np.histogram(fit_values, bins=bin_count)

    if counts.size < 3 or float(np.sum(counts)) <= 0.0:
        return None

    centers = 0.5 * (edges[:-1] + edges[1:])
    y_values = np.asarray(counts, dtype=float)

    weight_sum = float(np.sum(y_values))
    if weight_sum <= 0.0:
        return None

    mean_fit = float(np.sum(centers * y_values) / weight_sum)

    variance = float(np.sum(((centers - mean_fit) ** 2) * y_values) / weight_sum)
    std_fit = float(np.sqrt(max(variance, 0.0)))

    if not np.isfinite(std_fit) or std_fit <= 0.0:
        return None

    basis = np.exp(-0.5 * ((centers - mean_fit) / std_fit) ** 2)
    basis_energy = float(np.sum(basis * basis))

    if basis_energy <= 0.0:
        return None

    amplitude = float(np.sum(y_values * basis) / basis_energy)
    modeled = amplitude * basis

    residual = y_values - modeled
    sse = float(np.sum(residual * residual))
    y_mean = float(np.mean(y_values))
    sst = float(np.sum((y_values - y_mean) ** 2))

    if sst <= 0.0:
        r2_value = 1.0 if sse <= 0.0 else 0.0
    else:
        r2_value = 1.0 - sse / sst

    if use_log_space:
        # Convert log10-space mean and std back to linear space.
        # mean_linear = 10^mean_log10
        # std_linear = mean_linear * sinh(std_log10 * ln(10))  (exact for log-normal)
        mean_value = float(10.0 ** mean_fit)
        std_value = float(mean_value * np.sinh(std_fit * np.log(10.0)))
    else:
        mean_value = mean_fit
        std_value = std_fit

    cv_value = float("inf")
    if mean_value != 0.0:
        cv_value = float(abs(std_value / mean_value))

    return {
        "mean": float(mean_value),
        "std": float(std_value),
        "cv": float(cv_value),
        "r2": float(r2_value),
        "count": int(fit_values.size),
    }


def resolve_baseline_peak(
    *,
    peaks: list[dict[str, float]],
) -> dict[str, float]:
    """
    Resolve baseline fluorescence peak.

    The baseline noise peak is expected to have the highest event count.
    """
    if not peaks:
        raise ValueError("Expected at least one fluorescence peak.")

    return max(
        peaks,
        key=lambda peak: (
            float(peak.get("count", 0.0)),
            -float(peak.get("mean", 0.0)),
        ),
    )


def classify_marker_peaks(
    *,
    marker_peaks: list[dict[str, float]],
) -> list[dict[str, float]]:
    """
    Classify marker peaks as dim or bright.

    The lowest (or only) fluorescent marker is always the 140 nm dim marker,
    because the 380 nm bright marker is the more intense population and can
    saturate the fluorescence detector, so it can never be the faintest peak.
    """
    marker_peaks_sorted = sorted(
        marker_peaks,
        key=lambda peak: float(peak.get("mean", 0.0)),
    )

    classified: list[dict[str, float]] = []

    for marker_index, marker_peak in enumerate(marker_peaks_sorted):
        classified_peak = dict(marker_peak)

        if marker_index == 0:
            classified_peak["marker_role"] = "Dim marker"
        else:
            classified_peak["marker_role"] = "Bright marker"

        classified.append(classified_peak)

    return classified


def build_sigma_gate_mask(
    *,
    values: np.ndarray,
    mean_value: float,
    std_value: float,
    sigma_multiplier: float,
) -> np.ndarray:
    """
    Build a symmetric sigma gate mask.
    """
    values = np.asarray(values, dtype=float)

    safe_std = max(float(std_value), max(abs(mean_value) * 0.01, 1e-6))
    half_width = float(sigma_multiplier) * safe_std

    lower_bound = float(mean_value) - half_width
    upper_bound = float(mean_value) + half_width

    return (
        np.isfinite(values)
        & (values >= lower_bound)
        & (values <= upper_bound)
    )


def select_primary_validated_peak(
    *,
    values: np.ndarray,
    peak_count: int,
    minimum_peak_fraction: float,
    minimum_events_per_peak: int,
    fit_r2_threshold: float,
    fit_cv_threshold: float,
) -> Optional[dict[str, float]]:
    """
    Return the strongest validated peak from one 1D dataset.
    """
    analysis = find_fit_validate_peaks_1d(
        values=values,
        peak_count=peak_count,
        minimum_peak_fraction=minimum_peak_fraction,
        minimum_events_per_peak=minimum_events_per_peak,
        fit_r2_threshold=fit_r2_threshold,
        fit_cv_threshold=fit_cv_threshold,
        saturation_intensity=float("inf"),
    )

    validated = analysis["validated_peaks"]

    if not validated:
        return None

    return max(
        validated,
        key=lambda peak: float(peak.get("count", 0.0)),
    )


def build_peak_display_points(
    *,
    scattering_values: np.ndarray,
    fluorescence_values: np.ndarray,
    scatter_peak_positions: list[float],
    default_y: float,
    kind: str,
) -> list[dict[str, float]]:
    """
    Build 2D display points from scatter peak positions.
    """
    scattering_values = np.asarray(scattering_values, dtype=float)
    fluorescence_values = np.asarray(fluorescence_values, dtype=float)

    valid_mask = (
        np.isfinite(scattering_values)
        & np.isfinite(fluorescence_values)
        & (scattering_values > 0.0)
    )

    scattering_values = scattering_values[valid_mask]
    fluorescence_values = fluorescence_values[valid_mask]

    if scattering_values.size == 0:
        return [
            {
                "x": float(x_position),
                "y": float(default_y),
                "kind": str(kind),
            }
            for x_position in scatter_peak_positions
        ]

    log_scattering_values = np.log10(scattering_values)

    points: list[dict[str, float]] = []

    for scatter_peak_position in scatter_peak_positions:
        if scatter_peak_position <= 0.0:
            continue

        target_log = float(np.log10(scatter_peak_position))

        local_mask = np.abs(log_scattering_values - target_log) <= 0.05

        if np.count_nonzero(local_mask) >= 5:
            y_value = float(np.median(fluorescence_values[local_mask]))
        else:
            y_value = float(default_y)

        points.append(
            {
                "x": float(scatter_peak_position),
                "y": float(y_value),
                "kind": str(kind),
            }
        )

    return points


def select_well_separated_peak_indices(
    *,
    candidate_peak_indices: list[int],
    weights: np.ndarray,
    peak_count: int,
    minimum_index_distance: int,
) -> list[int]:
    """
    Select strongest peaks while enforcing a minimum histogram-bin distance.
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

        selected_peak_indices.append(int(candidate_peak_index))

        if len(selected_peak_indices) >= int(peak_count):
            break

    return sorted(selected_peak_indices)


def smooth_counts(
    *,
    counts: np.ndarray,
    window_size: int,
) -> np.ndarray:
    """
    Smooth histogram counts with a moving-average kernel.
    """
    counts = np.asarray(counts, dtype=float)

    if counts.size < 3:
        return counts

    resolved_window_size = max(3, int(window_size))

    if resolved_window_size % 2 == 0:
        resolved_window_size += 1

    if counts.size < resolved_window_size:
        resolved_window_size = counts.size

        if resolved_window_size % 2 == 0:
            resolved_window_size -= 1

    if resolved_window_size < 3:
        return counts

    kernel = np.ones(resolved_window_size, dtype=float) / float(resolved_window_size)

    return np.convolve(counts, kernel, mode="same")


def find_local_maxima_indices(
    *,
    values: np.ndarray,
) -> list[int]:
    """
    Find local maxima indices for 1D data.
    """
    values = np.asarray(values, dtype=float)

    maxima_indices: list[int] = []

    for index in range(1, values.size - 1):
        if values[index] >= values[index - 1] and values[index] >= values[index + 1]:
            maxima_indices.append(index)

    return maxima_indices


def filter_candidate_peak_indices_by_prominence(
    *,
    counts: np.ndarray,
    candidate_peak_indices: list[int],
    minimum_prominence: float,
) -> list[int]:
    """
    Keep only candidate peaks that rise meaningfully above nearby valleys.
    """
    counts = np.asarray(counts, dtype=float)

    if counts.size < 3 or not candidate_peak_indices:
        return []

    prominences = estimate_peak_prominences(
        counts=counts,
        candidate_peak_indices=candidate_peak_indices,
    )

    filtered_indices: list[int] = []

    for index, prominence in zip(candidate_peak_indices, prominences):
        if float(prominence) >= float(minimum_prominence):
            filtered_indices.append(int(index))

    return filtered_indices


def estimate_peak_prominences(
    *,
    counts: np.ndarray,
    candidate_peak_indices: list[int],
) -> np.ndarray:
    """
    Estimate local peak prominence above the larger neighboring valley floor.
    """
    counts = np.asarray(counts, dtype=float)
    prominences: list[float] = []

    for candidate_peak_index in candidate_peak_indices:
        left_minimum = find_left_valley_minimum(
            counts=counts,
            peak_index=int(candidate_peak_index),
        )
        right_minimum = find_right_valley_minimum(
            counts=counts,
            peak_index=int(candidate_peak_index),
        )

        valley_minima = [
            float(value)
            for value in (left_minimum, right_minimum)
            if value is not None and np.isfinite(value)
        ]

        baseline = max(valley_minima) if valley_minima else 0.0
        prominence = float(counts[int(candidate_peak_index)] - baseline)
        prominences.append(max(0.0, prominence))

    return np.asarray(prominences, dtype=float)


def find_left_valley_minimum(
    *,
    counts: np.ndarray,
    peak_index: int,
) -> Optional[float]:
    """
    Find the left-side valley minimum for one histogram peak.
    """
    peak_height = float(counts[peak_index])
    left_index = int(peak_index)

    while left_index > 0 and counts[left_index] <= peak_height:
        left_index -= 1
        if counts[left_index] > peak_height:
            break

    left_slice = counts[left_index: peak_index + 1]

    if left_slice.size == 0:
        return None

    return float(np.min(left_slice))


def find_right_valley_minimum(
    *,
    counts: np.ndarray,
    peak_index: int,
) -> Optional[float]:
    """
    Find the right-side valley minimum for one histogram peak.
    """
    peak_height = float(counts[peak_index])

    if peak_index >= counts.size - 1:
        return None

    right_index = int(peak_index)

    while right_index < counts.size - 1 and counts[right_index] <= peak_height:
        right_index += 1
        if counts[right_index] > peak_height:
            break

    right_slice = counts[peak_index: right_index + 1]

    if right_slice.size == 0:
        return None

    return float(np.min(right_slice))


PROCESS = FluorescenceGuidedScatterPeakProcess()
