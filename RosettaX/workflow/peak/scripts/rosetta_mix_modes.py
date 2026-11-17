"""Shared execution behavior for the fixed-threshold Rosetta Mix modes."""

from __future__ import annotations

from .base import PeakProcessResult
from .rosetta_mix import FluorescenceGuidedScatterPeakProcess
from .rosetta_mix_v1 import (
    BRIGHT_MARKER_DIAMETER_NM,
    DIM_MARKER_DIAMETER_NM,
    _as_positive_float,
    bright_marker_scatter_anchor_is_reliable,
    build_peak_metadata,
    build_rosetta_mix_v1_peak_lines_payload,
    build_rosetta_mix_v1_table_prefill_rows,
    extract_marker_anchor_positions,
)
from dataclasses import replace
from typing import Any


class RosettaMixSizeAssignmentProcess(FluorescenceGuidedScatterPeakProcess):
    """Run shared Rosetta detection and assign sizes from fluorescent markers.

    The class keeps marker sizing behavior separate from the Custom V1 process
    so fixed-threshold Rosetta modes can preserve failure diagnostics.
    """

    preserve_graph_payload_on_warning = True
    supports_advanced_mode = False

    def get_detector_channel_labels(self) -> dict[str, str]:
        """Return the channel labels used by the Rosetta Mix modes."""
        return {
            "scattering": "Side scattering channel",
            "green_fluorescence": "Green fluorescence channel",
        }

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> PeakProcessResult | None:
        """Detect peaks, infer bead sizes, and preserve diagnostics on failure.

        Parameters
        ----------
        backend : Any
            Data backend used to read the current FCS sample.
        detector_channels : dict[str, Any]
            Detector columns selected for scattering and green fluorescence.
        peak_count : Any
            Maximum number of peaks considered by the detector.
        max_events_for_analysis : Any
            Maximum events passed to the detector.
        process_settings : dict[str, Any]
            Resolved Rosetta detection settings.

        Returns
        -------
        PeakProcessResult | None
            Detected peaks and size assignments, or ``None`` if detection did
            not produce a result.
        """
        resolved_process_settings = dict(process_settings or {})
        resolved_process_settings["advanced_mode"] = []
        result = FluorescenceGuidedScatterPeakProcess.run_automatic_action(
            self,
            backend=backend,
            detector_channels=detector_channels,
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_process_settings,
        )
        if result is None:
            return None

        if not result.table_prefill_rows:
            if result.status:
                warning_payload = _build_warning_graph_payload(
                    peak_lines_payload=result.peak_lines_payload,
                )
                return replace(
                    result,
                    peak_lines_payload=warning_payload,
                    warning=True,
                )
            return result

        resolved_rows, status_suffix = build_rosetta_mix_v1_table_prefill_rows(
            result=result,
        )
        if not resolved_rows and result.status:
            warning_payload = _build_warning_graph_payload(
                peak_lines_payload=result.peak_lines_payload,
            )
            return replace(
                result,
                peak_lines_payload=warning_payload,
                status=f"Warning: {result.status}",
                warning=True,
            )

        if status_suffix.startswith("Warning:") or any(
            not row.get("particle_diameter_nm") for row in resolved_rows
        ):
            warning_status = (
                status_suffix
                if "Rosetta Mix size range" in status_suffix
                else build_marker_anchor_warning(result=result)
            )
            warning_payload = _build_warning_graph_payload(
                peak_lines_payload=result.peak_lines_payload,
            )
            return replace(
                result,
                peak_positions=[],
                new_peak_positions=[],
                table_prefill_rows=[],
                peak_lines_payload=warning_payload,
                status=warning_status,
                warning=True,
            )

        updated_status = str(result.status or "").strip()
        if status_suffix:
            updated_status = f"{updated_status} {status_suffix}".strip()
        updated_status = ""

        updated_peak_lines_payload = result.peak_lines_payload
        if isinstance(result.peak_lines_payload, dict):
            updated_peak_lines_payload = build_rosetta_mix_v1_peak_lines_payload(
                result=result,
                resolved_rows=resolved_rows,
            )

        return replace(
            result,
            table_prefill_rows=resolved_rows,
            peak_lines_payload=updated_peak_lines_payload,
            status=updated_status,
        )


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
            "Both markers were detected, but their scatter positions are reversed or equal."
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


def _build_warning_graph_payload(*, peak_lines_payload: Any) -> dict[str, Any]:
    """Keep the event cloud and baseline gate while removing peak diagnostics.

    Parameters
    ----------
    peak_lines_payload : Any
        Existing graph annotations and event samples, if available.

    Returns
    -------
    dict[str, Any]
        A reduced graph payload without candidate positions or debug overlays.
    """
    if not isinstance(peak_lines_payload, dict):
        return {}

    retained_payload_keys = (
        "plot_x_values",
        "plot_y_values",
        "baseline_cutoff",
        "y_lower_gate",
        "y_upper_gate",
    )
    return {
        key: peak_lines_payload[key]
        for key in retained_payload_keys
        if key in peak_lines_payload
    }
