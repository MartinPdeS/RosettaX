import logging
import numpy as np
from .base import (
    BasePeakProcess,
    PeakProcessResult,
)
from .rosetta_mix_algorithms import (  # noqa: F401
    build_edge_pileup_mask,
    build_peak_analysis_diagnostic_text,
    build_peak_display_points,
    build_peak_rejection_reasons,
    build_rejected_peak_diagnostic_details,
    build_saturated_event_mask,
    build_sigma_gate_mask,
    classify_marker_peaks,
    estimate_log_peak_half_width,
    estimate_peak_prominences,
    filter_candidate_peak_indices_by_prominence,
    filter_table_points_by_saturation_guard,
    find_fit_validate_peaks_1d,
    find_left_valley_minimum,
    find_local_maxima_indices,
    find_right_valley_minimum,
    fit_gaussian_from_values,
    resolve_baseline_peak,
    resolve_detector_channel_saturation_value_from_metadata,
    resolve_enabled_setting,
    resolve_float,
    resolve_integer,
    resolve_saturation_intensity,
    resolve_scattering_saturation_value_from_data,
    select_well_separated_peak_indices,
    smooth_counts,
    unique_sorted_finite_values,
)
from .rosetta_mix_algorithms import (
    resolve_scattering_saturation_value_for_guard as _resolve_scattering_saturation_value_for_guard,
)
from .rosetta_mix_algorithms import (
    select_primary_validated_peak as _select_primary_validated_peak,
)
from .rosetta_mix_models import (
    DEFAULT_BASELINE_SIGMA_MULTIPLIER,
    RosettaEventData,
    RosettaFluorescenceAnalysis,
    RosettaMarkerScatter,
    RosettaRunSettings,
    RosettaScatterAnalysis,
)
from RosettaX.utils.io import column_copy
from typing import Any

logger = logging.getLogger(__name__)


def select_primary_validated_peak(
    *,
    values: np.ndarray,
    peak_count: int,
    minimum_peak_fraction: float,
    minimum_events_per_peak: int,
    fit_r2_threshold: float,
    fit_cv_threshold: float,
) -> dict[str, float] | None:
    """Select a validated peak using the facade's replaceable fit function."""
    return _select_primary_validated_peak(
        values=values,
        peak_count=peak_count,
        minimum_peak_fraction=minimum_peak_fraction,
        minimum_events_per_peak=minimum_events_per_peak,
        fit_r2_threshold=fit_r2_threshold,
        fit_cv_threshold=fit_cv_threshold,
        fit_function=find_fit_validate_peaks_1d,
    )


