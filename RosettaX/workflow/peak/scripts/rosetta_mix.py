"""Fluorescence-guided Rosetta detection pipeline and process controls."""

import logging
import numpy as np
from ..core.process_calls import standard_peak_action
from ._events import filter_finite_peak_events, read_peak_event_columns
from .base import (
    BasePeakProcess,
    PeakProcessResult,
)
from .rosetta_mix_diagnostics import (  # noqa: F401
    build_rosetta_debug_diagnostics,
    extract_marker_candidate_fluorescence_diagnostics,
    extract_marker_candidate_fluorescence_positions,
)
from .rosetta_mix_fitting import (  # noqa: F401
    build_peak_analysis_diagnostic_text,
    build_peak_display_points,
    build_peak_rejection_reasons,
    build_rejected_peak_diagnostic_details,
    build_sigma_gate_mask,
    classify_marker_peaks,
    estimate_log_peak_half_width,
    estimate_peak_prominences,
    filter_candidate_peak_indices_by_prominence,
    find_fit_validate_peaks_1d,
    find_left_valley_minimum,
    find_local_maxima_indices,
    find_right_valley_minimum,
    find_separated_fluorescence_gate,
    fit_gaussian_from_values,
    resolve_baseline_peak,
    select_well_separated_peak_indices,
    smooth_counts,
)
from .rosetta_mix_fitting import (
    select_primary_validated_peak as _select_primary_validated_peak,
)
from .rosetta_mix_models import (
    ROSETTA_SETTINGS,
    MarkerScatterDiagnostic,
    RosettaDetectionIssue,
    RosettaEventData,
    RosettaFluorescenceAnalysis,
    RosettaMarkerScatter,
    RosettaPeakPoint,
    RosettaPlotSource,
    RosettaRunSettings,
    RosettaScatterAnalysis,
)
from .rosetta_mix_support import (  # noqa: F401
    build_edge_pileup_mask,
    build_saturated_event_mask,
    filter_table_points_by_saturation_guard,
    resolve_detector_channel_saturation_value_from_metadata,
    resolve_enabled_setting,
    resolve_float,
    resolve_integer,
    resolve_saturation_intensity,
    resolve_scattering_saturation_value_from_data,
    unique_sorted_finite_values,
)
from .rosetta_mix_support import (
    resolve_scattering_saturation_value_for_guard as _resolve_scattering_saturation_value_for_guard,
)
from collections.abc import Callable
from dataclasses import replace
from functools import partial
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
        """Return the definitions used for both controls and detection."""
        return [dict(setting) for setting in ROSETTA_SETTINGS.values()]


    @standard_peak_action
    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
        max_events_for_plots: Any = None,
        runtime_config_data: Any = None,
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
                status="Select the scatter channel used to measure the Rosetta beads, then run peak detection again.",
                clear_existing_table_peaks=False,
            )

        if not str(green_fluorescence_column or "").strip():
            return self._empty_result(
                status="Select the green fluorescence channel used to identify the Rosetta marker beads, then run peak detection again.",
                clear_existing_table_peaks=False,
            )

        settings = RosettaRunSettings.from_raw_values(
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=process_settings,
        )
        recover_clipped_marker = getattr(self, "recover_clipped_marker", False)
        events = load_rosetta_events(
            backend=backend,
            scattering_column=str(scattering_column),
            green_fluorescence_column=str(green_fluorescence_column),
            settings=settings,
            retain_scatter_edges=recover_clipped_marker,
        )
        if events.scattering_values.size == 0:
            return self._build_stop_result(
                status="The selected scatter and fluorescence channels have no usable paired events after filtering. Check the selected channels and inspect the raw event plot.",
                issue=RosettaDetectionIssue.EVENTS_MISSING,
                event_counts=events.event_counts(),
            )
        fluorescence = analyze_rosetta_fluorescence(events=events, settings=settings)
        if (
            recover_clipped_marker and len(fluorescence.marker_peaks) == 1
            and events.fluorescence_with_scatter_edges is not None
        ):
            inclusive_fluorescence = analyze_rosetta_fluorescence(
                events=replace(events, fluorescence_values=events.fluorescence_with_scatter_edges),
                settings=settings,
            )
            original_marker = fluorescence.marker_peaks[0]
            if len(inclusive_fluorescence.marker_peaks) == 2 and any(
                abs(candidate["mean"] - original_marker["mean"]) <= original_marker["std"]
                for candidate in inclusive_fluorescence.marker_peaks
            ):
                fluorescence = inclusive_fluorescence
        if fluorescence.stop_status is not None:
            return self._build_stop_result(
                issue=fluorescence.issue,
                event_counts=events.event_counts(),
                status=(
                    f"{fluorescence.stop_status} Green channel: {green_fluorescence_column}. "
                    "Inspect its histogram for separated peaks above the baseline and for events piled up at the fluorescence ceiling."
                ),
                fluorescence_analysis=fluorescence.analysis,
                debug_diagnostics=build_rosetta_debug_diagnostics(
                    fluorescence_analysis=fluorescence.analysis,
                    fluorescence_baseline_peak=fluorescence.baseline_peak,
                    fluorescence_saturation_intensity=fluorescence.saturation_intensity,
                    settings=settings,
                ),
                fluorescence_marker_candidates=(
                    extract_marker_candidate_fluorescence_diagnostics(
                        fluorescence=fluorescence,
                    )
                ),
                fluorescence_marker_positions=(
                    extract_marker_candidate_fluorescence_positions(
                        fluorescence=fluorescence,
                    )
                ),
                baseline_lower_gate=fluorescence.baseline_lower_gate,
                baseline_upper_gate=fluorescence.baseline_upper_gate,
                plot_events=events,
            )
        markers = find_marker_scatter_points(
            events=events,
            fluorescence=fluorescence,
            settings=settings,
            fit_function=getattr(self, "scatter_fit_function", None),
            recover_clipped_marker=recover_clipped_marker,
        )
        scatter_fit_function = getattr(self, "scatter_fit_function", None)
        regional_fit = getattr(self, "fit_marker_bounded_scatter", None)
        if regional_fit is not None:
            scatter_fit_function = partial(
                regional_fit,
                marker_diagnostics=markers.diagnostics,
                fluorescence_saturation=fluorescence.saturation_intensity,
            )
        scatter = analyze_non_fluorescent_scatter(
            events=events,
            fluorescence=fluorescence,
            settings=settings,
            fit_function=scatter_fit_function,
        )
        if scatter.stop_status is not None:
            return self._build_stop_result(
                issue=RosettaDetectionIssue.SCATTER_MISSING,
                event_counts=dict(events.event_counts(), baseline_gated=scatter.gated_event_count),
                status=(
                    f"{scatter.stop_status} Scatter channel: {scattering_column}. "
                    f"The fluorescence gate retained events at or below {fluorescence.baseline_upper_gate:.4g} a.u. "
                    "Inspect the gated scatter histogram and check that the baseline gate includes the non-fluorescent beads."
                ),
                fluorescence_analysis=fluorescence.analysis,
                debug_diagnostics=build_rosetta_debug_diagnostics(
                    fluorescence_analysis=fluorescence.analysis,
                    fluorescence_baseline_peak=fluorescence.baseline_peak,
                    fluorescence_saturation_intensity=fluorescence.saturation_intensity,
                    marker_scatter_diagnostics=markers.diagnostics,
                    scatter_analysis=scatter.analysis,
                    settings=settings,
                ),
                fluorescence_marker_candidates=(
                    extract_marker_candidate_fluorescence_diagnostics(
                        fluorescence=fluorescence,
                    )
                ),
                fluorescence_marker_positions=(
                    extract_marker_candidate_fluorescence_positions(
                        fluorescence=fluorescence,
                    )
                ),
                marker_scatter_diagnostics=markers.diagnostics,
                baseline_lower_gate=fluorescence.baseline_lower_gate,
                baseline_upper_gate=fluorescence.baseline_upper_gate,
                marker_points=markers.points,
                plot_events=events,
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
        issue: RosettaDetectionIssue | None = None,
        event_counts: dict[str, Any] | None = None,
        fluorescence_analysis: dict[str, Any] | None = None,
        debug_diagnostics: dict[str, Any] | None = None,
        fluorescence_marker_candidates: list[dict[str, Any]] | None = None,
        fluorescence_marker_positions: list[float] | None = None,
        marker_scatter_diagnostics: list[dict[str, Any]] | None = None,
        baseline_lower_gate: float | None = None,
        baseline_upper_gate: float | None = None,
        marker_points: list[dict[str, float]] | None = None,
        plot_events: RosettaEventData | None = None,
    ) -> PeakProcessResult:
        """
        Build a stop result with optional diagnostic payload.
        """
        payload = self.build_empty_peak_lines_payload()
        marker_positions = list(fluorescence_marker_positions or [])
        if issue is not None:
            payload["rosetta_detection_issue"] = issue.value
        if event_counts is not None:
            payload["rosetta_event_counts"] = event_counts
        if debug_diagnostics:
            payload["rosetta_debug_diagnostics"] = debug_diagnostics

        if fluorescence_analysis is not None:
            validated_fluorescence_peaks = fluorescence_analysis.get(
                "validated_peaks",
                [],
            )
            payload["fluorescence_peak_count"] = len(validated_fluorescence_peaks)
            if len(validated_fluorescence_peaks) > 1:
                baseline_peak = resolve_baseline_peak(
                    peaks=validated_fluorescence_peaks,
                )
                marker_positions.extend(
                    float(peak["mean"])
                    for peak in validated_fluorescence_peaks
                    if peak is not baseline_peak
                )

        if fluorescence_marker_candidates:
            payload["fluorescence_marker_candidates"] = fluorescence_marker_candidates
        if marker_scatter_diagnostics:
            payload["marker_scatter_diagnostics"] = marker_scatter_diagnostics

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
            marker_positions.extend(
                float(point["y"])
                for point in marker_points
            )

        payload["fluorescence_guide_positions"] = unique_sorted_finite_values(
            marker_positions
        )

        if plot_events is not None:
            payload.update(plot_events.plot_payload())

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
    retain_scatter_edges: bool = False,
) -> RosettaEventData:
    """Read paired signals and retain clipped events separately for marker identification."""
    return read_rosetta_events(
        source=RosettaPlotSource(
            fcs_file_path=str(backend.fcs_file_path),
            scattering_column=scattering_column,
            green_fluorescence_column=green_fluorescence_column,
            max_events_for_analysis=settings.max_events_for_analysis,
            remove_saturated_events=settings.remove_saturated_events,
        ),
        retain_scatter_edges=retain_scatter_edges,
    )


