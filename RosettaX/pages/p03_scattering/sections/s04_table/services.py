"""Workflow table exports and local section assembly."""

import numpy as np
import plotly.graph_objects as go
from collections.abc import Callable
from RosettaX.utils.casting import as_optional_float
from RosettaX.workflow.page_session.scattering import ScatteringPageState
from RosettaX.workflow.parameters.table import MIE_MODEL_SOLID_SPHERE
from RosettaX.workflow.scattering.rosetta_assignment import (
    VALIDATION_MODEL_FIELDS,
    resolve_rosetta_model_rows,
    rosetta_validation_materials,
    update_rosetta_assignment_overlays,
)
from RosettaX.workflow.table.scattering import (
    ScatteringCalibrationStandardTable,
    add_empty_row_for_model,
    build_scattering_parameters_payload,
    build_table_state_from_runtime_config,
    compute_model_for_rows,
    core_shell_table_columns,
    get_user_data_column_ids_for_model,
    should_rebuild_table_from_runtime_config,
    sphere_table_columns,
    table_is_effectively_empty,
)
from typing import Any

__all__ = [
    "ScatteringCalibrationStandardTable",
    "add_empty_row_for_model",
    "build_scattering_parameters_payload",
    "build_table_state_from_runtime_config",
    "compute_model_for_rows",
    "core_shell_table_columns",
    "get_user_data_column_ids_for_model",
    "should_rebuild_table_from_runtime_config",
    "sphere_table_columns",
    "table_is_effectively_empty",
    "build_section",
]


def build_section(*args, **kwargs):
    """
    Build the scattering s04_table section instance.
    """
    from .main import ReferenceTable

    return ReferenceTable(*args, **kwargs)

def _build_validation_figure(*, rows: list[dict[str, Any]]) -> go.Figure | None:
    """Plot modeled coupling against measured scatter with a fitted scale."""
    points = []
    for row in rows:
        measured = as_optional_float(row.get("measured_peak_position"))
        expected = as_optional_float(row.get("expected_coupling"))
        if measured and expected and measured > 0 and expected > 0 and np.isfinite([measured, expected]).all():
            points.append((measured, expected, row["particle_diameter_nm"]))
    if not points:
        return None
    measured = np.array([point[0] for point in points])
    expected = np.array([point[1] for point in points])
    scale = (measured @ expected) / (measured @ measured)
    predicted_scatter = expected / scale
    percent_difference = 100 * (predicted_scatter / measured - 1)
    variance = np.sum((expected - expected.mean()) ** 2)
    r_squared = float(1 - np.sum((expected - scale * measured) ** 2) / variance) if variance > 0 else None
    bounds = [0, float(max(measured.max(), predicted_scatter.max()))]
    figure = go.Figure()
    figure.add_scatter(x=bounds, y=bounds, mode="lines", name="Equal response", hoverinfo="skip")
    figure.add_scatter(
        x=measured.tolist(), y=predicted_scatter.tolist(), mode="markers",
        text=[f"{point[2]} nm" for point in points], name="Table assignments",
        customdata=percent_difference.tolist(),
        hovertemplate=(
            "%{text}<br>Measured: %{x:,.2f} a.u.<br>Predicted: %{y:,.2f} a.u."
            "<br>Difference: %{customdata:+.1f}%<extra></extra>"
        ),
    )
    figure.update_layout(
        margin={"t": 36},
        legend={"orientation": "h", "y": 1, "yanchor": "bottom"},
        meta={
            "point_count": len(points),
            "r_squared": r_squared,
            "max_percent_difference": float(np.max(np.abs(percent_difference))),
        },
        xaxis_title="Measured scatter (a.u.)",
        yaxis_title="Predicted scatter after scaling (a.u.)",
    )
    return figure


def review_rosetta_assignments(
    *,
    computed_rows: list[dict[str, Any]],
    page_state: ScatteringPageState,
    mie_model: str,
    compute_coupling: Callable[..., list[dict[str, Any]]],
    model_inputs: dict[str, Any],
    apply: bool,
    reviewed_suggestions: Any,
) -> tuple[list[dict[str, Any]], ScatteringPageState, str, go.Figure | None, dict[str, Any] | None]:
    """Review model support and apply changed diameters only after user review."""
    evidence = page_state.rosetta_assignment_evidence
    if not evidence:
        return computed_rows, page_state, "Run Rosetta to propose bead assignments first.", None, None
    if mie_model != MIE_MODEL_SOLID_SPHERE:
        return computed_rows, page_state, "Select the Solid Sphere particle model to validate Rosetta assignments.", None, None

    diagnostics = []
    proposed_rows, status, result = resolve_rosetta_model_rows(
        current_rows=computed_rows, evidence=evidence, compute_model=compute_coupling, diagnostics=diagnostics,
    )
    if result is None:
        return computed_rows, page_state, "The table differs from the Rosetta results. Run Rosetta again to validate its assignments.", None, None

    model_settings = {field: model_inputs[field] for field in VALIDATION_MODEL_FIELDS}
    result["validation_model_settings"] = model_settings
    supported = result.get("supported_peak_count", 0) if result.get("confirmed") else 0
    total = len(evidence["rows"])
    findings = list(dict.fromkeys(diagnostics))
    if not findings and status and not result.get("confirmed"):
        findings.append(status)
    status = " ".join([f"{supported} of {total} bead identities supported.", *findings])

    changes = []
    for before, after in zip(computed_rows, proposed_rows, strict=True):
        old = as_optional_float(before.get("particle_diameter_nm"))
        new = as_optional_float(after.get("particle_diameter_nm"))
        if old != new:
            peak = before["measured_peak_position"]
            changes.append(f"{peak} a.u.: {old if old is not None else 'blank'} → {new if new is not None else 'unresolved'}")

    if changes:
        review = {"table": computed_rows, "proposed": compute_coupling(current_rows=proposed_rows), "source": evidence, "settings": model_settings}
        if not apply or reviewed_suggestions != review:
            pending = page_state.update(
                rosetta_assignment_evidence=dict(evidence, confirmed=False),
                calibration_payload=None,
                calibration_saved=False,
            )
            review["source"] = pending.rosetta_assignment_evidence
            pending = pending.update(scattering_peak_lines_payload=update_rosetta_assignment_overlays(
                graph_payload=pending.scattering_peak_lines_payload, evidence=review["source"],
            ))
            prefix = "The results changed. Review the updated suggestions before applying. " if apply else ""
            status += " Suggested changes: " + "; ".join(changes) + ". Unresolved diameters will be cleared if applied."
            return computed_rows, pending, prefix + status, _build_validation_figure(rows=computed_rows), review
        computed_rows = review["proposed"]
        status += " Suggested changes applied."
    elif apply:
        return computed_rows, page_state, "Run validation again to review any suggested changes.", None, None

    result["validation_materials"] = rosetta_validation_materials(rows=computed_rows)
    updated = page_state.update(
        rosetta_assignment_evidence=result,
        scattering_peak_lines_payload=update_rosetta_assignment_overlays(
            graph_payload=page_state.scattering_peak_lines_payload, evidence=result,
        ) if result.get("confirmed") else page_state.scattering_peak_lines_payload,
        calibration_payload=None,
        calibration_saved=False,
    )
    return computed_rows, updated, status, _build_validation_figure(rows=computed_rows), None
