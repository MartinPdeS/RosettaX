"""Custom Rosetta mode with editable settings and detailed fit diagnostics."""

from ..core.process_calls import standard_peak_action
from .base import PeakProcessResult
from .rosetta_mix import FluorescenceGuidedScatterPeakProcess
from .rosetta_mix_models import RosettaAssignmentState
from .rosetta_mix_sizing import (  # noqa: F401
    BRIGHT_MARKER_DIAMETER_NM,
    DIM_MARKER_DIAMETER_NM,
    MARKER_SATURATION_FLUORESCENCE_FRACTION,
    ROSETTA_MIX_PARTICLE_DIAMETERS_NM,
    _as_positive_float,
    assign_monotonic_candidate_diameters,
    bright_marker_scatter_anchor_is_reliable,
    build_peak_metadata,
    build_scatter_guide_annotations,
    extract_marker_anchor_positions,
    format_size_annotation_label,
    infer_rosetta_mix_particle_diameters_nm,
    match_table_points_to_peak_metadata,
    resolve_marker_proxy_sizes,
    resolve_marker_row_diameter,
    resolve_rosetta_table_sizes,
)
from .rosetta_mix_sizing import (
    build_rosetta_peak_lines_payload as build_rosetta_mix_v1_peak_lines_payload,
)
from .rosetta_mix_sizing import (
    build_rosetta_table_prefill_rows as build_rosetta_mix_v1_table_prefill_rows,  # noqa: F401
)
from dataclasses import replace
from typing import Any


class FluorescenceGuidedScatterPeakProcessV1(FluorescenceGuidedScatterPeakProcess):
    """
    Rosetta peak detection with V1 Rosetta Mix diameter inference.

    This variant keeps the current fluorescence-guided detection behavior, then
    replaces the placeholder particle-diameter column with Rosetta Mix size
    assignments inferred from the dim and bright fluorescent marker peaks.
    """

    process_name = "Rosetta Script V1"
    process_label = "Rosetta — Custom & Diagnostics"
    description = (
        "Custom Rosetta Script with editable detection settings and marker-based "
        "bead sizing from the 140 nm and 380 nm fluorescent markers."
    )
    sort_order = 4
    supports_advanced_mode = False
    always_advanced_mode = True
    always_show_process_settings = True
    supports_debug_diagnostics = True

    def get_detector_channel_labels(self) -> dict[str, str]:
        """Return the labels for the required FCS channels.

        Returns
        -------
        dict[str, str]
            Channel roles mapped to their displayed labels.
        """
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
        """
        Run Rosetta detection, then infer Rosetta Mix diameter assignments.
        """
        resolved_process_settings = dict(process_settings or {})
        if self.always_advanced_mode:
            resolved_process_settings["advanced_mode"] = ["enabled"]

        result = super().run_automatic_action(
            backend=backend,
            detector_channels=detector_channels,
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_process_settings,
        )

        if result is None:
            return None

        assignment = resolve_rosetta_table_sizes(result=result)
        resolved_rows = assignment.rows
        status_suffix = assignment.status

        if not resolved_rows and result.status:
            return replace(result, status=f"Warning: {result.status}", warning=True)

        if assignment.state is RosettaAssignmentState.FAILED or any(
            not row.get("particle_diameter_nm") for row in resolved_rows
        ):
            debug_diagnostics = (
                result.peak_lines_payload.get("rosetta_debug_diagnostics")
                if isinstance(result.peak_lines_payload, dict)
                else None
            )
            warning_payload = {
                key: result.peak_lines_payload[key]
                for key in ("rosetta_event_counts", "rosetta_detection_issue")
                if key in result.peak_lines_payload
            }
            if isinstance(debug_diagnostics, dict):
                warning_payload["rosetta_debug_diagnostics"] = debug_diagnostics
            warning_payload["rosetta_sizing"] = assignment.to_diagnostics()
            return replace(
                result,
                peak_positions=[],
                new_peak_positions=[],
                table_prefill_rows=[],
                peak_lines_payload=warning_payload,
                status=(
                    status_suffix
                    if assignment.state is RosettaAssignmentState.FAILED
                    else f"Warning: {status_suffix}"
                ),
                warning=True,
            )

        updated_status = str(result.status or "").strip()

        if status_suffix:
            updated_status = f"{updated_status} {status_suffix}".strip()

        if not _advanced_mode_enabled(
            process_settings=resolved_process_settings,
        ):
            updated_status = ""

        updated_peak_lines_payload = result.peak_lines_payload

        if isinstance(result.peak_lines_payload, dict):
            updated_peak_lines_payload = build_rosetta_mix_v1_peak_lines_payload(
                result=result,
                resolved_rows=resolved_rows,
            )
        updated_peak_lines_payload = dict(updated_peak_lines_payload, rosetta_sizing=assignment.to_diagnostics())

        return replace(
            result,
            table_prefill_rows=resolved_rows if resolved_rows else result.table_prefill_rows,
            peak_lines_payload=updated_peak_lines_payload,
            status=updated_status,
        )


def _advanced_mode_enabled(
    *,
    process_settings: dict[str, Any] | None,
) -> bool:
    """
    Return whether the peak workflow advanced mode toggle is enabled.
    """
    if not isinstance(process_settings, dict):
        return False

    value = process_settings.get("advanced_mode")

    if isinstance(value, str):
        return value == "enabled"

    if isinstance(value, (list, tuple, set)):
        return "enabled" in value

    return bool(value)


PROCESS = FluorescenceGuidedScatterPeakProcessV1()