def read_rosetta_events(
    *, source: RosettaPlotSource, retain_scatter_edges: bool = False,
) -> RosettaEventData:
    """Apply the same event selection for detection and plotting.

    Parameters
    ----------
    source : RosettaPlotSource
        File, detector channels, event limit, and detector edge filtering.
    retain_scatter_edges : bool, optional
        Keep separate signals for detecting clipped fluorescent markers.

    Returns
    -------
    RosettaEventData
        Aligned detector signals in detector units, with filtering diagnostics.
    """
    columns = read_peak_event_columns(
        fcs_file_path=source["fcs_file_path"],
        detector_columns=(source["scattering_column"], source["green_fluorescence_column"]),
        max_events=source["max_events_for_analysis"],
        read_column=column_copy,
    )
    (scattering_values, green_fluorescence_values), removed_nonfinite = filter_finite_peak_events(columns=columns)
    scatter_edge_values = {}
    scatter_edge_fluorescence = {}
    if retain_scatter_edges and scattering_values.size:
        for edge, resolve_extreme in (("min", np.min), ("max", np.max)):
            edge_mask = build_edge_pileup_mask(values=scattering_values, edge=edge)
            if np.any(edge_mask):
                scatter_edge_values[edge] = float(resolve_extreme(scattering_values))
                scatter_edge_fluorescence[edge] = green_fluorescence_values[edge_mask]

    fluorescence_with_scatter_edges = None
    if scatter_edge_fluorescence and source["remove_saturated_events"]:
        fluorescence_floor = build_edge_pileup_mask(values=green_fluorescence_values, edge="min")
        fluorescence_with_scatter_edges = green_fluorescence_values[~fluorescence_floor]

    removed_saturated_event_count = 0
    if source["remove_saturated_events"]:
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
        scattering_values, green_fluorescence_values, removed_saturated_event_count,
        scatter_edge_values, scatter_edge_fluorescence, fluorescence_with_scatter_edges,
        removed_nonfinite_event_count=removed_nonfinite,
        plot_source=source,
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
    *, events: RosettaEventData, settings: RosettaRunSettings,
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
    fit_options = dict(
        minimum_peak_fraction=settings.minimum_peak_fraction,
        minimum_events_per_peak=settings.minimum_events_per_peak,
        fit_r2_threshold=settings.fit_r2_threshold,
        fit_cv_threshold=settings.fit_cv_threshold,
        saturation_intensity=fluorescence_saturation_intensity,
    )
    fluorescence_analysis = find_fit_validate_peaks_1d(
        values=events.fluorescence_values, peak_count=3, **fit_options,
    )
    fluorescence_validated_peaks = fluorescence_analysis["validated_peaks"]
    fluorescence_diagnostic = build_peak_analysis_diagnostic_text(
        analysis=fluorescence_analysis, label="fluorescence"
    )
    if not fluorescence_validated_peaks:
        # Quantized baseline bins can fill every candidate slot. Recover only
        # when a wide gap supports treating the dim band as one baseline.
        cutoff = find_separated_fluorescence_gate(
            values=events.fluorescence_values, minimum_events=settings.minimum_events_per_peak,
        )
        if cutoff is not None:
            marker_fit = find_fit_validate_peaks_1d(
                values=events.fluorescence_values[events.fluorescence_values > cutoff],
                peak_count=3, **fit_options,
            )
            recovered_markers = marker_fit["validated_peaks"]
            if 1 <= len(recovered_markers) <= 2:
                values = events.fluorescence_values
                baseline = values[np.isfinite(values) & (values > 0) & (values <= cutoff)]
                baseline_peak = {
                    "mean": float(np.median(baseline)),
                    "count": int(baseline.size),
                    "validated": True,
                }
                return RosettaFluorescenceAnalysis(
                    analysis={
                        "all_peaks": [baseline_peak, *marker_fit["all_peaks"]],
                        "validated_peaks": [baseline_peak, *recovered_markers],
                    },
                    baseline_peak=baseline_peak,
                    marker_peaks=recovered_markers,
                    baseline_lower_gate=0.0,
                    baseline_upper_gate=cutoff,
                    saturation_intensity=fluorescence_saturation_intensity,
                )
        return RosettaFluorescenceAnalysis(
            analysis=fluorescence_analysis,
            baseline_peak=baseline_peak,
            marker_peaks=marker_peaks,
            baseline_lower_gate=baseline_lower_gate,
            baseline_upper_gate=baseline_upper_gate,
            saturation_intensity=fluorescence_saturation_intensity,
            issue=RosettaDetectionIssue.FLUORESCENCE_MISSING,
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
            issue=RosettaDetectionIssue.MARKER_AMBIGUOUS if marker_peaks else RosettaDetectionIssue.MARKER_MISSING,
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
    fit_function: Callable[..., dict[str, Any]] | None = None,
    recover_clipped_marker: bool = False,
) -> RosettaMarkerScatter:
    """Fit scatter peaks inside the accepted fluorescent marker gates.

    Parameters
    ----------
    events : RosettaEventData
        Paired scatter and fluorescence intensities in arbitrary units.
    fluorescence : RosettaFluorescenceAnalysis
        Accepted marker populations and baseline gate.
    settings : RosettaRunSettings
        Detection thresholds and gate widths.
    fit_function : Callable or None, optional
        Alternative fitter using the existing peak-analysis dictionary contract.
        ``None`` preserves the original histogram fitter.
    recover_clipped_marker : bool, optional
        Fit the scatter distribution of events at a separated fluorescence ceiling.

    Returns
    -------
    RosettaMarkerScatter
        Validated marker positions and fit diagnostics.
    """
    resolve_fit_function = fit_function or find_fit_validate_peaks_1d
    marker_classification = classify_marker_peaks(
        marker_peaks=fluorescence.marker_peaks
    )
    marker_points: list[RosettaPeakPoint] = []
    marker_scatter_guide_positions: list[float] = []
    marker_scatter_diagnostics: list[MarkerScatterDiagnostic] = []
    if recover_clipped_marker and marker_classification:
        clipped = build_edge_pileup_mask(values=events.fluorescence_values, edge="max")
        dim = marker_classification[0]
        ceiling = float(events.fluorescence_values.max())
        dim_upper_gate = dim["mean"] + settings.marker_gate_sigma_multiplier * dim["std"]
        bright = marker_classification[1] if len(marker_classification) == 2 else None
        bright_gate_reaches_ceiling = bright is None or (
            bright["mean"] + settings.marker_gate_sigma_multiplier * bright["std"] >= ceiling
        )
        if (
            bright_gate_reaches_ceiling
            and np.count_nonzero(clipped) >= settings.minimum_events_per_peak
            and ceiling > fluorescence.baseline_upper_gate
            and np.all(events.fluorescence_values[clipped] > dim_upper_gate)
        ):
            marker_classification = [dim, {
                "mean": ceiling, "std": 0.0, "marker_role": "Bright marker", "clipped_gate": clipped,
            }]
    marker_gates = [
        marker["clipped_gate"] if "clipped_gate" in marker else build_sigma_gate_mask(
            values=events.fluorescence_values,
            mean_value=marker["mean"],
            std_value=marker["std"],
            sigma_multiplier=settings.marker_gate_sigma_multiplier,
        )
        for marker in marker_classification
    ]
    gate_overlap = 0.0
    if len(marker_gates) == 2:
        first_gate, second_gate = marker_gates
        gate_overlap = np.count_nonzero(first_gate & second_gate) / max(
            1, min(np.count_nonzero(first_gate), np.count_nonzero(second_gate)),
        )
    for marker_peak, marker_gate_mask in zip(marker_classification, marker_gates, strict=True):
        clipped_gate = marker_peak.get("clipped_gate")
        gated_scatter_values = events.scattering_values[marker_gate_mask]
        gated_event_count = int(
            np.count_nonzero(
                np.isfinite(gated_scatter_values) & (gated_scatter_values > 0.0)
            )
        )
        if (
            recover_clipped_marker and settings.remove_saturated_events
            and len(marker_classification) == 2 and clipped_gate is None
        ):
            edge = "min" if marker_peak["marker_role"] == "Dim marker" else "max"
            edge_values = events.scatter_edge_fluorescence.get(edge)
            if edge_values is not None:
                edge_gate = build_sigma_gate_mask(
                    values=edge_values,
                    mean_value=marker_peak["mean"],
                    std_value=marker_peak["std"],
                    sigma_multiplier=settings.marker_gate_sigma_multiplier,
                )
                gated_edge_count = int(np.count_nonzero(edge_gate))
                if (
                    marker_peak["mean"] - settings.marker_gate_sigma_multiplier * marker_peak["std"]
                    > fluorescence.baseline_upper_gate
                    and gated_edge_count >= settings.minimum_events_per_peak
                    and gated_edge_count >= 0.70 * edge_values.size
                    and gated_edge_count >= 0.70 * (gated_event_count + gated_edge_count)
                ):
                    marker_scatter_diagnostics.append({
                        "marker_role": str(marker_peak["marker_role"]),
                        "fluorescence_position": float(marker_peak["mean"]),
                        "gated_event_count": gated_edge_count,
                        "validated": False,
                        "scatter_boundary": events.scatter_edge_values[edge],
                    })
                    continue
        select_peak = select_primary_validated_peak if fit_function is None else _select_primary_validated_peak
        fit_arguments = {} if fit_function is None else {"fit_function": resolve_fit_function}
        if clipped_gate is not None:
            clipped_analysis = resolve_fit_function(
                values=gated_scatter_values, peak_count=2,
                minimum_peak_fraction=settings.minimum_peak_fraction,
                minimum_events_per_peak=settings.minimum_events_per_peak,
                fit_r2_threshold=settings.scatter_fit_r2_threshold,
                fit_cv_threshold=settings.scatter_fit_cv_threshold,
                saturation_intensity=float("inf"),
            )
            validated = clipped_analysis["validated_peaks"]
            scatter_peak = (
                validated[0] if len(validated) == 1
                and validated[0]["count"] >= 0.70 * gated_event_count
                and not build_edge_pileup_mask(values=gated_scatter_values, edge="max").any()
                else None
            )
        else:
            scatter_peak = select_peak(
                **fit_arguments,
                values=gated_scatter_values,
                peak_count=1,
                minimum_peak_fraction=settings.minimum_peak_fraction,
                minimum_events_per_peak=settings.minimum_events_per_peak,
                fit_r2_threshold=settings.scatter_fit_r2_threshold,
                fit_cv_threshold=settings.scatter_fit_cv_threshold,
            )
        if scatter_peak is None:
            scatter_analysis = clipped_analysis if clipped_gate is not None else resolve_fit_function(
                values=gated_scatter_values,
                peak_count=1,
                minimum_peak_fraction=settings.minimum_peak_fraction,
                minimum_events_per_peak=settings.minimum_events_per_peak,
                fit_r2_threshold=settings.scatter_fit_r2_threshold,
                fit_cv_threshold=settings.scatter_fit_cv_threshold,
                saturation_intensity=float("inf"),
            )
            marker_scatter_diagnostics.append(
                {
                    "marker_role": str(marker_peak["marker_role"]),
                    "fluorescence_position": float(marker_peak["mean"]),
                    "gated_event_count": gated_event_count,
                    "validated": False,
                    "rejected_peaks": [
                        {
                            "mean": peak.get("mean"),
                            "count": peak.get("count"),
                            "r2": peak.get("r2"),
                            "cv": peak.get("cv"),
                            "rejection_reasons": list(
                                peak.get("rejection_reasons") or []
                            ),
                        }
                        for peak in scatter_analysis.get("all_peaks", [])
                        if not peak.get("validated")
                    ],
                }
            )
            continue
        marker_scatter_diagnostics.append(
            {
                "marker_role": str(marker_peak["marker_role"]),
                "fluorescence_position": float(marker_peak["mean"]),
                "gated_event_count": gated_event_count,
                "validated": True,
                "gate_overlap": float(gate_overlap),
                "above_baseline_fraction": float(np.count_nonzero(
                    marker_gate_mask & (events.fluorescence_values > fluorescence.baseline_upper_gate)
                ) / max(1, np.count_nonzero(marker_gate_mask))),
                "selected_peak": {
                    "mean": scatter_peak.get("mean"),
                    "count": scatter_peak.get("count"),
                    "r2": scatter_peak.get("r2"),
                    "cv": scatter_peak.get("cv"),
                    "bootstrap_positions": scatter_peak.get("bootstrap_positions"),
                },
                "rejected_peaks": [],
                "recovered_from_clipped_fluorescence": clipped_gate is not None,
            }
        )
        marker_scatter_guide_positions.append(float(scatter_peak["mean"]))
        marker_points.append(
            {
                "x": float(scatter_peak["mean"]),
                "y": float(marker_peak["mean"]),
                "kind": "marker",
                "label": str(marker_peak["marker_role"]),
            }
        )
    return RosettaMarkerScatter(
        points=marker_points,
        guide_positions=marker_scatter_guide_positions,
        diagnostics=marker_scatter_diagnostics,
    )


