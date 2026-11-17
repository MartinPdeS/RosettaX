"""Shared execution behavior for the fixed-threshold Rosetta Mix modes."""

from __future__ import annotations

from .base import PeakProcessResult
from .rosetta_mix import FluorescenceGuidedScatterPeakProcess
from .rosetta_mix_diagnostics import (  # noqa: F401
    _build_warning_graph_payload,
    build_marker_anchor_warning,
)
from .rosetta_mix_sizing import (
    build_rosetta_peak_lines_payload,
    build_rosetta_table_prefill_rows,
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

        resolved_rows, status_suffix = self.assign_particle_sizes(result=result)
        if not resolved_rows or status_suffix.startswith("Warning:") or any(
            not row.get("particle_diameter_nm") for row in resolved_rows
        ):
            warning_status = status_suffix or build_marker_anchor_warning(result=result)
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

        updated_peak_lines_payload = result.peak_lines_payload
        if isinstance(result.peak_lines_payload, dict):
            updated_peak_lines_payload = build_rosetta_peak_lines_payload(
                result=result,
                resolved_rows=resolved_rows,
            )

        return replace(
            result,
            table_prefill_rows=resolved_rows,
            peak_lines_payload=updated_peak_lines_payload,
            status="",
        )

    def assign_particle_sizes(
        self, *, result: PeakProcessResult,
    ) -> tuple[list[dict[str, Any]], str]:
        """Assign sizes using the existing two-marker estimation method.

        Parameters
        ----------
        result : PeakProcessResult
            Detected peaks, marker anchors and table rows.

        Returns
        -------
        tuple[list[dict[str, Any]], str]
            Assigned rows and a status message, including any failure details.
        """
        rows, status = build_rosetta_table_prefill_rows(result=result)
        if status.startswith("Warning:") and "Rosetta Mix size range" not in status:
            status = build_marker_anchor_warning(result=result)
        return rows, status