def resolve_scattering_saturation_value_for_guard(
    *,
    backend: Any,
    detector_column: str,
    scattering_values: np.ndarray,
) -> tuple[float | None, str | None]:
    """Resolve saturation while honoring helpers patched through this facade."""
    return _resolve_scattering_saturation_value_for_guard(
        backend=backend,
        detector_column=detector_column,
        scattering_values=scattering_values,
        metadata_resolver=resolve_detector_channel_saturation_value_from_metadata,
        data_resolver=resolve_scattering_saturation_value_from_data,
    )


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
                "default_value": DEFAULT_BASELINE_SIGMA_MULTIPLIER,
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
                    "peaks or plotted events. Example: 0.5 means 4,000,000 "
                    "saturation becomes a 2,000,000 table threshold."
                ),
                "default_value": 0.5,
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
    ) -> PeakProcessResult | None:
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

        settings = RosettaRunSettings.from_raw_values(
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=process_settings,
        )
        events = load_rosetta_events(
            backend=backend,
            scattering_column=str(scattering_column),
            green_fluorescence_column=str(green_fluorescence_column),
            settings=settings,
        )
        if events.scattering_values.size == 0:
            return self._empty_result(
                status="No finite events are available for automatic detection.",
                clear_existing_table_peaks=False,
            )
        fluorescence = analyze_rosetta_fluorescence(events=events, settings=settings)
        if fluorescence.stop_status is not None:
            return self._build_stop_result(
                status=fluorescence.stop_status,
                fluorescence_analysis=fluorescence.analysis,
                baseline_lower_gate=fluorescence.baseline_lower_gate,
                baseline_upper_gate=fluorescence.baseline_upper_gate,
                plot_scattering_values=events.scattering_values,
                plot_fluorescence_values=events.fluorescence_values,
            )
        markers = find_marker_scatter_points(
            events=events,
            fluorescence=fluorescence,
            settings=settings,
        )
        scatter = analyze_non_fluorescent_scatter(
            events=events,
            fluorescence=fluorescence,
            settings=settings,
        )
        if scatter.stop_status is not None:
            return self._build_stop_result(
                status=scatter.stop_status,
                fluorescence_analysis=fluorescence.analysis,
                baseline_lower_gate=fluorescence.baseline_lower_gate,
                baseline_upper_gate=fluorescence.baseline_upper_gate,
                marker_points=markers.points,
                plot_scattering_values=events.scattering_values,
                plot_fluorescence_values=events.fluorescence_values,
            )
        return build_rosetta_detection_result(
            backend=backend,
            scattering_column=str(scattering_column),
            settings=settings,
            events=events,
            fluorescence=fluorescence,
            markers=markers,
            scatter=scatter,
        )

    def _build_stop_result(
        self,
        *,
        status: str,
        fluorescence_analysis: dict[str, Any] | None = None,
        baseline_lower_gate: float | None = None,
        baseline_upper_gate: float | None = None,
        marker_points: list[dict[str, float]] | None = None,
        plot_scattering_values: np.ndarray | None = None,
        plot_fluorescence_values: np.ndarray | None = None,
    ) -> PeakProcessResult:
        """
        Build a stop result with optional diagnostic payload.
        """
        payload = self.build_empty_peak_lines_payload()

        if fluorescence_analysis is not None:
            payload["fluorescence_peak_count"] = len(
                fluorescence_analysis.get("validated_peaks", [])
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
                str(point.get("label", "Marker peak")) for point in marker_points
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


def load_rosetta_events(
    *,
    backend: Any,
    scattering_column: str,
    green_fluorescence_column: str,
    settings: RosettaRunSettings,
) -> RosettaEventData:
    """Read paired signals and apply the configured saturated-event filter."""
    scattering_values = np.asarray(
        column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(scattering_column),
            dtype=float,
            n=settings.max_events_for_analysis,
        ),
        dtype=float,
    )
    green_fluorescence_values = np.asarray(
        column_copy(
            fcs_file_path=backend.fcs_file_path,
            detector_column=str(green_fluorescence_column),
            dtype=float,
            n=settings.max_events_for_analysis,
        ),
        dtype=float,
    )
    finite_mask = np.isfinite(scattering_values) & np.isfinite(
        green_fluorescence_values
    )
    scattering_values = scattering_values[finite_mask]
    green_fluorescence_values = green_fluorescence_values[finite_mask]
    removed_saturated_event_count = 0
    if settings.remove_saturated_events:
        saturation_mask = build_saturated_event_mask(
            scattering_values=scattering_values,
            fluorescence_values=green_fluorescence_values,
        )
        removed_saturated_event_count = int(np.count_nonzero(saturation_mask))
        if removed_saturated_event_count > 0:
            keep_mask = ~saturation_mask
            scattering_values = scattering_values[keep_mask]
            green_fluorescence_values = green_fluorescence_values[keep_mask]
    return RosettaEventData(
        scattering_values, green_fluorescence_values, removed_saturated_event_count
    )


def resolve_marker_stop_status(marker_count: int, diagnostic: str) -> str | None:
    """Accept one or two fluorescent marker populations after baseline removal."""
    if marker_count == 0 or marker_count >= 3:
        return (
            f"{marker_count} fluorescent marker peaks found after removing baseline. "
            f"Stopping Rosetta workflow. {diagnostic}"
        )
    return None


