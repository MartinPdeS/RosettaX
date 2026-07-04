# -*- coding: utf-8 -*-

from dataclasses import replace
import logging
from typing import Any, Optional

import numpy as np

from RosettaX.workflow.scattering.model import (
    ROSETTA_MIX_PRESET_NAME,
    get_scattering_calibration_scatterer_preset,
)

from .base import PeakProcessResult
from .rosetta_mix import FluorescenceGuidedScatterPeakProcess


logger = logging.getLogger(__name__)

DIM_MARKER_DIAMETER_NM = 140.0
BRIGHT_MARKER_DIAMETER_NM = 380.0

# Single-anchor fallback: diameter scales with SSC-A as d proportional to
# scatter ** exponent. An exponent of 0.25 corresponds to SSC-A growing with
# diameter ** 4, a reasonable effective slope across the Rosetta Mix size range
# under 488 nm illumination. It is only used when the two-marker slope cannot be
# fitted (bright marker saturated or absent).
SINGLE_ANCHOR_DIAMETER_SCATTER_EXPONENT = 0.25

# A fluorescent marker whose peak intensity reaches this fraction of the
# fluorescence saturation intensity is treated as detector-saturated, so its
# scatter gate is contaminated and its scatter anchor is considered unreliable.
MARKER_SATURATION_FLUORESCENCE_FRACTION = 0.95


