"""Peak graph controls, interaction revisions, and post-layout annotations."""

from typing import Any

import numpy as np
import plotly.graph_objs as go

from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph

from .. import registry
from .rosetta_annotations import (
    add_rosetta_scatter_guide_annotations,
    extract_rosetta_scatter_guide_annotations,
)


def is_enabled(
    graph_toggle_value: Any,
) -> bool:
    """
    Return whether the graph should be displayed.
    """
    if isinstance(graph_toggle_value, str):
        return graph_toggle_value == "enabled"

    if isinstance(graph_toggle_value, (list, tuple, set)):
        return "enabled" in graph_toggle_value

    if isinstance(graph_toggle_value, bool):
        return graph_toggle_value

    return False


def scale_selection_is_log(
    scale_selection: Any,
) -> bool:
    """
    Return whether a legacy scale selection requests generic log scale.

    Compatibility wrapper for older peak workflow code.
    """
    if isinstance(scale_selection, str):
        return scale_selection == "log"

    if isinstance(scale_selection, (list, tuple, set)):
        return "log" in scale_selection

    return False


def axis_scale_selection_is_log(
    *,
    scale_selection: Any,
    axis: str,
) -> bool:
    """
    Return whether one axis is configured for log scaling.
    """
    expected_toggle = (
        Scatter2DGraph.x_log_value if axis == "x" else Scatter2DGraph.y_log_value
    )

    if isinstance(scale_selection, str):
        return scale_selection in {
            "log",
            expected_toggle,
        }

    if isinstance(scale_selection, (list, tuple, set)):
        return "log" in scale_selection or expected_toggle in scale_selection

    return False


def build_peak_workflow_uirevision(
    *,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_values: list[Any],
    xscale_selection: Any,
    yscale_selection: Any,
) -> str:
    """
    Build a stable Plotly UI revision token for peak workflow graphs.

    Preserve the current zoom/pan only when the user is still looking at the
    same underlying graph identity: same file, same process, same detector
    selection, and same axis scale modes.

    Changes such as overlays, helper traces, peak payload updates, or histogram
    bin counts should not invalidate the interaction state.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    normalized_detector_values = tuple(
        str(value or "").strip()
        for value in (
            detector_dropdown_values
            if isinstance(detector_dropdown_values, list)
            else []
        )
    )

    return repr(
        (
            "peak_workflow_graph",
            str(uploaded_fcs_path or ""),
            str(resolved_process_name or ""),
            normalized_detector_values,
            bool(
                axis_scale_selection_is_log(
                    scale_selection=xscale_selection,
                    axis="x",
                )
            ),
            bool(
                axis_scale_selection_is_log(
                    scale_selection=yscale_selection,
                    axis="y",
                )
            ),
        )
    )


def apply_peak_workflow_interaction_revision(
    *,
    figure: go.Figure,
    uploaded_fcs_path: Any,
    process_name: Any,
    detector_dropdown_values: list[Any],
    xscale_selection: Any,
    yscale_selection: Any,
) -> go.Figure:
    """
    Apply a stable Plotly interaction contract to a peak workflow figure.
    """
    figure.update_layout(
        uirevision=build_peak_workflow_uirevision(
            uploaded_fcs_path=uploaded_fcs_path,
            process_name=process_name,
            detector_dropdown_values=detector_dropdown_values,
            xscale_selection=xscale_selection,
            yscale_selection=yscale_selection,
        ),
    )

    return figure


def add_peak_workflow_post_layout_overlays(
    *,
    figure: go.Figure,
    process_name: Any,
    peak_lines_payload: Any,
) -> go.Figure:
    """
    Add overlays that must run after callback-level layout and trace updates.
    """
    resolved_process_name = registry.resolve_process_name(
        process_name,
    )

    if not _is_rosetta_script_process_name(
        resolved_process_name,
    ):
        return figure

    process = registry.get_process_instance(
        process_name=resolved_process_name,
    )

    if getattr(process, "graph_type", "2d_scatter") != "2d_scatter":
        return figure

    annotation_entries = extract_rosetta_scatter_guide_annotations(
        peak_lines_payload=peak_lines_payload,
    )

    if not annotation_entries:
        return figure

    return add_rosetta_scatter_guide_annotations(
        figure=figure,
        annotation_entries=annotation_entries,
    )


def unique_finite_preserving_order(
    values: list[Any],
) -> list[float]:
    """
    Return finite floats in first-seen order with near-duplicates collapsed.
    """
    resolved_values: list[float] = []

    for raw_value in values:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(value):
            continue

        if any(
            np.isclose(
                value,
                existing_value,
                rtol=0.0,
                atol=max(abs(existing_value) * 1e-6, 1e-9),
            )
            for existing_value in resolved_values
        ):
            continue

        resolved_values.append(value)

    return resolved_values


def _is_rosetta_script_process_name(
    process_name: Any,
) -> bool:
    """
    Return whether a process name refers to one of the Rosetta scripts.
    """
    normalized_name = str(process_name or "").strip().lower()

    return normalized_name in {
        "rosetta script",
        "rosetta script v1",
    }
