"""Render Rosetta fit diagnostics for the peak workflow."""

import dash_bootstrap_components as dbc
import math
from dash import html
from decimal import Decimal
from typing import Any


def build_rosetta_result_panel(*, status: str = "", peak_lines_payload: Any = None) -> html.Section:
    """Show the current Rosetta outcome and the status of the calibration table.

    Parameters
    ----------
    status : str
        Message returned by peak detection.
    peak_lines_payload : dict or None
        Detection results containing sizing, event counts, and fit diagnostics.

    Returns
    -------
    dash.html.Section
        The ready state or the current detection outcome.
    """
    peak_lines_payload = peak_lines_payload if isinstance(peak_lines_payload, dict) else {}
    preview = bool(peak_lines_payload.get("rosetta_settings_preview"))
    detection_issue = peak_lines_payload.get("rosetta_detection_issue")
    sizing = peak_lines_payload.get("rosetta_sizing")
    event_counts = peak_lines_payload.get("rosetta_event_counts", {})
    ready = not status and not preview and not detection_issue and not isinstance(sizing, dict)

    assigned_count = sizing.get("assigned_row_count", 0) if isinstance(sizing, dict) else 0
    measured_count = sizing.get("measured_row_count", 0) if isinstance(sizing, dict) else 0
    unassigned_count = max(0, measured_count - assigned_count)
    needs_confirmation = isinstance(sizing, dict) and sizing.get("needs_confirmation")

    failed = isinstance(sizing, dict) and sizing.get("state") == "failed"
    if ready:
        title, tone = "Rosetta ready", "preview"
        summary = "Select Detect peaks to begin."
    elif preview:
        title, tone = "Rosetta preview", "preview"
        summary = "Select Detect peaks to update the calibration table."
    elif failed or (assigned_count == 0 and (detection_issue or not measured_count)):
        title, tone = "Rosetta detection stopped", "error"
        summary = "Table unchanged."
    elif assigned_count == 0:
        title, tone = "Rosetta detected peaks · No sizes assigned", "review"
        summary = "Measured positions are available in the calibration table."
    else:
        sizes = "size" if assigned_count == 1 else "sizes"
        title = f"Rosetta detection complete · {assigned_count} {sizes} assigned"
        tone = "complete"
        summary = "Calibration table updated."
        if needs_confirmation:
            summary += " The assigned diameters are provisional."

    excluded_count = len(peak_lines_payload.get("saturation_guard_excluded_positions") or [])
    if peak_lines_payload.get("rosetta_lowest_peak_exclusion"):
        excluded_count += 1
    analyzed_count = event_counts.get("retained") if isinstance(event_counts, dict) else None
    valley = "—"
    gate_interval = peak_lines_payload.get("rosetta_gate_interval")
    if (
        isinstance(gate_interval, list) and len(gate_interval) == 2
        and all(isinstance(bound, (int, float)) for bound in gate_interval)
    ):
        lower, upper = gate_interval
        valley = f"{lower:.3g}–{upper:.3g} a.u."

    metrics = (
        ("Sized peaks", assigned_count if isinstance(sizing, dict) else "—"),
        ("Excluded peaks", "—" if ready else excluded_count),
        ("Events analyzed", analyzed_count if isinstance(analyzed_count, int) else "—"),
        ("Fluorescence valley", valley),
    )
    metric_list = html.Dl(
        [
            html.Div([html.Dt(label, title=label), html.Dd(f"{value:,}" if isinstance(value, int) else value, title=str(value))])
            for label, value in metrics
        ],
        className="peak-result-metrics",
    )
    unassigned_detail = f"Peaks without a diameter: {unassigned_count}." if unassigned_count else ""
    detail_message = " ".join(filter(None, (summary, status, unassigned_detail)))
    details = build_rosetta_debug_panel(
        peak_lines_payload=peak_lines_payload,
        status=detail_message,
    )
    return html.Section(
        [
            html.Div(
                [
                    html.H6(title, className="peak-result-title", title=title),
                ],
                role="alert" if tone == "error" else "status",
            ),
            metric_list,
            details,
        ],
        className=f"app-diagnostics-inline peak-result peak-result--{tone}",
        **{"aria-label": "Rosetta result"},
    )