def analyze_rosetta_fluorescence(
    *, events: RosettaEventData, settings: RosettaRunSettings
) -> RosettaFluorescenceAnalysis:
    """Fit fluorescence populations and resolve baseline and marker gates."""
    baseline_peak = None
    marker_peaks = []
    baseline_lower_gate = None
    baseline_upper_gate = None
    fluorescence_saturation_intensity = resolve_saturation_intensity(
        values=events.fluorescence_values,
        saturation_quantile=settings.fluorescence_saturation_quantile,
    )
    fluorescence_analysis = find_fit_validate_peaks_1d(
        values=events.fluorescence_values,
        peak_count=3,
        minimum_peak_fraction=settings.minimum_peak_fraction,
        minimum_events_per_peak=settings.minimum_events_per_peak,
        fit_r2_threshold=settings.fit_r2_threshold,
        fit_cv_threshold=settings.fit_cv_threshold,
        saturation_intensity=fluorescence_saturation_intensity,
    )
    fluorescence_validated_peaks = fluorescence_analysis["validated_peaks"]
    fluorescence_diagnostic = build_peak_analysis_diagnostic_text(
        analysis=fluorescence_analysis, label="fluorescence"
    )
    if not fluorescence_validated_peaks:
        return RosettaFluorescenceAnalysis(
            analysis=fluorescence_analysis,
            baseline_peak=baseline_peak,
            marker_peaks=marker_peaks,
            baseline_lower_gate=baseline_lower_gate,
            baseline_upper_gate=baseline_upper_gate,
            saturation_intensity=fluorescence_saturation_intensity,
            stop_status=(
                "No validated fluorescence peaks found. "
                "Unable to identify fluorescent marker populations. "
                f"{fluorescence_diagnostic}"
            ),
        )
    baseline_peak = resolve_baseline_peak(peaks=fluorescence_validated_peaks)
    baseline_lower_gate = float(
        max(
            0.0,
            baseline_peak["mean"]
            - settings.baseline_sigma_multiplier * max(baseline_peak["std"], 1e-12),
        )
    )
    baseline_upper_gate = float(
        baseline_peak["mean"]
        + settings.baseline_sigma_multiplier * max(baseline_peak["std"], 1e-12)
    )
    marker_peaks = [
        peak for peak in fluorescence_validated_peaks if peak is not baseline_peak
    ]
    marker_stop_status = resolve_marker_stop_status(
        len(marker_peaks), fluorescence_diagnostic
    )
    if marker_stop_status is not None:
        return RosettaFluorescenceAnalysis(
            analysis=fluorescence_analysis,
            baseline_peak=baseline_peak,
            marker_peaks=marker_peaks,
            baseline_lower_gate=baseline_lower_gate,
            baseline_upper_gate=baseline_upper_gate,
            saturation_intensity=fluorescence_saturation_intensity,
            stop_status=marker_stop_status,
        )
    return RosettaFluorescenceAnalysis(
        analysis=fluorescence_analysis,
        baseline_peak=baseline_peak,
        marker_peaks=marker_peaks,
        baseline_lower_gate=baseline_lower_gate,
        baseline_upper_gate=baseline_upper_gate,
        saturation_intensity=fluorescence_saturation_intensity,
    )