def analyze_non_fluorescent_scatter(
    *,
    events: RosettaEventData,
    fluorescence: RosettaFluorescenceAnalysis,
    settings: RosettaRunSettings,
    fit_function: Callable[..., dict[str, Any]] | None = None,
) -> RosettaScatterAnalysis:
    """Fit baseline-gated scatter populations and build their display points.

    Parameters
    ----------
    events : RosettaEventData
        Paired scatter and fluorescence intensities in arbitrary units.
    fluorescence : RosettaFluorescenceAnalysis
        Accepted baseline fluorescence gate.
    settings : RosettaRunSettings
        Detection thresholds and maximum peak count.
    fit_function : Callable or None, optional
        Alternative fitter using the existing peak-analysis dictionary contract.
        ``None`` preserves the original histogram fitter.

    Returns
    -------
    RosettaScatterAnalysis
        Accepted scatter positions, display points and validation outcomes.
    """
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
    resolve_fit_function = fit_function or find_fit_validate_peaks_1d
    non_fluorescent_analysis = resolve_fit_function(
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
            gated_event_count=non_fluorescent_scattering_values.size,
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
        gated_event_count=non_fluorescent_scattering_values.size,
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
    fluorescence_guide_positions = extract_marker_candidate_fluorescence_positions(
        fluorescence=fluorescence,
    )
    peak_lines_payload = {
        "rosetta_event_counts": dict(events.event_counts(), baseline_gated=scatter.gated_event_count),
        "positions": [float(point["x"]) for point in all_points],
        "x_positions": [float(point["x"]) for point in all_points],
        "y_positions": [float(point["y"]) for point in all_points],
        **events.plot_payload(),
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
        "fluorescence_marker_candidates": (
            extract_marker_candidate_fluorescence_diagnostics(
                fluorescence=fluorescence,
            )
        ),
        "marker_scatter_diagnostics": markers.diagnostics,
        "rosetta_debug_diagnostics": build_rosetta_debug_diagnostics(
            fluorescence_analysis=fluorescence.analysis,
            fluorescence_baseline_peak=fluorescence.baseline_peak,
            fluorescence_saturation_intensity=fluorescence.saturation_intensity,
            marker_scatter_diagnostics=markers.diagnostics,
            scatter_analysis=scatter.analysis,
            settings=settings,
        ),
        "baseline_cutoff": fluorescence.baseline_upper_gate,
        "y_lower_gate": fluorescence.baseline_lower_gate,
        "y_upper_gate": fluorescence.baseline_upper_gate,
        "fluorescence_saturation_intensity": float(fluorescence.saturation_intensity),
    }
    scatter_bootstrap = [
        {"position": peak["mean"], "replicates": peak["bootstrap_positions"]}
        for peak in scatter.analysis.get("validated_peaks", [])
        if "bootstrap_positions" in peak
    ]
    if scatter_bootstrap:
        peak_lines_payload["scatter_bootstrap_positions"] = scatter_bootstrap
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
        peak_lines_payload["saturation_guard_message"] = status_lines[-1]
    if saturation_guard_threshold is not None:
        peak_lines_payload["saturation_guard_threshold"] = saturation_guard_threshold
        peak_lines_payload["saturation_guard_excluded_positions"] = [
            float(point["x"]) for point in (
                scatter.points if settings.table_non_fluorescent_only else all_points
            ) if point["x"] > saturation_guard_threshold
        ]
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
                "particle_diameter_nm": "",
            }
            for point in table_points
        ],
    )


PROCESS = FluorescenceGuidedScatterPeakProcess()
