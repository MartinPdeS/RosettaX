"""Peak graph controls, interaction revisions, and post-layout annotations."""

import numpy as np
import plotly.graph_objs as go
from .. import registry
from .rosetta_annotations import (
    ROSETTA_BASELINE_GATE_COLOR,
    add_rosetta_scatter_guide_annotations,
    extract_rosetta_scatter_guide_annotations,
    include_rosetta_peak_markers_in_view,
)
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from typing import Any


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

    figure.update_layout(
        showlegend=True,
        legend={
            "orientation": "h",
            "x": 0.01,
            "xref": "container",
            "xanchor": "left",
            "y": 0.012,
            "yref": "container",
            "yanchor": "bottom",
            "font": {"size": min(13, figure.layout.legend.font.size or 13)},
            "bgcolor": "rgba(255,255,255,0.9)",
        },
    )

    annotation_entries = extract_rosetta_scatter_guide_annotations(
        peak_lines_payload=peak_lines_payload,
    )

    if not annotation_entries and resolved_process_name == "Rosetta Script Mixture" and isinstance(peak_lines_payload, dict):
        try:
            gate = float(peak_lines_payload.get("baseline_cutoff"))
        except (TypeError, ValueError):
            gate = np.nan
        if np.isfinite(gate) and gate > 0:
            add_rosetta_baseline_shape(figure=figure, baseline_gate=gate)

    if not annotation_entries:
        return figure

    has_classified_peaks = any(entry.get("kind") in ("marker", "non_fluorescent", "excluded") for entry in annotation_entries)
    baseline_gate = None
    if has_classified_peaks and isinstance(peak_lines_payload, dict):
        include_rosetta_peak_markers_in_view(figure=figure, peak_lines_payload=peak_lines_payload)
        try:
            baseline_gate = float(peak_lines_payload.get("baseline_cutoff"))
            if not np.isfinite(baseline_gate):
                baseline_gate = None
        except (TypeError, ValueError):
            pass
        for trace in figure.data:
            trace.showlegend = trace.name in ("Fluorescent marker", "Non-fluorescent peak", "Excluded by saturation guard")
        if baseline_gate is not None and (figure.layout.yaxis.type != "log" or baseline_gate > 0):
            add_rosetta_baseline_shape(figure=figure, baseline_gate=baseline_gate)

    if isinstance(peak_lines_payload, dict) and peak_lines_payload.get("saturation_guard_threshold"):
        figure.add_vline(
            x=float(peak_lines_payload["saturation_guard_threshold"]),
            line_color="#b45309", line_dash="dashdot", line_width=2,
            name="Saturation guard cutoff", showlegend=True,
            layer="below",
        )
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

    return normalized_name == "rosetta script" or normalized_name.startswith("rosetta script ")



def add_rosetta_baseline_shape(*, figure: go.Figure, baseline_gate: float) -> None:
    """
    Draw the fluorescence gate across the visible scatter axis.

    Parameters
    ----------
    figure : go.Figure
        Scatter figure with event traces and optional peak overlays.
    baseline_gate : float
        Fluorescence gate in raw channel intensity units.
    """
    figure.layout.shapes = tuple(
        shape for shape in figure.layout.shapes
        if not (shape.type == "line" and shape.yref == "y"
                and shape.y0 == baseline_gate and shape.y1 == baseline_gate)
    )
    figure.add_shape(
        type="line", xref="x domain", x0=0, x1=1,
        yref="y", y0=baseline_gate, y1=baseline_gate,
        name="Fluorescence baseline gate", showlegend=True, layer="below",
        line={"color": ROSETTA_BASELINE_GATE_COLOR, "width": 2},
    )
