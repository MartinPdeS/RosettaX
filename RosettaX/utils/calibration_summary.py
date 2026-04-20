# -*- coding: utf-8 -*-

from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.6g}"

    return str(value)


def _parameter_rows(parameters: dict[str, Any]) -> list[html.Tr]:
    rows: list[html.Tr] = []

    for key, value in parameters.items():
        rows.append(
            html.Tr(
                [
                    html.Td(str(key), style={"fontWeight": "600", "width": "40%"}),
                    html.Td(_format_value(value)),
                ]
            )
        )

    if not rows:
        rows.append(html.Tr([html.Td("Parameters"), html.Td("N/A")]))

    return rows


def build_calibration_summary_card(summary: dict[str, Any]) -> dbc.Card:
    parameter_rows = _parameter_rows(summary.get("parameters", {}) or {})

    return dbc.Card(
        [
            dbc.CardHeader("Calibration summary"),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H4(_format_value(summary.get("name")), style={"marginBottom": "4px"}),
                            html.Div(
                                f"Type: {_format_value(summary.get('calibration_type'))}",
                                style={"opacity": 0.8, "marginBottom": "12px"},
                            ),
                        ]
                    ),
                    dbc.Table(
                        [
                            html.Tbody(
                                [
                                    html.Tr([html.Td("Created at", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("created_at")))]),
                                    html.Tr([html.Td("Source file", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("source_file")))]),
                                    html.Tr([html.Td("Source channel", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("source_channel")))]),
                                    html.Tr([html.Td("Gating channel", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("gating_channel")))]),
                                    html.Tr([html.Td("Gating threshold", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("gating_threshold")))]),
                                    html.Tr([html.Td("Fit model", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("fit_model")))]),
                                    html.Tr([html.Td("R²", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("r_squared")))]),
                                    html.Tr([html.Td("Point count", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("point_count")))]),
                                    *parameter_rows,
                                    html.Tr([html.Td("Notes", style={"fontWeight": "600"}), html.Td(_format_value(summary.get("notes")))]),
                                ]
                            )
                        ],
                        bordered=False,
                        hover=False,
                        size="sm",
                        style={"marginBottom": "0px"},
                    ),
                ]
            ),
        ]
    )