def find_marker_scatter_points(
    *,
    events: RosettaEventData,
    fluorescence: RosettaFluorescenceAnalysis,
    settings: RosettaRunSettings,
) -> RosettaMarkerScatter:
    """Fit scatter peaks inside the accepted fluorescent marker gates."""
    marker_classification = classify_marker_peaks(
        marker_peaks=fluorescence.marker_peaks
    )
    marker_points: list[dict[str, float]] = []
    marker_scatter_guide_positions: list[float] = []
    for marker_peak in marker_classification:
        marker_gate_mask = build_sigma_gate_mask(
            values=events.fluorescence_values,
            mean_value=marker_peak["mean"],
            std_value=marker_peak["std"],
            sigma_multiplier=settings.marker_gate_sigma_multiplier,
        )
        gated_scatter_values = events.scattering_values[marker_gate_mask]
        scatter_peak = select_primary_validated_peak(
            values=gated_scatter_values,
            peak_count=1,
            minimum_peak_fraction=settings.minimum_peak_fraction,
            minimum_events_per_peak=settings.minimum_events_per_peak,
            fit_r2_threshold=settings.scatter_fit_r2_threshold,
            fit_cv_threshold=settings.scatter_fit_cv_threshold,
        )
        if scatter_peak is None:
            continue
        marker_scatter_guide_positions.append(float(scatter_peak["mean"]))
        marker_points.append(
            {
                "x": float(scatter_peak["mean"]),
                "y": float(marker_peak["mean"]),
                "kind": "marker",
                "label": str(marker_peak["marker_role"]),
            }
        )
    return RosettaMarkerScatter(marker_points, marker_scatter_guide_positions)


def analyze_non_fluorescent_scatter(
    *,
    events: RosettaEventData,
    fluorescence: RosettaFluorescenceAnalysis,
    settings: RosettaRunSettings,
) -> RosettaScatterAnalysis:
    """Fit baseline-gated scatter populations and build their display points."""
    non_fluorescent_points = []
    non_fluorescent_scatter_positions = []
    non_fluorescent_mask = (
        np.isfinite(events.scattering_values)
        & np.isfinite(events.fluorescence_values)
        & (events.scattering_values > 0.0)
        & (events.fluorescence_values <= fluorescence.baseline_upper_gate)
    )
    non_fluorescent_scattering_values = events.scattering_values[non_fluorescent_mask]
    non_fluorescent_fluorescence_values = events.fluorescence_values[
        non_fluorescent_mask
    ]
    non_fluorescent_analysis = find_fit_validate_peaks_1d(
        values=non_fluorescent_scattering_values,
        peak_count=settings.peak_count,
        minimum_peak_fraction=settings.minimum_peak_fraction,
        minimum_events_per_peak=settings.minimum_events_per_peak,
        fit_r2_threshold=settings.scatter_fit_r2_threshold,
        fit_cv_threshold=settings.scatter_fit_cv_threshold,
        saturation_intensity=float("inf"),
    )
    non_fluorescent_diagnostic = build_peak_analysis_diagnostic_text(
        analysis=non_fluorescent_analysis, label="scatter"
    )
    non_fluorescent_validated_peaks = non_fluorescent_analysis["validated_peaks"]
    if not non_fluorescent_validated_peaks:
        return RosettaScatterAnalysis(
            analysis=non_fluorescent_analysis,
            points=non_fluorescent_points,
            positions=non_fluorescent_scatter_positions,
            diagnostic=non_fluorescent_diagnostic,
            stop_status=f"No validated non-fluorescent scatter peaks found. Stopping Rosetta workflow. {non_fluorescent_diagnostic}",
        )
    non_fluorescent_scatter_positions = [
        float(peak["mean"]) for peak in non_fluorescent_validated_peaks
    ]
    non_fluorescent_points = build_peak_display_points(
        scattering_values=non_fluorescent_scattering_values,
        fluorescence_values=non_fluorescent_fluorescence_values,
        scatter_peak_positions=non_fluorescent_scatter_positions,
        default_y=float(fluorescence.baseline_peak["mean"]),
        kind="non_fluorescent",
    )
    return RosettaScatterAnalysis(
        analysis=non_fluorescent_analysis,
        points=non_fluorescent_points,
        positions=non_fluorescent_scatter_positions,
        diagnostic=non_fluorescent_diagnostic,
    )


