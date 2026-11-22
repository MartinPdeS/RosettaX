"""Rosetta fit diagnostics, anchor warnings, and failure plot payloads."""

import numpy as np
from .base import PeakProcessResult
from .rosetta_mix_fitting import resolve_baseline_peak
from .rosetta_mix_models import RosettaFluorescenceAnalysis, RosettaRunSettings
from .rosetta_mix_sizing import (
    BRIGHT_MARKER_DIAMETER_NM,
    DIM_MARKER_DIAMETER_NM,
    _as_positive_float,
    bright_marker_scatter_anchor_is_reliable,
    build_peak_metadata,
    extract_marker_anchor_positions,
)
from .rosetta_mix_support import unique_sorted_finite_values
from typing import Any


def extract_marker_candidate_fluorescence_positions(
    *,
    fluorescence: RosettaFluorescenceAnalysis,
) -> list[float]:
    """Return fluorescence candidate positions excluding the baseline peak.

    Parameters
    ----------
    fluorescence : RosettaFluorescenceAnalysis
        Fitted fluorescence populations, including rejected candidates.

    Returns
    -------
    list[float]
        Sorted candidate marker positions in fluorescence detector units.
    """
    return unique_sorted_finite_values(
        [
            float(peak["position"])
            for peak in extract_marker_candidate_fluorescence_diagnostics(
                fluorescence=fluorescence,
            )
        ]
    )


def extract_marker_candidate_fluorescence_diagnostics(
    *,
    fluorescence: RosettaFluorescenceAnalysis,
) -> list[dict[str, Any]]:
    """Return fit diagnostics for fluorescence candidates other than baseline.

    Parameters
    ----------
    fluorescence : RosettaFluorescenceAnalysis
        Fitted fluorescence populations, including rejected candidates.

    Returns
    -------
    list[dict[str, Any]]
        Candidate fit statistics and rejection reasons.
    """
    all_peaks = fluorescence.analysis.get("all_peaks", [])
    if not isinstance(all_peaks, list) or not all_peaks:
        return []

    baseline_peak = fluorescence.baseline_peak
    if baseline_peak is None:
        baseline_peak = resolve_baseline_peak(peaks=all_peaks)
    baseline_mean = float(baseline_peak["mean"])

    diagnostics: list[dict[str, Any]] = []
    for peak in all_peaks:
        if not isinstance(peak, dict):
            continue
        try:
            peak_mean = float(peak["mean"])
        except (KeyError, TypeError, ValueError):
            continue
        if not np.isfinite(peak_mean) or np.isclose(peak_mean, baseline_mean):
            continue
        diagnostics.append(
            {
                "position": peak_mean,
                "validated": bool(peak.get("validated", False)),
                "count": peak.get("count"),
                "r2": peak.get("r2"),
                "cv": peak.get("cv"),
                "rejection_reasons": list(peak.get("rejection_reasons") or []),
            }
        )
    return sorted(diagnostics, key=lambda item: item["position"])