class FluorescenceGuidedScatterPeakProcessV1(FluorescenceGuidedScatterPeakProcess):
    """
    Rosetta peak detection with V1 Rosetta Mix diameter inference.

    This variant keeps the current fluorescence-guided detection behavior, then
    replaces the placeholder particle-diameter column with Rosetta Mix size
    assignments inferred from the dim and bright fluorescent marker peaks.
    """

    process_name = "Rosetta Script V1"
    process_label = "Rosetta Script V1"
    description = (
        "Fluorescence-guided scatter peak identification with Rosetta Mix "
        "diameter inference anchored by the 140 nm and 380 nm marker beads."
    )
    sort_order = 21

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
        Run Rosetta detection, then infer Rosetta Mix diameter assignments.
        """
        result = super().run_automatic_action(
            backend=backend,
            detector_channels=detector_channels,
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=process_settings,
        )

        if result is None:
            return None

        resolved_rows, status_suffix = build_rosetta_mix_v1_table_prefill_rows(
            result=result,
        )

        updated_status = str(result.status or "").strip()

        if status_suffix:
            updated_status = f"{updated_status} {status_suffix}".strip()

        updated_peak_lines_payload = result.peak_lines_payload

        if isinstance(result.peak_lines_payload, dict):
            updated_peak_lines_payload = build_rosetta_mix_v1_peak_lines_payload(
                result=result,
                resolved_rows=resolved_rows,
            )

        return replace(
            result,
            table_prefill_rows=resolved_rows if resolved_rows else result.table_prefill_rows,
            peak_lines_payload=updated_peak_lines_payload,
            status=updated_status,
        )


def build_rosetta_mix_v1_table_prefill_rows(
    *,
    result: PeakProcessResult,
) -> tuple[list[dict[str, Any]], str]:
    """
    Replace placeholder Rosetta table diameters with inferred Rosetta Mix sizes.
    """
    source_rows = result.table_prefill_rows or []

    if not source_rows:
        return [], ""

    rows = [
        dict(row)
        for row in source_rows
        if isinstance(row, dict)
    ]

    if not rows:
        return [], ""

    peak_metadata = build_peak_metadata(
        peak_lines_payload=result.peak_lines_payload,
    )
    marker_positions = extract_marker_anchor_positions(
        peak_metadata=peak_metadata,
    )
    bright_marker_is_reliable = bright_marker_scatter_anchor_is_reliable(
        peak_metadata=peak_metadata,
        peak_lines_payload=result.peak_lines_payload,
    )
    table_point_metadata = match_table_points_to_peak_metadata(
        table_points=result.peak_positions,
        peak_metadata=peak_metadata,
    )

    non_fluorescent_row_indices: list[int] = []
    non_fluorescent_peak_positions: list[float] = []

    for row_index, row in enumerate(rows):
        metadata = (
            table_point_metadata[row_index]
            if row_index < len(table_point_metadata)
            else {}
        )

        marker_diameter = resolve_marker_row_diameter(
            metadata=metadata,
        )

        if marker_diameter is not None:
            row["particle_diameter_nm"] = float(marker_diameter)
            continue

        measured_peak_position = _as_positive_float(
            row.get("measured_peak_position"),
        )

        if measured_peak_position is None:
            continue

        non_fluorescent_row_indices.append(
            row_index,
        )
        non_fluorescent_peak_positions.append(
            float(measured_peak_position),
        )

    inferred_diameters_nm, used_marker_count = infer_rosetta_mix_particle_diameters_nm(
        measured_peak_positions=non_fluorescent_peak_positions,
        marker_positions=marker_positions,
        bright_marker_is_reliable=bright_marker_is_reliable,
    )

    if inferred_diameters_nm:
        for assignment_index, row_index in enumerate(non_fluorescent_row_indices):
            if assignment_index < len(inferred_diameters_nm):
                rows[row_index]["particle_diameter_nm"] = float(
                    inferred_diameters_nm[assignment_index],
                )
            else:
                rows[row_index]["particle_diameter_nm"] = ""

        unassigned_peak_count = len(non_fluorescent_row_indices) - len(
            inferred_diameters_nm,
        )
        unassigned_suffix = (
            f" {unassigned_peak_count} scatter peak(s) exceeded the Rosetta Mix size"
            " range and were left blank for manual review."
            if unassigned_peak_count > 0
            else ""
        )

        if used_marker_count >= 2:
            return (
                rows,
                "Rosetta Script V1 assigned Rosetta Mix diameters from the 140 nm and 380 nm marker anchors."
                + unassigned_suffix,
            )

        if used_marker_count == 1:
            bright_marker_present = (
                marker_positions.get("Bright marker") is not None
            )

            if bright_marker_present and not bright_marker_is_reliable:
                return (
                    rows,
                    "Rosetta Script V1 anchored Rosetta Mix diameters on the 140 nm marker "
                    "because the 380 nm marker was fluorescence-saturated."
                    + unassigned_suffix,
                )

            return (
                rows,
                "Rosetta Script V1 assigned approximate Rosetta Mix diameters from a single marker anchor."
                + unassigned_suffix,
            )

    return (
        rows,
        "Rosetta Script V1 kept placeholder Rosetta Mix diameters because the marker anchors were insufficient for size assignment.",
    )


def build_rosetta_mix_v1_peak_lines_payload(
    *,
    result: PeakProcessResult,
    resolved_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Attach per-peak size annotations to the Rosetta peak payload.
    """
    source_payload = result.peak_lines_payload

    if not isinstance(source_payload, dict):
        return {}

    payload = dict(source_payload)
    annotation_entries = build_scatter_guide_annotations(
        result=result,
        resolved_rows=resolved_rows,
    )

    payload["scatter_guide_annotations"] = annotation_entries

    return payload


