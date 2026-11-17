"""Experimental Rosetta mode with prominence and joint scatter mixture fitting."""

from .base import PeakProcessResult
from .rosetta_mix_diagnostics import build_marker_anchor_warning
from .rosetta_mix_mixture_fitting import find_mixture_scatter_peaks
from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess
from .rosetta_mix_sizing import (
    _as_positive_float,
    bright_marker_scatter_anchor_is_reliable,
    build_peak_metadata,
    extract_marker_anchor_positions,
    match_table_points_to_peak_metadata,
    resolve_marker_row_diameter,
)
from typing import Any


class MixtureRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Identify scatter populations with a joint model in log intensity.

    Fluorescence gates and marker-based sizing follow the existing Rosetta
    workflow. Scatter acceptance uses prominence, separation and bootstrap
    stability; histogram R² is not an acceptance criterion.
    """

    process_name = "Rosetta Script Mixture"
    process_label = "Rosetta — Mixture (Experimental)"
    description = (
        "Uses fluorescence gates and a joint mixture fit of log scatter intensity. "
        "Requires three populations between the 140 and 380 nm markers; outer populations are optional. "
        "Experimental: compare against known standards before using calibration results."
    )
    sort_order = 3
    scatter_fit_function = staticmethod(find_mixture_scatter_peaks)
    clear_table_on_warning = True

    def assign_particle_sizes(
        self, *, result: PeakProcessResult,
    ) -> tuple[list[dict[str, Any]], str]:
        """Assign the CAL003 populations in order within marker-bounded regions.

        Parameters
        ----------
        result : PeakProcessResult
            Validated scatter peaks and fluorescent marker anchors in arbitrary
            intensity units. Marker positions must be positive and ordered.

        Returns
        -------
        tuple[list[dict[str, Any]], str]
            Complete rows assigned by rank, or no rows and an explicit warning.
            Exactly three populations are required between the anchors. Outer
            populations are optional and assigned outward from each anchor;
            this assumes missing outer sizes occur at the extremes.
        """
        metadata = build_peak_metadata(peak_lines_payload=result.peak_lines_payload)
        anchors = extract_marker_anchor_positions(peak_metadata=metadata)
        lower = _as_positive_float(anchors.get("Dim marker"))
        upper = _as_positive_float(anchors.get("Bright marker"))
        reliable = bright_marker_scatter_anchor_is_reliable(
            peak_metadata=metadata, peak_lines_payload=result.peak_lines_payload,
        )
        if lower is None or upper is None or upper <= lower or not reliable:
            return [], build_marker_anchor_warning(result=result)

        scatter_positions = sorted({
            float(item["x"]) for item in metadata
            if item.get("kind") == "non_fluorescent"
        })
        regions = (
            ("between the 140 nm and 380 nm markers", [x for x in scatter_positions if lower < x < upper], (147, 203, 296)),
            ("below the 140 nm marker", sorted((x for x in scatter_positions if x < lower), reverse=True), (125, 100, 70)),
            ("above the 380 nm marker", [x for x in scatter_positions if x > upper], (400, 600, 799, 994)),
        )
        for region_index, (label, positions, diameters) in enumerate(regions):
            if region_index == 0 and len(positions) != len(diameters):
                expected = ", ".join(str(size) for size in diameters)
                return [], (
                    f"Warning: Mixture size assignment failed: found {len(positions)} validated "
                    f"non-fluorescent populations {label}; expected exactly {len(diameters)} "
                    f"({expected} nm). No sizes were assigned."
                )
            if region_index > 0 and len(positions) > len(diameters):
                return [], (
                    f"Warning: Mixture size assignment failed: found {len(positions)} populations "
                    f"{label}, exceeding the {len(diameters)} known outer sizes. No sizes were assigned."
                )
        if any(x == lower or x == upper for x in scatter_positions):
            return [], "Warning: Mixture size assignment failed: a non-fluorescent peak coincides with a marker anchor. No sizes were assigned."

        assignments = {
            position: float(diameter)
            for _label, positions, diameters in regions
            for position, diameter in zip(positions, diameters, strict=False)
        }
        row_metadata = match_table_points_to_peak_metadata(
            table_points=result.peak_positions, peak_metadata=metadata,
        )
        rows = []
        for index, source_row in enumerate(result.table_prefill_rows or []):
            row = dict(source_row)
            item = row_metadata[index] if index < len(row_metadata) else {}
            diameter = resolve_marker_row_diameter(metadata=item)
            if diameter is None:
                diameter = assignments.get(_as_positive_float(row.get("measured_peak_position")))
            if diameter is None:
                return [], "Warning: Mixture size assignment failed: a table row could not be matched to a validated population. No sizes were assigned."
            row["particle_diameter_nm"] = diameter
            rows.append(row)
        return rows, ""

    def get_settings(self) -> list[dict[str, Any]]:
        """Return workflow settings excluding the unused scatter R² threshold.

        Returns
        -------
        list[dict[str, Any]]
            Controls supported by the fluorescence and mixture workflow.
        """
        settings = [
            dict(setting) for setting in super().get_settings()
            if setting.get("name") != "scatter_fit_r2_threshold"
        ]
        for setting in settings:
            if setting.get("name") == "fit_r2_threshold":
                setting["default_value"] = 0.70
        return settings

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> Any:
        """Run mixture detection using this mode's declared default settings.

        Parameters
        ----------
        backend : Any
            Current FCS data backend.
        detector_channels : dict[str, Any]
            Selected scattering and fluorescence channel names.
        peak_count : Any
            Maximum scatter population count.
        max_events_for_analysis : Any
            Maximum number of events to analyze.
        process_settings : dict[str, Any]
            Explicit settings, which override this mode's defaults.

        Returns
        -------
        Any
            Existing Rosetta result with peaks or an explanatory warning.
        """
        resolved_settings = {
            setting["name"]: setting["default_value"]
            for setting in self.get_settings()
        }
        resolved_settings.update(process_settings or {})
        return super().run_automatic_action(
            backend=backend, detector_channels=detector_channels,
            peak_count=peak_count, max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_settings,
        )
