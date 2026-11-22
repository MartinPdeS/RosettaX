"""Experimental Rosetta mode with prominence and joint scatter mixture fitting."""

import numpy as np
from ..core.process_calls import standard_peak_action
from .base import PeakProcessResult
from .rosetta_mix_diagnostics import build_marker_anchor_warning
from .rosetta_mix_mixture_fitting import find_mixture_scatter_peaks, fit_marker_regions
from .rosetta_mix_models import (
    MIXTURE_MARKER_STRICTNESS,
    RosettaAssignmentState,
    RosettaDetectionIssue,
    RosettaSizeAssignment,
    resolve_rosetta_setting,
)
from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess
from .rosetta_mix_sizing import (
    BRIGHT_MARKER_DIAMETER_NM,
    DIM_MARKER_DIAMETER_NM,
    MARKER_SATURATION_FLUORESCENCE_FRACTION,
    ROSETTA_MIX_PARTICLE_DIAMETERS_NM,
    _as_positive_float,
    bright_marker_scatter_anchor_is_reliable,
    build_peak_metadata,
    extract_marker_anchor_positions,
    match_table_points_to_peak_metadata,
    resolve_marker_row_diameter,
)
from dataclasses import replace
from typing import Any


class MixtureRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Identify scatter populations with a joint model in log intensity.

    Fluorescence gates and marker-based sizing follow the existing Rosetta
    workflow. Scatter acceptance uses prominence, separation and bootstrap
    stability; histogram R² is not an acceptance criterion.
    """

    process_name = "Rosetta Script Mixture"
    process_label = "Rosetta"
    description = (
        "Uses fluorescence gates and a joint mixture fit of log scatter intensity. "
        "Assigns sizes from two usable markers and reports measured scatter positions when only one marker is usable. "
        "Experimental: compare against known standards before using calibration results."
    )
    sort_order = 1
    scatter_fit_function = staticmethod(find_mixture_scatter_peaks)
    clear_table_on_warning = True
    always_show_process_settings = True
    recover_clipped_marker = True
    allow_unassigned_sizes = True

    def fit_marker_bounded_scatter(
        self,
        *,
        values: np.ndarray,
        peak_count: int,
        marker_diagnostics: list[dict[str, Any]],
        fluorescence_saturation: float,
        **fit_options: Any,
    ) -> dict[str, Any]:
        """Fit three log-scatter regions when two measured anchors are usable."""
        anchors = {
            marker["marker_role"]: marker
            for marker in marker_diagnostics
            if marker.get("validated") and "scatter_boundary" not in marker
        }
        dim = anchors.get("Dim marker")
        bright = anchors.get("Bright marker")
        if dim is not None and bright is not None:
            lower = dim["selected_peak"]["mean"]
            upper = bright["selected_peak"]["mean"]
            if (
                0 < lower < upper
                and dim.get("gate_overlap", 0) < 0.5
                and (
                    bright.get("recovered_from_clipped_fluorescence")
                    or bright["fluorescence_position"] < MARKER_SATURATION_FLUORESCENCE_FRACTION * fluorescence_saturation
                )
            ):
                return fit_marker_regions(
                    values=values, lower=lower, upper=upper, peak_count=peak_count,
                    fit=self.scatter_fit_function, fit_options=fit_options,
                )
        return self.scatter_fit_function(values=values, peak_count=peak_count, **fit_options)

    def _assign_particle_sizes(self, *, result: PeakProcessResult) -> RosettaSizeAssignment:
        """Assign CAL003 sizes in order within regions bounded by the markers."""
        metadata = build_peak_metadata(peak_lines_payload=result.peak_lines_payload)
        anchors = extract_marker_anchor_positions(peak_metadata=metadata)
        lower = _as_positive_float(anchors.get("Dim marker"))
        upper = _as_positive_float(anchors.get("Bright marker"))
        reliable = bright_marker_scatter_anchor_is_reliable(
            peak_metadata=metadata, peak_lines_payload=result.peak_lines_payload,
        )
        if not reliable:
            reliable = any(
                diagnostic.get("recovered_from_clipped_fluorescence")
                and upper is not None
                and upper <= result.peak_lines_payload.get("saturation_guard_threshold", np.inf)
                for diagnostic in result.peak_lines_payload.get("marker_scatter_diagnostics", [])
            )
        boundaries = {
            item["marker_role"]: item["scatter_boundary"]
            for item in result.peak_lines_payload.get("marker_scatter_diagnostics", [])
            if "scatter_boundary" in item
        }
        bounded_marker = None
        if lower is not None and upper is None and "Bright marker" in boundaries:
            upper = boundaries["Bright marker"]
            bounded_marker = 380
            reliable = True
        elif lower is None and upper is not None and reliable and "Dim marker" in boundaries:
            lower = boundaries["Dim marker"]
            bounded_marker = 140
        if lower is None or upper is None or upper <= lower or not reliable:
            return RosettaSizeAssignment(
                state=RosettaAssignmentState.FAILED,
                failure_code="unreliable_markers",
                rejection_reasons=(build_marker_anchor_warning(result=result).removeprefix("Warning: "),),
            )

        scatter_positions = sorted({
            float(item["x"]) for item in metadata
            if item.get("kind") == "non_fluorescent"
        })
        regions = (
            ("between the 140 nm and 380 nm markers", [x for x in scatter_positions if lower < x < upper], (147, 203, 296)),
            ("below the 140 nm marker", sorted((x for x in scatter_positions if x < lower), reverse=True), (125, 100, 70)),
            ("above the 380 nm marker", [x for x in scatter_positions if x > upper], (400, 600, 799, 994)),
        )
        assignments = {}
        unresolved = []
        assumed_missing_ends = []
        for region_index, (label, positions, diameters) in enumerate(regions):
            middle = region_index == 0
            if len(positions) > len(diameters) or (middle and len(positions) != len(diameters)):
                expected = ", ".join(str(size) for size in diameters)
                unresolved.append(
                    f"Found {len(positions)} validated scatter {'peak' if len(positions) == 1 else 'peaks'} {label}; "
                    f"expected {'exactly' if middle else 'at most'} {len(diameters)} ({expected} nm)."
                )
                continue
            if not middle and 0 < len(positions) < len(diameters):
                assumed_missing_ends.append(label)
            assignments.update(
                (position, float(diameter)) for position, diameter in zip(positions, diameters)
            )

        if any(x == lower or x == upper for x in scatter_positions):
            unresolved.append("A scatter peak coincides with a marker anchor and was left unsized.")

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
            row["particle_diameter_nm"] = diameter if diameter is not None else ""
            rows.append(row)

        notices = []
        if assumed_missing_ends:
            notices.append(
                f"Outer assignments {' and '.join(assumed_missing_ends)} are provisional and assume missing beads occur at the ends."
            )
        if bounded_marker:
            notices.append(
                f"Used the {bounded_marker} nm marker at the scatter limit as an ordering boundary. "
                "The clipped marker was excluded from calibration."
            )
        if not any(row["particle_diameter_nm"] for row in rows):
            state = RosettaAssignmentState.UNRESOLVED
        elif unresolved:
            state = RosettaAssignmentState.PARTIAL
        else:
            state = RosettaAssignmentState.ASSIGNED
        return RosettaSizeAssignment(
            rows=rows,
            state=state,
            detail="No sizes assigned:" if unresolved and state is RosettaAssignmentState.UNRESOLVED else "",
            notices=tuple(notices),
            rejection_reasons=tuple(unresolved),
            needs_confirmation=bool(unresolved or assumed_missing_ends or any(not row["particle_diameter_nm"] for row in rows)),
            clipped_marker_nm=bounded_marker,
        )

    def _record_size_assignments(
        self, *, result: PeakProcessResult, rows: list[dict[str, Any]], method: str,
        marker_diameters_nm: tuple[float, ...],
    ) -> PeakProcessResult:
        """Record the evidence behind each assigned diameter for the peak graph."""
        return replace(
            result,
            peak_lines_payload=dict(
                result.peak_lines_payload,
                rosetta_size_assignments=[
                    {
                        "position": row["measured_peak_position"],
                        "diameter_nm": row["particle_diameter_nm"],
                        "method": method,
                        "marker_diameters_nm": list(marker_diameters_nm),
                    }
                    for row in rows if row.get("particle_diameter_nm")
                ],
            ),
        )

    def _review_marker_pair(
        self, *, result: PeakProcessResult,
    ) -> tuple[PeakProcessResult, str]:
        """Keep measured marker candidates while rejecting a weak contradictory gate."""
        payload = result.peak_lines_payload
        if not isinstance(payload, dict):
            return result, ""
        diagnostics = payload.get("marker_scatter_diagnostics", [])
        candidates = [item for item in diagnostics if item.get("validated") and "gate_overlap" in item]
        if len(candidates) != 2:
            return result, ""

        dim, bright = candidates
        dim_position = dim["selected_peak"]["mean"]
        bright_position = bright["selected_peak"]["mean"]
        if dim_position < bright_position and dim["gate_overlap"] < 0.5:
            return result, ""

        # A marker needs support in its scatter gate and separation from the
        # fluorescence baseline. Prefer one candidate only with a clear margin.
        quality = [
            min(1.0, float(item["selected_peak"].get("count") or 0) / max(1, item["gated_event_count"]))
            * item["above_baseline_fraction"]
            for item in candidates
        ]
        preferred = int(np.argmax(quality))
        keep_one = (
            quality[preferred] >= 0.70 and abs(quality[0] - quality[1]) >= 0.20
            and candidates[preferred]["gate_overlap"] < 0.5
        )
        for index, candidate in enumerate(candidates):
            candidate = dict(candidate, validated=keep_one and index == preferred, identity_uncertain=True)
            candidates[index] = candidate
        reason = "overlap in fluorescence" if dim["gate_overlap"] >= 0.5 else "are reversed or equal in scatter"
        status = (
            f"Warning: Two fluorescent candidates {reason}. "
            f"The lower-fluorescence fit is at {dim_position:.4g} a.u. scatter and "
            f"the higher-fluorescence fit is at {bright_position:.4g} a.u. "
        )
        status += (
            "Only the better-supported candidate was retained, and its diameter remains uncertain."
            if keep_one else "Both candidate positions are shown because neither establishes the marker order."
        )
        labels = [
            "Fluorescent marker candidate" if point["kind"] == "marker" else label
            for point, label in zip(payload["points"], payload["labels"], strict=True)
        ]
        status += " Compute model can compare size assignments after detector configuration."
        reviewed = dict(payload, labels=labels, marker_scatter_diagnostics=candidates)
        return replace(result, peak_lines_payload=reviewed), status

    def _resolve_particle_sizes(
        self, *, result: PeakProcessResult,
    ) -> tuple[PeakProcessResult, RosettaSizeAssignment]:
        """Return two-marker assignments or measured positions with blank diameters."""
        result, marker_conflict = self._review_marker_pair(result=result)
        if marker_conflict:
            rows = [dict(row, particle_diameter_nm="") for row in result.table_prefill_rows or []]
            return result, RosettaSizeAssignment(
                rows=rows, state=RosettaAssignmentState.UNRESOLVED,
                failure_code="conflicting_markers",
                rejection_reasons=(marker_conflict.removeprefix("Warning: "),),
                needs_confirmation=True,
            )
        assignment = self._assign_particle_sizes(result=result)
        rows = assignment.rows
        payload = result.peak_lines_payload
        if not isinstance(payload, dict):
            return result, assignment

        marker_diagnostics = payload.get("marker_scatter_diagnostics", [])
        if rows:
            method = "Two measured markers"
            if assignment.clipped_marker_nm is not None:
                method = "One measured marker and a clipped scatter boundary"
            elif any(item.get("recovered_from_clipped_fluorescence") for item in marker_diagnostics):
                method = "Two measured scatter markers, one recovered from clipped fluorescence"
                assignment = replace(
                    assignment, notices=(*assignment.notices, "Recovered the 380 nm marker from scatter events at the fluorescence ceiling."),
                )
            result = self._record_size_assignments(
                result=result, rows=rows, method=method,
                marker_diameters_nm=(DIM_MARKER_DIAMETER_NM, BRIGHT_MARKER_DIAMETER_NM),
            )
            return result, assignment

        metadata = build_peak_metadata(peak_lines_payload=payload)
        bright_is_reliable = bright_marker_scatter_anchor_is_reliable(
            peak_metadata=metadata, peak_lines_payload=payload,
        )
        scatter_ceiling = payload.get("saturation_guard_threshold", np.inf)
        anchors = [
            item for item in marker_diagnostics
            if item.get("validated")
            and item["selected_peak"]["mean"] <= scatter_ceiling
            and (item["marker_role"] != "Bright marker" or bright_is_reliable
                 or item.get("recovered_from_clipped_fluorescence"))
        ]
        if len(anchors) != 1:
            if not payload.get("scatter_bootstrap_positions"):
                return result, assignment
            rows = [dict(row, particle_diameter_nm="") for row in result.table_prefill_rows or []]
            return result, replace(
                assignment, rows=rows, state=RosettaAssignmentState.UNRESOLVED, needs_confirmation=True,
            )

        rows = [dict(row, particle_diameter_nm="") for row in result.table_prefill_rows or []]
        marker_warning = " ".join(assignment.rejection_reasons)
        marker_position = anchors[0]["selected_peak"]["mean"]
        known_sizes = sorted(ROSETTA_MIX_PARTICLE_DIAMETERS_NM)
        marker_sizes = {DIM_MARKER_DIAMETER_NM, BRIGHT_MARKER_DIAMETER_NM}
        scatter_positions = sorted({
            float(item["x"]) for item in metadata if item.get("kind") == "non_fluorescent"
        })
        ordered_positions = sorted([*scatter_positions, marker_position])
        if (
            not any("scatter_boundary" in item for item in marker_diagnostics)
            and len(scatter_positions) == len(known_sizes) - len(marker_sizes)
            and marker_position not in scatter_positions
            and all(row["measured_peak_position"] in ordered_positions for row in rows)
        ):
            marker_rank = ordered_positions.index(marker_position)
            compatible = [
                diameter for diameter in marker_sizes
                if sum(size < diameter and size not in marker_sizes for size in known_sizes) == marker_rank
            ]
            if len(compatible) == 1:
                marker_size = compatible[0]
                other_size, = marker_sizes - {marker_size}
                known_sizes.remove(other_size)
                assignments = dict(zip(ordered_positions, known_sizes, strict=True))
                for row in rows:
                    row["particle_diameter_nm"] = assignments[row["measured_peak_position"]]
                labels = [
                    ("Dim marker" if marker_size == DIM_MARKER_DIAMETER_NM else "Bright marker")
                    if point["kind"] == "marker" and point["x"] == marker_position
                    else "Unresolved fluorescent marker" if point["kind"] == "marker" else label
                    for point, label in zip(payload["points"], payload["labels"], strict=True)
                ]
                return (
                    self._record_size_assignments(
                        result=replace(result, peak_lines_payload=dict(payload, labels=labels)),
                        rows=rows, method="One marker and all ten scatter populations",
                        marker_diameters_nm=(marker_size,),
                    ),
                    RosettaSizeAssignment(
                        rows=rows, needs_confirmation=True,
                        detail=f"Assigned all ten scatter populations by rank using the {marker_size:g} nm marker.",
                    ),
                )
        anchor = anchors[0]
        assume_bright_marker = len(marker_diagnostics) == 1
        marker_role = "Bright marker" if assume_bright_marker else anchor["marker_role"]
        marker_ranges = {
            "Dim marker": (DIM_MARKER_DIAMETER_NM, "Bright marker", (125, 100, 70), (147, 203, 296)),
            "Bright marker": (BRIGHT_MARKER_DIAMETER_NM, "Dim marker", (296, 203, 147), (400, 600, 799, 994)),
        }
        marker_size, other_marker_role, sizes_below, sizes_above = marker_ranges[marker_role]
        marker_confirmed = any(
            item["marker_role"] == other_marker_role
            and (
                (item["fluorescence_position"] > anchor["fluorescence_position"])
                if marker_role == "Dim marker"
                else item["fluorescence_position"] < anchor["fluorescence_position"]
            )
            for item in marker_diagnostics
        )
        if (
            (marker_confirmed or assume_bright_marker)
            and not any("scatter_boundary" in item for item in marker_diagnostics)
            and marker_position not in scatter_positions
        ):
            positions_above = [position for position in scatter_positions if position > marker_position]
            positions_below = [position for position in reversed(scatter_positions) if position < marker_position]
            above_assignments = dict(zip(positions_above, sizes_above, strict=False))
            below_assignments = dict(zip(positions_below, sizes_below, strict=False))
            assignments = above_assignments | below_assignments
            table_positions = {row["measured_peak_position"] for row in rows}
            if table_positions.intersection(assignments):
                for row in rows:
                    position = row["measured_peak_position"]
                    row["particle_diameter_nm"] = (
                        marker_size if position == marker_position else assignments.get(position, "")
                    )
                assignments_by_direction = []
                for direction, direction_assignments in (("above", above_assignments), ("below", below_assignments)):
                    sizes = ", ".join(
                        str(diameter) for position, diameter in direction_assignments.items()
                        if position in table_positions
                    )
                    if sizes:
                        assignments_by_direction.append(f"{sizes} nm {direction}")
                resolved_rows = sum(bool(row["particle_diameter_nm"]) for row in rows)
                status = (
                    f"Assigned {' and '.join(assignments_by_direction)} the {marker_size:g} nm marker at {marker_position:.4g} a.u. "
                    "This assumes no intermediate populations were missed."
                )
                if resolved_rows < len(rows):
                    status += f" {len(rows) - resolved_rows} measured peaks remain unsized."
                method = "Estimated by rank from one marker"
                if assume_bright_marker:
                    status = "Assumed the only fluorescent marker is the 380 nm bright marker. " + status
                    method = "Estimated by rank assuming the 380 nm marker"
                    labels = [
                        "Bright marker (assumed)" if point["kind"] == "marker" and point["x"] == marker_position else label
                        for point, label in zip(payload["points"], payload["labels"], strict=True)
                    ]
                    result = replace(result, peak_lines_payload=dict(payload, labels=labels))
                result = self._record_size_assignments(
                    result=result, rows=rows, method=method,
                    marker_diameters_nm=(marker_size,),
                )
                return result, RosettaSizeAssignment(rows=rows, detail=status, needs_confirmation=True)

        status = (
            f"Found one usable marker at {marker_position:.4g} a.u. and retained {len(rows)} measured scatter peaks. "
            "Diameters are blank because the missing marker's position or scatter limit could not establish a unique bead order. "
            "Detected peaks remain available in the graph and table. "
            "Compute model can compare size assignments after detector configuration."
        )
        failed_marker = next((item for item in marker_diagnostics if not item.get("validated")), None)
        if failed_marker and "scatter_boundary" in failed_marker:
            status += f" {marker_warning}"
        elif failed_marker:
            status += (
                f" The other fluorescence gate, centered at {failed_marker['fluorescence_position']:.4g} a.u., "
                f"contained {failed_marker['gated_event_count']:,} usable scatter events but yielded no accepted marker peak."
            )
        labels = [
            "Fluorescent marker" if point["kind"] == "marker" else label
            for point, label in zip(payload["points"], payload["labels"], strict=True)
        ]
        return (
            replace(result, peak_lines_payload=dict(payload, labels=labels)),
            RosettaSizeAssignment(
                rows=rows, state=RosettaAssignmentState.UNRESOLVED,
                failure_code="unreliable_markers", rejection_reasons=(status,), needs_confirmation=True,
            ),
        )

    def get_settings(self) -> list[dict[str, Any]]:
        """Return Rosetta controls with one setting for fluorescence fit quality."""
        return [dict(MIXTURE_MARKER_STRICTNESS, marks=dict(MIXTURE_MARKER_STRICTNESS["marks"]))]


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
            for setting in [*super().get_settings(), *self.get_settings()]
            if setting["name"] != "scatter_fit_r2_threshold"
        }
        explicit_settings = process_settings or {}
        resolved_settings.update(explicit_settings)
        strictness = resolve_rosetta_setting(
            definition=MIXTURE_MARKER_STRICTNESS, value=resolved_settings["marker_fit_strictness"],
        )
        # The middle setting reproduces the historical 0.70 R² / 0.60 CV
        # defaults. Interpolate each half independently for useful endpoints.
        thresholds = {
            "fit_r2_threshold": round(float(np.interp(strictness, [0.0, 0.5, 1.0], [0.35, 0.70, 0.95])), 3),
            "fit_cv_threshold": round(float(np.interp(strictness, [0.0, 0.5, 1.0], [1.50, 0.60, 0.30])), 3),
        }
        for name, threshold in thresholds.items():
            if "marker_fit_strictness" in explicit_settings or name not in explicit_settings:
                resolved_settings[name] = threshold

        result = super().run_automatic_action(
            backend=backend, detector_channels=detector_channels,
            peak_count=peak_count, max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_settings,
        )
        if result and result.warning and strictness > 0 and result.peak_lines_payload.get(
            "rosetta_detection_issue",
        ) in {RosettaDetectionIssue.FLUORESCENCE_MISSING, RosettaDetectionIssue.MARKER_MISSING}:
            result = replace(
                result,
                status=(
                    f"{result.status} If the histogram shows a distinct marker peak that was rejected, "
                    f"lower Marker fit strictness from {strictness:g} and rerun. "
                    "Check the accepted peaks before calibrating."
                ),
            )
        return result

    def _finalize_size_assignment(
        self, *, result: PeakProcessResult, assignment: RosettaSizeAssignment,
    ) -> tuple[PeakProcessResult, RosettaSizeAssignment]:
        """Apply the lowest-peak exclusion and retain evidence for detector checks."""
        payload = result.peak_lines_payload
        lowest_peak = min(
            (point["x"] for point in payload.get("points", []) if point.get("kind") == "non_fluorescent"),
            default=None,
        )
        rows = [row for row in assignment.rows if row["measured_peak_position"] != lowest_peak]
        if len(rows) != len(assignment.rows):
            excluded_row = next(row for row in assignment.rows if row["measured_peak_position"] == lowest_peak)
            # Keep the peak on the graph and preserve the rank of the other rows.
            payload = dict(
                payload,
                rosetta_lowest_peak_exclusion={
                    "position": lowest_peak,
                    "diameter_nm": excluded_row.get("particle_diameter_nm"),
                    "rows_before": len(assignment.rows),
                },
                rosetta_size_assignments=[
                    entry for entry in payload.get("rosetta_size_assignments", [])
                    if entry["position"] != lowest_peak
                ],
                scatter_guide_annotations=[
                    entry for entry in payload.get("scatter_guide_annotations", [])
                    if entry["x"] != lowest_peak or entry.get("kind") == "marker"
                ],
            )
            result = replace(
                result, table_prefill_rows=rows,
                peak_positions=[point for point in result.peak_positions if point["x"] != lowest_peak],
                new_peak_positions=[position for position in (result.new_peak_positions or []) if position != lowest_peak],
            )
            if not any(row.get("particle_diameter_nm") for row in rows) and assignment.state in {
                RosettaAssignmentState.ASSIGNED, RosettaAssignmentState.PARTIAL,
            }:
                assignment = replace(
                    assignment, state=RosettaAssignmentState.UNRESOLVED, failure_code="lowest_peak_exclusion",
                    detail=" ".join(filter(None, (
                        "No assigned diameters remain after excluding the lowest non-fluorescent peak.", assignment.detail,
                    ))),
                )
            assignment = replace(assignment, rows=rows)

        if rows and assignment.needs_confirmation and payload.get("scatter_bootstrap_positions"):
            payload = dict(
                payload,
                rosetta_assignment_evidence={
                    "rows": [row for row in rows if row.get("particle_diameter_nm")],
                    "scatter": payload["scatter_bootstrap_positions"],
                    "markers": payload.get("marker_scatter_diagnostics", []),
                },
            )
        return replace(result, peak_lines_payload=payload), assignment