def build_scatter_guide_annotations(
    *,
    result: PeakProcessResult,
    resolved_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build size labels for Rosetta scatter guide positions.
    """
    peak_metadata = build_peak_metadata(
        peak_lines_payload=result.peak_lines_payload,
    )

    if not peak_metadata:
        return []

    resolved_annotations: list[dict[str, Any]] = []
    used_positions: list[float] = []

    def append_annotation(*, x_value: Any, label: str) -> None:
        resolved_x_value = _as_positive_float(
            x_value,
        )

        if resolved_x_value is None:
            return

        resolved_label = str(label).strip()

        if not resolved_label:
            return

        for existing_x_value in used_positions:
            if np.isclose(
                float(existing_x_value),
                float(resolved_x_value),
                rtol=0.0,
                atol=max(abs(float(resolved_x_value)) * 1e-6, 1e-9),
            ):
                return

        resolved_annotations.append(
            {
                "x": float(resolved_x_value),
                "label": resolved_label,
            }
        )
        used_positions.append(
            float(resolved_x_value),
        )

    table_point_metadata = match_table_points_to_peak_metadata(
        table_points=result.peak_positions,
        peak_metadata=peak_metadata,
    )

    for row, metadata in zip(
        resolved_rows,
        table_point_metadata,
    ):
        if not isinstance(row, dict):
            continue

        label = format_size_annotation_label(
            row.get("particle_diameter_nm"),
        )

        if not label:
            continue

        x_value = metadata.get("x")

        if x_value is None:
            x_value = row.get("measured_peak_position")

        append_annotation(
            x_value=x_value,
            label=label,
        )

    for metadata in peak_metadata:
        marker_diameter_nm = resolve_marker_row_diameter(
            metadata=metadata,
        )

        if marker_diameter_nm is None:
            continue

        append_annotation(
            x_value=metadata.get("x"),
            label=format_size_annotation_label(
                marker_diameter_nm,
            ),
        )

    return sorted(
        resolved_annotations,
        key=lambda item: float(item["x"]),
    )


def infer_rosetta_mix_particle_diameters_nm(
    *,
    measured_peak_positions: list[float],
    marker_positions: dict[str, float],
    bright_marker_is_reliable: bool = True,
) -> tuple[list[float], int]:
    """
    Infer Rosetta Mix non-fluorescent diameters from measured scatter peaks.

    When both markers are reliable, the scatter-to-size exponent is fitted from
    the 140 nm and 380 nm anchors. When the bright (380 nm) marker is saturated
    or absent, the dim (140 nm) marker becomes the sole anchor and a fixed
    scatter-vs-size exponent is used instead of the fitted slope.
    """
    valid_peak_positions = [
        float(value)
        for value in measured_peak_positions
        if _as_positive_float(value) is not None
    ]

    if not valid_peak_positions:
        return [], 0

    dim_marker_position = _as_positive_float(
        marker_positions.get("Dim marker"),
    )
    bright_marker_position = _as_positive_float(
        marker_positions.get("Bright marker"),
    )

    estimated_sizes_nm: list[float] = []
    used_marker_count = 0

    if (
        dim_marker_position is not None
        and bright_marker_position is not None
        and bright_marker_is_reliable
        and bright_marker_position > dim_marker_position
    ):
        used_marker_count = 2
        marker_exponent = float(
            np.log(BRIGHT_MARKER_DIAMETER_NM / DIM_MARKER_DIAMETER_NM)
            / np.log(bright_marker_position / dim_marker_position)
        )

        estimated_sizes_nm = [
            float(
                DIM_MARKER_DIAMETER_NM
                * (float(peak_position) / dim_marker_position) ** marker_exponent
            )
            for peak_position in valid_peak_positions
        ]

    else:
        if dim_marker_position is not None:
            anchor_position = dim_marker_position
            anchor_diameter_nm = DIM_MARKER_DIAMETER_NM
        elif bright_marker_position is not None:
            anchor_position = bright_marker_position
            anchor_diameter_nm = BRIGHT_MARKER_DIAMETER_NM
        else:
            return [], 0

        used_marker_count = 1
        estimated_sizes_nm = [
            float(
                anchor_diameter_nm
                * (float(peak_position) / anchor_position)
                ** SINGLE_ANCHOR_DIAMETER_SCATTER_EXPONENT
            )
            for peak_position in valid_peak_positions
        ]

    if not estimated_sizes_nm:
        return [], used_marker_count

    candidate_diameters_nm = build_rosetta_mix_non_fluorescent_candidates()

    if not candidate_diameters_nm:
        return [], used_marker_count

    resolved_diameters_nm = assign_monotonic_candidate_diameters(
        estimated_sizes_nm=estimated_sizes_nm,
        candidate_diameters_nm=candidate_diameters_nm,
    )

    return resolved_diameters_nm, used_marker_count


def build_rosetta_mix_non_fluorescent_candidates() -> list[float]:
    """
    Build Rosetta Mix candidate diameters excluding the fluorescent markers.
    """
    preset = get_scattering_calibration_scatterer_preset(
        ROSETTA_MIX_PRESET_NAME,
    )

    candidate_diameters_nm = sorted(
        {
            float(value)
            for value in preset.particle_diameters_nm
            if float(value) > 0.0
        }
    )

    marker_proxy_sizes = resolve_marker_proxy_sizes(
        candidate_diameters_nm=candidate_diameters_nm,
    )

    return [
        float(value)
        for value in candidate_diameters_nm
        if float(value) not in marker_proxy_sizes
    ]


def resolve_marker_proxy_sizes(
    *,
    candidate_diameters_nm: list[float],
) -> set[float]:
    """
    Resolve which preset diameters act as the Rosetta marker proxies.
    """
    if not candidate_diameters_nm:
        return set()

    dim_proxy = min(
        candidate_diameters_nm,
        key=lambda value: abs(float(value) - DIM_MARKER_DIAMETER_NM),
    )
    bright_proxy = min(
        candidate_diameters_nm,
        key=lambda value: abs(float(value) - BRIGHT_MARKER_DIAMETER_NM),
    )

    return {
        float(dim_proxy),
        float(bright_proxy),
    }


def assign_monotonic_candidate_diameters(
    *,
    estimated_sizes_nm: list[float],
    candidate_diameters_nm: list[float],
) -> list[float]:
    """
    Assign unique Rosetta Mix diameters while preserving size order.
    """
    resolved_diameters_nm: list[float] = []
    minimum_candidate_index = 0

    for estimated_size_nm in estimated_sizes_nm:
        if estimated_size_nm <= 0.0:
            continue

        best_index: Optional[int] = None
        best_error: Optional[float] = None

        for candidate_index in range(
            minimum_candidate_index,
            len(candidate_diameters_nm),
        ):
            candidate_size_nm = float(
                candidate_diameters_nm[candidate_index],
            )
            log_error = abs(
                float(np.log10(candidate_size_nm) - np.log10(estimated_size_nm))
            )

            if best_error is None or log_error < best_error:
                best_error = log_error
                best_index = candidate_index

        if best_index is None:
            break

        resolved_diameters_nm.append(
            float(candidate_diameters_nm[best_index]),
        )
        minimum_candidate_index = best_index + 1

    return resolved_diameters_nm


def build_peak_metadata(
    *,
    peak_lines_payload: Any,
) -> list[dict[str, Any]]:
    """
    Build normalized point metadata from the Rosetta peak payload.
    """
    if not isinstance(peak_lines_payload, dict):
        return []

    raw_points = peak_lines_payload.get("points")
    raw_labels = peak_lines_payload.get("labels")

    if not isinstance(raw_points, list):
        return []

    labels = raw_labels if isinstance(raw_labels, list) else []
    metadata: list[dict[str, Any]] = []

    for point_index, raw_point in enumerate(raw_points):
        if not isinstance(raw_point, dict):
            continue

        x_value = _as_positive_float(
            raw_point.get("x"),
        )
        y_value = _as_positive_float(
            raw_point.get("y"),
        )

        if x_value is None:
            continue

        metadata.append(
            {
                "x": float(x_value),
                "y": None if y_value is None else float(y_value),
                "kind": str(raw_point.get("kind") or "").strip(),
                "label": str(labels[point_index] if point_index < len(labels) else "").strip(),
            }
        )

    return metadata


def extract_marker_anchor_positions(
    *,
    peak_metadata: list[dict[str, Any]],
) -> dict[str, float]:
    """
    Extract marker anchor x positions from Rosetta peak metadata.
    """
    marker_positions: dict[str, float] = {}

    for item in peak_metadata:
        label = str(item.get("label") or "").strip().lower()
        x_value = _as_positive_float(
            item.get("x"),
        )

        if x_value is None:
            continue

        if "dim marker" in label:
            marker_positions["Dim marker"] = float(x_value)
        elif "bright marker" in label:
            marker_positions["Bright marker"] = float(x_value)

    return marker_positions


def bright_marker_scatter_anchor_is_reliable(
    *,
    peak_metadata: list[dict[str, Any]],
    peak_lines_payload: Any,
) -> bool:
    """
    Return whether the bright marker scatter anchor can be trusted.

    A bright marker whose fluorescence peak reaches the detector saturation
    intensity has a contaminated scatter gate, so its scatter position is not a
    dependable size anchor and the dim marker should anchor size inference.
    """
    if not isinstance(peak_lines_payload, dict):
        return True

    saturation_intensity = _as_positive_float(
        peak_lines_payload.get("fluorescence_saturation_intensity"),
    )

    if saturation_intensity is None:
        return True

    for metadata in peak_metadata:
        label = str(metadata.get("label") or "").strip().lower()

        if "bright marker" not in label:
            continue

        bright_marker_fluorescence = _as_positive_float(
            metadata.get("y"),
        )

        if bright_marker_fluorescence is None:
            return True

        return bright_marker_fluorescence < (
            MARKER_SATURATION_FLUORESCENCE_FRACTION * saturation_intensity
        )

    return True


def match_table_points_to_peak_metadata(
    *,
    table_points: Any,
    peak_metadata: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Match table points back to Rosetta peak metadata.
    """
    if not isinstance(table_points, list):
        return []

    remaining_metadata = [
        dict(item)
        for item in peak_metadata
    ]
    resolved_metadata: list[dict[str, Any]] = []

    for table_point in table_points:
        point_x = None
        point_y = None

        if isinstance(table_point, dict):
            point_x = _as_positive_float(
                table_point.get("x"),
            )
            point_y = _as_positive_float(
                table_point.get("y"),
            )

        if point_x is None:
            resolved_metadata.append({})
            continue

        matched_index: Optional[int] = None

        for metadata_index, metadata in enumerate(remaining_metadata):
            metadata_x = _as_positive_float(
                metadata.get("x"),
            )
            metadata_y = _as_positive_float(
                metadata.get("y"),
            )

            if metadata_x is None:
                continue

            x_matches = np.isclose(
                float(metadata_x),
                float(point_x),
                rtol=0.0,
                atol=max(abs(float(point_x)) * 1e-6, 1e-9),
            )

            y_matches = (
                point_y is None
                or metadata_y is None
                or np.isclose(
                    float(metadata_y),
                    float(point_y),
                    rtol=0.0,
                    atol=max(abs(float(point_y)) * 1e-6, 1e-9),
                )
            )

            if x_matches and y_matches:
                matched_index = metadata_index
                break

        if matched_index is None:
            resolved_metadata.append({})
            continue

        resolved_metadata.append(
            remaining_metadata.pop(matched_index),
        )

    return resolved_metadata


def resolve_marker_row_diameter(
    *,
    metadata: dict[str, Any],
) -> Optional[float]:
    """
    Resolve the marker diameter for one table row if it is a marker row.
    """
    label = str(metadata.get("label") or "").strip().lower()

    if "dim marker" in label:
        return DIM_MARKER_DIAMETER_NM

    if "bright marker" in label:
        return BRIGHT_MARKER_DIAMETER_NM

    return None


def format_size_annotation_label(value: Any) -> str:
    """
    Format one Rosetta size annotation label.
    """
    resolved_value = _as_positive_float(
        value,
    )

    if resolved_value is None:
        return ""

    rounded_value = round(
        float(resolved_value),
        3,
    )

    if np.isclose(
        rounded_value,
        round(rounded_value),
        rtol=0.0,
        atol=1e-9,
    ):
        return f"{int(round(rounded_value))} nm"

    return f"{rounded_value:g} nm"


def _as_positive_float(
    value: Any,
) -> Optional[float]:
    """
    Convert one value to a positive finite float.
    """
    try:
        resolved_value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(resolved_value):
        return None

    if resolved_value <= 0.0:
        return None

    return float(resolved_value)


PROCESS = FluorescenceGuidedScatterPeakProcessV1()
