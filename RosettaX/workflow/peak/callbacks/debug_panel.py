"""Render Rosetta fit diagnostics for the peak workflow."""

import dash_bootstrap_components as dbc
import math
from dash import html
from typing import Any


def build_rosetta_debug_panel(*, peak_lines_payload: Any) -> Any:
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
    if not isinstance(diagnostics, dict):
        return None

    thresholds = diagnostics.get("thresholds", {})
    threshold_summary = (
        "Thresholds: fluorescence "
        f"R² ≥ {_format_debug_value(thresholds.get('fluorescence_r2_minimum'))}, "
        f"CV ≤ {_format_debug_value(thresholds.get('fluorescence_cv_maximum'))}; "
        "scatter "
        f"R² ≥ {_format_debug_value(thresholds.get('scatter_r2_minimum'))}, "
        f"CV ≤ {_format_debug_value(thresholds.get('scatter_cv_maximum'))}; "
        f"minimum {thresholds.get('minimum_events_per_peak', '—')} events per peak; "
        "marker gate ±"
        f"{_format_debug_value(thresholds.get('marker_gate_sigma_multiplier'))}σ; "
        "fluorescence saturation estimate "
        f"{_format_debug_value(thresholds.get('fluorescence_saturation_intensity'))} a.u."
    )
    sections: list[Any] = [html.Div(threshold_summary, style={"margin": "6px 0"})]

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
        [html.Summary("Debug diagnostics"), html.Div(sections)],
        style={"marginTop": "8px", "fontSize": "0.9rem"},
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