def build_rosetta_debug_panel(*, peak_lines_payload: dict[str, Any], status: str = "") -> html.Details:
    """Build a collapsed Custom Rosetta diagnostic section.

    Parameters
    ----------
    peak_lines_payload : Any
        Peak result payload containing ``rosetta_debug_diagnostics``.
    status : str, optional
        Detailed explanation of the result.

    Returns
    -------
    html.Details
        A collapsed details panel.
    """
    diagnostics = peak_lines_payload.get("rosetta_debug_diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    sections: list[Any] = [html.P(status, className="peak-result-detail-message")] if status else []
    plotted_guides = [
        guide for guide in peak_lines_payload.get("scatter_guide_annotations", [])
        if guide.get("kind") in {"marker", "non_fluorescent"}
    ]
    if plotted_guides:
        sections.append(html.Div([
            html.Strong("Size labels shown on the graph"),
            dbc.Table([
                html.Thead(html.Tr([html.Th("Label"), html.Th("Scatter position [a.u.]")])),
                html.Tbody([
                    html.Tr([html.Td(guide["label"]), html.Td(_format_position(value=guide["x"]))])
                    for guide in plotted_guides
                ]),
            ], size="sm", responsive=True),
        ]))
    thresholds = diagnostics.get("thresholds", {})
    if thresholds:
        scatter_limits = f"CV ≤ {_format_debug_value(thresholds.get('scatter_cv_maximum'))}"
        scatter_fit_method = diagnostics.get("scatter_fit_method")
        if scatter_fit_method in {"log_gaussian_mixture", "marker_bounded_log_gaussian_mixture"}:
            scatter_limits += ", mixture fit"
        else:
            scatter_limits += f", R² ≥ {_format_debug_value(thresholds.get('scatter_r2_minimum'))}"
        sections.append(html.Ul([
            html.Li(
                f"Fluorescence R² ≥ {_format_debug_value(thresholds.get('fluorescence_r2_minimum'))} "
                f"and CV ≤ {_format_debug_value(thresholds.get('fluorescence_cv_maximum'))}."
            ),
            html.Li(f"Scatter {scatter_limits}."),
            html.Li(
                f"Minimum {thresholds.get('minimum_events_per_peak', '—')} events per peak. "
                f"Marker gate ±{_format_debug_value(thresholds.get('marker_gate_sigma_multiplier'))}σ."
            ),
            html.Li(
                "Fluorescence saturation estimate "
                f"{_format_debug_value(thresholds.get('fluorescence_saturation_intensity'))} a.u."
            ),
        ], className="peak-result-fit-thresholds"))

    fluorescence_rows = diagnostics.get("fluorescence_peaks", [])
    if fluorescence_rows:
        sections.append(
            _build_rosetta_debug_table(
                title="Fluorescence fits",
                rows=fluorescence_rows,
            )
        )

    marker_rows: list[dict[str, Any]] = []
    for marker_fit in diagnostics.get("marker_scatter_fits", []):
        marker_name = str(marker_fit.get("marker_role", "Marker"))
        selected_peak = marker_fit.get("selected_peak")
        if isinstance(selected_peak, dict):
            marker_rows.append(
                {
                    "population": f"{marker_name} (gate {marker_fit.get('gated_event_count', '—')} events)",
                    **selected_peak,
                    "validated": True,
                    "rejection_reasons": [],
                }
            )
            continue
        rejected_peaks = marker_fit.get("rejected_peaks", [])
        if rejected_peaks:
            for rejected_peak in rejected_peaks:
                marker_rows.append(
                    {
                        "population": f"{marker_name} candidate",
                        **rejected_peak,
                        "validated": False,
                    }
                )
        else:
            marker_rows.append(
                {
                    "population": f"{marker_name} gate ({marker_fit.get('gated_event_count', '—')} events)",
                    "validated": False,
                    "rejection_reasons": ["No scatter peak candidate was fitted"],
                }
            )
    if marker_rows:
        sections.append(
            _build_rosetta_debug_table(
                title="Marker-gated scatter fits",
                rows=marker_rows,
            )
        )

    scatter_rows = diagnostics.get("scatter_peaks", [])
    if scatter_rows:
        labels_by_position = {
            guide["x"]: guide["label"]
            for guide in plotted_guides
            if guide["kind"] == "non_fluorescent"
        }
        exclusion_reasons = {
            position: "Excluded because it falls beyond the scatter saturation guard."
            for position in peak_lines_payload.get("saturation_guard_excluded_positions", [])
        }
        lowest_peak = peak_lines_payload.get("rosetta_lowest_peak_exclusion")
        if isinstance(lowest_peak, dict) and lowest_peak.get("position") is not None:
            diameter = lowest_peak.get("diameter_nm")
            assigned_size = f" ({diameter:g} nm)" if isinstance(diameter, (int, float)) and diameter > 0 else ""
            exclusion_reasons[lowest_peak["position"]] = (
                f"Excluded as the lowest detected non-fluorescent peak{assigned_size}."
            )
        sizing = peak_lines_payload.get("rosetta_sizing") or {}
        unsized_reasons = {item["position"]: item["reason"] for item in sizing.get("unsized_peaks", [])}
        failure_reason = {
            "unreliable_markers": "The available marker anchors could not establish a unique bead order.",
            "conflicting_markers": "The fluorescent markers give conflicting scatter order.",
            "size_range_exceeded": "The detected peaks exceed the available bead sizes.",
        }.get(sizing.get("failure_code"))
        displayed_rows = []
        for row in scatter_rows:
            position = row.get("position")
            label = labels_by_position.get(position)
            reasons = list(row.get("rejection_reasons") or [])
            if not label:
                reason = exclusion_reasons.get(position) or unsized_reasons.get(position)
                if not reason and row.get("validated"):
                    reason = failure_reason or (
                        "Size assignment has not run for this preview."
                        if peak_lines_payload.get("rosetta_settings_preview") and not sizing
                        else "No diameter was recorded for this peak."
                    )
                if reason:
                    reasons.append(reason)
            displayed_rows.append(dict(row, assigned_size=label or "Unassigned", rejection_reasons=reasons))
        sections.append(
            _build_rosetta_debug_table(
                title="Non-fluorescent scatter candidates",
                rows=displayed_rows,
            )
        )

    if not sections:
        sections.append(html.P("No additional fit details were recorded."))

    return html.Details(
        [html.Summary("Fit details"), html.Div(sections, className="peak-result-details-content")],
        className="peak-result-details",
    )


def _build_rosetta_debug_table(*, title: str, rows: list[dict[str, Any]]) -> Any:
    """Build a compact table of peak fit values and validation decisions.

    Parameters
    ----------
    title : str
        Visible heading for this group of fits.
    rows : list[dict[str, Any]]
        Fit summaries to display.

    Returns
    -------
    Any
        A heading and responsive Bootstrap table.
    """
    headers = ["Peak", "Position [a.u.]", "Events", "R²", "CV", "Result", "Reason"]
    scatter_candidates = any("assigned_size" in row for row in rows)
    if scatter_candidates:
        headers[-2:] = ["Peak fit", "Assigned size", "Reason"]
    body_rows = []
    for row in rows:
        reasons = row.get("rejection_reasons") or []
        position = row.get("position", row.get("mean"))
        position_cell = _format_position(value=position)
        if scatter_candidates and isinstance(position, (int, float)) and math.isfinite(position):
            position_cell = html.Button(
                position_cell, type="button", className="peak-position-button",
                **{"data-scatter-position": position, "aria-pressed": "false",
                   "aria-label": f"Highlight {row.get('population', 'peak')} at {position_cell} a.u."},
            )
        fit_result = ("Detected" if scatter_candidates else "Accepted") if row.get("validated") else "Rejected"
        body_rows.append(
            html.Tr(
                [
                    html.Td(row.get("population", "—")),
                    html.Td(position_cell),
                    html.Td(_format_debug_value(row.get("events", row.get("count")))),
                    html.Td(_format_debug_value(row.get("r2"))),
                    html.Td(_format_debug_value(row.get("cv"))),
                    html.Td(fit_result),
                    *([html.Td(row["assigned_size"])] if scatter_candidates else []),
                    html.Td("; ".join(str(reason) for reason in reasons) or "—"),
                ]
            )
        )
    return html.Div(
        [
            html.Div(title, style={"fontWeight": "600", "marginTop": "8px"}),
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th(header) for header in headers])),
                    html.Tbody(body_rows),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                size="sm",
                striped=True,
                style={"marginBottom": "4px", "fontSize": "0.82rem"},
            ),
        ]
    )


def _format_debug_value(value: Any) -> str:
    """Format one numeric debug value compactly."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(numeric_value):
        return "∞" if numeric_value > 0 else "—"
    return f"{numeric_value:.4g}"




def _format_position(*, value: Any) -> str:
    """Format a position in detector units with decimal SI suffixes."""
    formatted = _format_debug_value(value)
    try:
        position = Decimal(formatted)
    except ArithmeticError:
        return formatted
    if not position.is_finite():
        return formatted
    for scale, suffix in ((1_000_000, "M"), (1_000, "k")):
        if abs(position) >= scale:
            return f"{(position / scale).normalize():f}{suffix}"
    return f"{position:f}"