def build_rosetta_debug_diagnostics(
    *,
    fluorescence_analysis: dict[str, Any],
    fluorescence_baseline_peak: dict[str, Any] | None,
    fluorescence_saturation_intensity: float,
    settings: RosettaRunSettings,
    marker_scatter_diagnostics: list[dict[str, Any]] | None = None,
    scatter_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build serializable fit details for the Custom Rosetta debug panel.

    Parameters
    ----------
    fluorescence_analysis : dict[str, Any]
        Fluorescence fit candidates and validation outcomes.
    fluorescence_baseline_peak : dict[str, Any] | None
        Baseline fluorescence fit, when one was validated.
    fluorescence_saturation_intensity : float
        Estimated detector saturation level in fluorescence units.
    settings : RosettaRunSettings
        Effective detection thresholds used for this run.
    marker_scatter_diagnostics : list[dict[str, Any]] | None, optional
        Marker-gated scatter fit summaries.
    scatter_analysis : dict[str, Any] | None, optional
        Baseline-gated scatter fit candidates and validation outcomes.

    Returns
    -------
    dict[str, Any]
        JSON-serializable diagnostics for display in the peak workflow.
    """
    fluorescence_peaks = fluorescence_analysis.get("all_peaks", [])
    fluorescence_peaks = (
        sorted(
            [peak for peak in fluorescence_peaks if isinstance(peak, dict)],
            key=lambda peak: float(peak.get("mean", 0.0)),
        )
        if isinstance(fluorescence_peaks, list)
        else []
    )
    baseline_mean = (
        float(fluorescence_baseline_peak["mean"])
        if isinstance(fluorescence_baseline_peak, dict)
        else None
    )
    marker_candidate_index = 0
    fluorescence_rows: list[dict[str, Any]] = []
    for peak in fluorescence_peaks:
        mean_value = float(peak.get("mean", 0.0))
        if baseline_mean is not None and np.isclose(mean_value, baseline_mean):
            population = "Baseline"
        else:
            marker_candidate_index += 1
            population = (
                "Dim marker candidate"
                if marker_candidate_index == 1
                else "Bright marker candidate"
                if marker_candidate_index == 2
                else f"Fluorescence candidate {marker_candidate_index}"
            )
        fluorescence_rows.append(
            {
                "population": population,
                "position": mean_value,
                "events": peak.get("count"),
                "r2": peak.get("r2"),
                "cv": peak.get("cv"),
                "validated": bool(peak.get("validated", False)),
                "rejection_reasons": list(peak.get("rejection_reasons") or []),
            }
        )

    scatter_peaks = (
        scatter_analysis.get("all_peaks", [])
        if isinstance(scatter_analysis, dict)
        else []
    )
    scatter_rows = [
        {
            "population": f"Scatter candidate {index}",
            "position": peak.get("mean"),
            "events": peak.get("count"),
            "r2": peak.get("r2"),
            "cv": peak.get("cv"),
            "validated": bool(peak.get("validated", False)),
            "rejection_reasons": list(peak.get("rejection_reasons") or []),
        }
        for index, peak in enumerate(scatter_peaks, start=1)
        if isinstance(peak, dict)
    ]

    return {
        "thresholds": {
            "fluorescence_r2_minimum": settings.fit_r2_threshold,
            "fluorescence_cv_maximum": settings.fit_cv_threshold,
            "scatter_r2_minimum": settings.scatter_fit_r2_threshold,
            "scatter_cv_maximum": settings.scatter_fit_cv_threshold,
            "minimum_events_per_peak": settings.minimum_events_per_peak,
            "minimum_peak_fraction": settings.minimum_peak_fraction,
            "marker_gate_sigma_multiplier": settings.marker_gate_sigma_multiplier,
            "fluorescence_saturation_intensity": fluorescence_saturation_intensity,
        },
        "fluorescence_peaks": fluorescence_rows,
        "marker_scatter_fits": list(marker_scatter_diagnostics or []),
        "scatter_peaks": scatter_rows,
        "scatter_fit_method": scatter_analysis.get("method") if isinstance(scatter_analysis, dict) else None,
    }


def build_marker_anchor_warning(*, result: PeakProcessResult) -> str:
    """Explain which marker anchor prevented size assignment.

    Parameters
    ----------
    result : PeakProcessResult
        Detection result containing marker positions and fluorescence guides.

    Returns
    -------
    str
        User-facing explanation of the unavailable or unreliable marker anchor.
    """
    peak_metadata = build_peak_metadata(peak_lines_payload=result.peak_lines_payload)
    marker_positions = extract_marker_anchor_positions(peak_metadata=peak_metadata)
    marker_is_reliable = bright_marker_scatter_anchor_is_reliable(
        peak_metadata=peak_metadata,
        peak_lines_payload=result.peak_lines_payload,
    )
    payload = result.peak_lines_payload
    raw_fluorescence_guides = (
        payload.get("fluorescence_guide_positions", [])
        if isinstance(payload, dict)
        else []
    )
    fluorescence_candidates = (
        payload.get("fluorescence_marker_candidates", [])
        if isinstance(payload, dict)
        else []
    )
    scatter_diagnostics = (
        payload.get("marker_scatter_diagnostics", [])
        if isinstance(payload, dict)
        else []
    )
    fluorescence_guides = (
        [
            float(value)
            for value in raw_fluorescence_guides
            if _as_positive_float(value) is not None
        ]
        if isinstance(raw_fluorescence_guides, list)
        else []
    )

    missing_markers = [
        ("Dim marker", DIM_MARKER_DIAMETER_NM),
        ("Bright marker", BRIGHT_MARKER_DIAMETER_NM),
    ]
    details: list[str] = []
    for marker_name, diameter_nm in missing_markers:
        if marker_name in marker_positions:
            continue
        if marker_name == "Bright marker" and len(fluorescence_guides) >= 2:
            bright_candidate = (
                max(
                    fluorescence_candidates,
                    key=lambda candidate: float(candidate.get("position", 0.0)),
                )
                if isinstance(fluorescence_candidates, list)
                and fluorescence_candidates
                else None
            )
            if bright_candidate and not bright_candidate.get("validated"):
                rejection_reasons = bright_candidate.get("rejection_reasons") or []
                reason_text = (
                    "; ".join(str(reason) for reason in rejection_reasons)
                    if rejection_reasons
                    else "it did not pass the fluorescence fit checks"
                )
                details.append(
                    f"The higher-intensity fluorescence peak at "
                    f"{float(bright_candidate['position']):g} a.u. was detected, but its "
                    f"fluorescence fit was rejected ({reason_text}). Rosetta therefore did not "
                    f"create a scatter gate for the {diameter_nm:g} nm marker."
                )
            else:
                bright_scatter_diagnostic = (
                    next(
                        (
                            diagnostic
                            for diagnostic in scatter_diagnostics
                            if diagnostic.get("marker_role") == marker_name
                        ),
                        None,
                    )
                    if isinstance(scatter_diagnostics, list)
                    else None
                )
                if bright_scatter_diagnostic:
                    rejected_peaks = bright_scatter_diagnostic.get(
                        "rejected_peaks",
                        [],
                    )
                    rejection_reasons = [
                        str(reason)
                        for peak in rejected_peaks
                        for reason in peak.get("rejection_reasons", [])
                    ]
                    rejection_detail = (
                        "; ".join(rejection_reasons)
                        if rejection_reasons
                        else "no scatter peak candidate passed validation"
                    )
                    details.append(
                        f"The higher-intensity fluorescence peak at "
                        f"{max(fluorescence_guides):g} a.u. was detected, but its gated scatter "
                        f"fit was rejected: {rejection_detail}."
                    )
                else:
                    details.append(
                        f"The higher-intensity fluorescence peak at "
                        f"{max(fluorescence_guides):g} a.u. was detected, but Rosetta found no "
                        f"validated scatter position for the {diameter_nm:g} nm marker."
                    )
        else:
            details.append(
                f"No validated scatter position was assigned to the {diameter_nm:g} nm marker. "
                "Check whether its fluorescence population was detected and whether its gated "
                "scatter events form a stable peak."
            )

    if "Bright marker" in marker_positions and not marker_is_reliable:
        details.append(
            f"The {BRIGHT_MARKER_DIAMETER_NM:g} nm marker's scatter anchor is unreliable "
            "because its fluorescence signal is at or near detector saturation."
        )

    if (
        "Dim marker" in marker_positions
        and "Bright marker" in marker_positions
        and marker_positions["Bright marker"] <= marker_positions["Dim marker"]
    ):
        details.append(
            f"Two marker candidates were fitted. The dim candidate is at "
            f"{marker_positions['Dim marker']:.4g} a.u. scatter and the bright candidate "
            f"is at {marker_positions['Bright marker']:.4g} a.u. "
            "The 380 nm candidate must be to the right of the 140 nm candidate for two-marker sizing."
        )

    if not details:
        details.append(
            "Rosetta could not use the detected marker anchors to assign sizes. Check the "
            "selected channels and data, then rerun peak detection."
        )
    return (
        "Warning: Size assignment needs both reliable 140 nm and 380 nm marker anchors. "
        + " ".join(details)
    )


def _build_warning_graph_payload(*, peak_lines_payload: Any, show_detected_peaks: bool = False) -> dict[str, Any]:
    """Keep the event cloud and baseline gate, with detection guides for previews.

    Parameters
    ----------
    peak_lines_payload : Any
        Existing graph annotations and event samples, if available.
    show_detected_peaks : bool, optional
        Keep detected peak guides and fit diagnostics for review.

    Returns
    -------
    dict[str, Any]
        Graph payload with optional detection guides and no size annotations.
    """
    if not isinstance(peak_lines_payload, dict):
        return {}

    retained_payload_keys = (
        "plot_x_values",
        "plot_y_values",
        "baseline_cutoff",
        "y_lower_gate",
        "y_upper_gate",
        "rosetta_detection_issue",
        "rosetta_event_counts",
    )
    if show_detected_peaks:
        retained_payload_keys += (
            "points", "labels", "scatter_guide_positions", "fluorescence_guide_positions",
            "saturation_guard_excluded_positions",
            "rosetta_debug_diagnostics",
        )
    payload = {key: peak_lines_payload[key] for key in retained_payload_keys if key in peak_lines_payload}
    if show_detected_peaks:
        payload["rosetta_size_assignment_warning"] = True
    return payload