def build_rosetta_detection_result(
    *,
    backend: Any,
    scattering_column: str,
    settings: RosettaRunSettings,
    events: RosettaEventData,
    fluorescence: RosettaFluorescenceAnalysis,
    markers: RosettaMarkerScatter,
    scatter: RosettaScatterAnalysis,
) -> PeakProcessResult:
    """Assemble overlays, table points, and diagnostic text from detection stages."""
    labels: list[str] = []
    for index, _ in enumerate(scatter.points, start=1):
        labels.append(f"Non-fluorescent peak {index}")
    for marker_point in markers.points:
        labels.append(str(marker_point.get("label", "Marker peak")))
    all_points = [*scatter.points, *markers.points]
    scatter_guide_positions = unique_sorted_finite_values(
        [*scatter.positions, *markers.guide_positions]
    )
    fluorescence_guide_positions = unique_sorted_finite_values(
        [float(peak["mean"]) for peak in fluorescence.marker_peaks]
    )
    peak_lines_payload = {
        "positions": [float(point["x"]) for point in all_points],
        "x_positions": [float(point["x"]) for point in all_points],
        "y_positions": [float(point["y"]) for point in all_points],
        "plot_x_values": events.scattering_values.astype(float).tolist(),
        "plot_y_values": events.fluorescence_values.astype(float).tolist(),
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
        "baseline_cutoff": fluorescence.baseline_upper_gate,
        "y_lower_gate": fluorescence.baseline_lower_gate,
        "y_upper_gate": fluorescence.baseline_upper_gate,
        "fluorescence_saturation_intensity": float(fluorescence.saturation_intensity),
    }
    status_lines = [
        (
            f"Fluorescence peaks: {len(fluorescence.analysis['validated_peaks'])} total "
            f"(1 baseline + {len(fluorescence.marker_peaks)} marker); "
            f"non-fluorescent scatter peaks: {len(scatter.points)}."
        ),
        f"Baseline cutoff={fluorescence.baseline_upper_gate:.6g}.",
        (
            "Only non-fluorescent scatter peaks are inserted into the table; "
            "marker peaks are shown for orientation."
            if settings.table_non_fluorescent_only
            else "Both non-fluorescent scatter peaks and marker-associated scatter peaks "
            "are inserted into the table."
        ),
        scatter.diagnostic,
    ]
    if settings.remove_saturated_events:
        status_lines.append(
            f"Saturated-event filter removed {events.removed_saturated_event_count} event(s)."
        )
    table_points = scatter.points if settings.table_non_fluorescent_only else all_points
    if settings.saturation_guard_enabled:
        (
            table_points,
            removed_saturation_guard_peak_count,
            saturation_guard_threshold,
            scattering_saturation_value,
            scattering_saturation_source,
        ) = filter_table_points_by_saturation_guard(
            table_points=table_points,
            backend=backend,
            scattering_column=str(scattering_column),
            saturation_guard_fraction=settings.saturation_guard_fraction,
            scattering_values=events.scattering_values,
            saturation_resolver=resolve_scattering_saturation_value_for_guard,
        )
    else:
        removed_saturation_guard_peak_count = 0
        saturation_guard_threshold = None
        scattering_saturation_value = None
        scattering_saturation_source = None
    if (
        removed_saturation_guard_peak_count > 0
        and saturation_guard_threshold is not None
    ):
        saturation_context_suffix = (
            (
                f" (scatter saturation used={float(scattering_saturation_value):.6g}, "
                f"guard fraction={float(settings.saturation_guard_fraction):.6g}, "
                f"channel={scattering_column!s}, "
                f"saturation source={scattering_saturation_source or 'unknown'!s})."
            )
            if scattering_saturation_value is not None
            else "."
        )
        status_lines.append(
            f"Saturation guard excluded {removed_saturation_guard_peak_count} table peak(s) "
            f"above {saturation_guard_threshold:.6g}{saturation_context_suffix}"
        )
    status = "\n".join(line for line in status_lines if str(line or "").strip())
    return PeakProcessResult(
        peak_positions=[
            {"x": float(point["x"]), "y": float(point["y"])} for point in table_points
        ],
        new_peak_positions=[float(point["x"]) for point in table_points],
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


PROCESS = FluorescenceGuidedScatterPeakProcess()
