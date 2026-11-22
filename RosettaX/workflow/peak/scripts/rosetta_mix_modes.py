"""Shared execution behavior for the fixed-threshold Rosetta Mix modes."""

from __future__ import annotations

from ..core.process_calls import standard_peak_action
from .base import PeakProcessResult
from .rosetta_mix import FluorescenceGuidedScatterPeakProcess
from .rosetta_mix_diagnostics import (  # noqa: F401
    _build_warning_graph_payload,
    build_marker_anchor_warning,
)
from .rosetta_mix_models import RosettaAssignmentState, RosettaSizeAssignment
from .rosetta_mix_sizing import (
    build_rosetta_peak_lines_payload,
    resolve_rosetta_table_sizes,
)
from dataclasses import replace
from typing import Any


class RosettaMixSizeAssignmentProcess(FluorescenceGuidedScatterPeakProcess):
    """Run shared Rosetta detection and assign sizes from fluorescent markers.

    Strict, Sensitive, and Mixture share result handling. Each mode supplies
    fixed thresholds or overrides the size-assignment method.
    """

    preserve_graph_payload_on_warning = True
    supports_advanced_mode = False
    allow_unassigned_sizes = False
    fit_thresholds: dict[str, float] = {}

    def get_settings(self) -> list[dict[str, Any]]:
        """Return editable settings, omitting this mode's fixed thresholds.

        Returns
        -------
        list[dict[str, Any]]
            Control definitions whose values the user may change.
        """
        return [
            dict(setting) for setting in super().get_settings()
            if setting.get("name") not in self.fit_thresholds
        ]

    def get_detector_channel_labels(self) -> dict[str, str]:
        """Return the channel labels used by the Rosetta Mix modes."""
        return {
            "scattering": "Side scattering channel",
            "green_fluorescence": "Green fluorescence channel",
        }

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
        resolved_process_settings.update(self.fit_thresholds)
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

        show_detected_peaks = self.allow_unassigned_sizes or bool(resolved_process_settings.get("preview_only"))
        if not result.table_prefill_rows:
            if result.status:
                warning_payload = _build_warning_graph_payload(
                    peak_lines_payload=result.peak_lines_payload,
                    show_detected_peaks=show_detected_peaks,
                )
                return replace(
                    result,
                    peak_lines_payload=warning_payload,
                    warning=True,
                )
            return result

        result, assignment = self._resolve_particle_sizes(result=result)
        if (
            not assignment.rows or assignment.state is RosettaAssignmentState.FAILED
            or (not self.allow_unassigned_sizes and any(
                not row.get("particle_diameter_nm") for row in assignment.rows
            ))
        ):
            detail = assignment.status or build_marker_anchor_warning(result=result)
            warning_payload = _build_warning_graph_payload(
                peak_lines_payload=result.peak_lines_payload,
                show_detected_peaks=show_detected_peaks,
            )
            warning_payload["rosetta_sizing"] = replace(
                assignment, state=RosettaAssignmentState.FAILED, rows=[],
            ).to_diagnostics()
            return replace(
                result, peak_positions=[], new_peak_positions=[], table_prefill_rows=[],
                peak_lines_payload=warning_payload, status=detail, warning=True,
            )

        payload = build_rosetta_peak_lines_payload(result=result, resolved_rows=assignment.rows)
        result = replace(result, table_prefill_rows=assignment.rows, peak_lines_payload=payload)
        result, assignment = self._finalize_size_assignment(result=result, assignment=assignment)
        payload = dict(result.peak_lines_payload, rosetta_sizing=assignment.to_diagnostics())
        suffix = payload.get("saturation_guard_message", "")
        status = assignment.status
        if assignment.state is RosettaAssignmentState.UNRESOLVED:
            status = "Warning: " + (status or "No diameters could be assigned to the detected non-fluorescent peaks.")
        status = " ".join(filter(None, (status, suffix)))

        return replace(
            result, peak_lines_payload=payload, status=status,
            warning=assignment.state in {
                RosettaAssignmentState.PARTIAL, RosettaAssignmentState.UNRESOLVED, RosettaAssignmentState.FAILED,
            },
        )

    def resolve_particle_sizes(
        self, *, result: PeakProcessResult,
    ) -> tuple[PeakProcessResult, list[dict[str, Any]], str]:
        """Return the source detection, sized rows, and user-facing status."""
        result, assignment = self._resolve_particle_sizes(result=result)
        return result, assignment.rows, assignment.status

    def _resolve_particle_sizes(
        self, *, result: PeakProcessResult,
    ) -> tuple[PeakProcessResult, RosettaSizeAssignment]:
        """Resolve an assignment and suppress success messages for fixed modes."""
        assignment = self._assign_particle_sizes(result=result)
        if assignment.state is RosettaAssignmentState.ASSIGNED:
            assignment = replace(assignment, detail="")
        return result, assignment

    def assign_particle_sizes(self, *, result: PeakProcessResult) -> tuple[list[dict[str, Any]], str]:
        """Return assigned rows and the rendered outcome for this mode."""
        assignment = self._assign_particle_sizes(result=result)
        return assignment.rows, assignment.status

    def _assign_particle_sizes(self, *, result: PeakProcessResult) -> RosettaSizeAssignment:
        """Assign sizes using the shared two-marker estimation method."""
        assignment = resolve_rosetta_table_sizes(result=result)
        if assignment.failure_code == "unreliable_markers":
            return replace(
                assignment,
                rejection_reasons=(build_marker_anchor_warning(result=result).removeprefix("Warning: "),),
            )
        return assignment

    def _finalize_size_assignment(
        self, *, result: PeakProcessResult, assignment: RosettaSizeAssignment,
    ) -> tuple[PeakProcessResult, RosettaSizeAssignment]:
        """Let a mode apply its final calibration table policy."""
        return result, assignment
