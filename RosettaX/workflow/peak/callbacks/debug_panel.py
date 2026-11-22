"""Render Rosetta fit diagnostics for the peak workflow."""

import dash_bootstrap_components as dbc
import math
from dash import html
from typing import Any


def build_rosetta_result_panel(*, status: str, peak_lines_payload: Any) -> html.Section | None:
    """Show the current Rosetta outcome and the status of the calibration table.

    Parameters
    ----------
    status : str
        Message returned by peak detection.
    peak_lines_payload : dict or None
        Detection results containing sizing, event counts, and fit diagnostics.

    Returns
    -------
    dash.html.Section or None
        Inline feedback for a Rosetta result, or None for other payloads.
    """
    if not isinstance(peak_lines_payload, dict):
        return None

    preview = bool(peak_lines_payload.get("rosetta_settings_preview"))
    detection_issue = peak_lines_payload.get("rosetta_detection_issue")
    sizing = peak_lines_payload.get("rosetta_sizing")
    event_counts = peak_lines_payload.get("rosetta_event_counts", {})
    if not preview and not detection_issue and not isinstance(sizing, dict):
        return None

    assigned_count = sizing.get("assigned_row_count", 0) if isinstance(sizing, dict) else 0
    measured_count = sizing.get("measured_row_count", 0) if isinstance(sizing, dict) else 0
    unassigned_count = max(0, measured_count - assigned_count)
    needs_confirmation = isinstance(sizing, dict) and sizing.get("needs_confirmation")

    if preview:
        title, tone = "Rosetta preview", "preview"
        summary = "Select Detect peaks to update the calibration table."
    elif detection_issue:
        title, tone = "Rosetta detection stopped", "error"
        summary = status
    elif assigned_count == 0:
        title, tone = "No diameters assigned", "review"
        summary = "Review the peaks and fit details before running detection again."
    elif needs_confirmation or unassigned_count:
        title, tone = "Review Rosetta assignments", "review"
        summary = (
            "Use Compute model to check provisional sizes against the detector model."
            if peak_lines_payload.get("rosetta_assignment_evidence")
            else "Check the assigned sizes against the detected peaks."
        )
    else:
        title, tone = "Rosetta detection complete", "complete"
        summary = ""

    metrics = []
    if isinstance(sizing, dict):
        metrics.append(("Sized peaks" if preview else "Calibration rows", assigned_count))
        if unassigned_count:
            metrics.append(("Peaks without a diameter", unassigned_count))
    excluded_count = len(peak_lines_payload.get("saturation_guard_excluded_positions") or [])
    if peak_lines_payload.get("rosetta_lowest_peak_exclusion"):
        excluded_count += 1
    if excluded_count:
        metrics.append(("Excluded peaks", excluded_count))
    analyzed_count = event_counts.get("retained") if isinstance(event_counts, dict) else None
    if isinstance(analyzed_count, int):
        metrics.append(("Events analyzed", analyzed_count))

    details = build_rosetta_debug_panel(
        peak_lines_payload=peak_lines_payload,
        status=status if status != summary else "",
    )
    return html.Section(
        [
            html.Div(
                [
                    html.H6(title, className="peak-result-title"),
                    html.P(summary, className="peak-result-summary") if summary else None,
                ],
                role="alert" if tone == "error" else "status",
            ),
            html.Dl(
                [
                    html.Div([html.Dt(label), html.Dd(f"{count:,}")])
                    for label, count in metrics
                ],
                className="peak-result-metrics",
            ) if metrics else None,
            details,
        ],
        className=f"app-diagnostics-inline peak-result peak-result--{tone}",
        **{"aria-label": "Rosetta result"},
    )


def build_rosetta_debug_panel(*, peak_lines_payload: Any, status: str = "") -> Any:
    """Build a collapsed Custom Rosetta diagnostic section.

    Parameters
    ----------
    peak_lines_payload : Any
        Peak result payload containing ``rosetta_debug_diagnostics``.

    Returns
    -------
    Any
        A collapsed details panel, or ``None`` when there are no diagnostics.
    """
    if not isinstance(peak_lines_payload, dict):
        return None
    diagnostics = peak_lines_payload.get("rosetta_debug_diagnostics")
    if not isinstance(diagnostics, dict) and not status:
        return None

    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    sections: list[Any] = [html.P(status, className="peak-result-detail-message")] if status else []
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
        sections.append(
            _build_rosetta_debug_table(
                title="Non-fluorescent scatter fits",
                rows=scatter_rows,
            )
        )

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
    body_rows = []
    for row in rows:
        reasons = row.get("rejection_reasons") or []
        body_rows.append(
            html.Tr(
                [
                    html.Td(row.get("population", "—")),
                    html.Td(_format_debug_value(row.get("position", row.get("mean")))),
                    html.Td(_format_debug_value(row.get("events", row.get("count")))),
                    html.Td(_format_debug_value(row.get("r2"))),
                    html.Td(_format_debug_value(row.get("cv"))),
                    html.Td("Accepted" if row.get("validated") else "Rejected"),
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


