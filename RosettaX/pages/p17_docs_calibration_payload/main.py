# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
    build_documentation_link_chip,
)


class CalibrationPayloadDocumentationPage:
    """
    Detailed documentation for calibration wrapper and payload content.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-calibration-payload"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Calibration File Wrapper and Payload",
                    description=(
                        "This page explains the shared outer calibration record and the inner payload blocks for "
                        "fluorescence and scattering calibrations."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use these pages to connect payload structure to modeling and apply behavior.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Regression models",
                                    href="/documentation/regression-models",
                                ),
                                build_documentation_link_chip(
                                    label="Apply checks",
                                    href="/documentation/apply-checks",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "10px",
                            },
                        ),
                    ],
                    min_height="unset",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._wrapper_card(), lg=6),
                        dbc.Col(self._payload_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._field_semantics_card(), lg=6),
                        dbc.Col(self._compatibility_card(), lg=6),
                    ],
                    className="g-3",
                ),
            ]
        )

    def _wrapper_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Calibration file wrapper",
            subtitle="Every saved calibration is wrapped in the same outer record.",
            body=[
                html.Pre(
                    '{\n  "schema": "rosettax_calibration_v1",\n  "kind": "fluorescence" | "scattering",\n  "created_at": "...",\n  "name": "...",\n  "payload": { ... }\n}',
                    style={
                        "marginBottom": "10px",
                        "padding": "12px 14px",
                        "borderRadius": "10px",
                        "border": "1px solid rgba(13, 110, 253, 0.16)",
                        "background": "rgba(13, 110, 253, 0.04)",
                        "fontSize": "0.9rem",
                        "lineHeight": "1.45",
                        "whiteSpace": "pre-wrap",
                    },
                ),
                html.Div(
                    "The outer wrapper is created by the shared save workflow. The inner payload differs by calibration type and is what the apply workflow actually interprets later.",
                ),
            ],
        )

    def _payload_card(self) -> dbc.Card:
        return build_documentation_card(
            title="What the inner payload contains",
            subtitle="Fluorescence and scattering payloads preserve different kinds of evidence.",
            body=[
                html.Div(
                    "Fluorescence payloads store fit_model, fit_metrics, parameters, reference_points, source_channel, optional gating metadata, and a legacy-compatible payload block used during apply.",
                ),
                html.Div(
                    "Scattering payloads store instrument_response, calibration_standard_mie_relation, reference_table, source_channel, output_quantity, version, and metadata describing the optical assumptions and standard table context.",
                ),
                html.Div(
                    "In both cases, the goal is the same: another user should be able to inspect the JSON and understand what was fitted without reopening the original session.",
                ),
            ],
        )

    def _field_semantics_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Field semantics that matter",
            subtitle="Some payload fields are descriptive metadata; others are required for apply-time computation.",
            body=[
                html.Div("Required computational fields include source channel, fit parameters, and reference data used by the chosen calibration type."),
                html.Div("Context fields such as model labels, version tags, and metadata support review and reproducibility even when not directly used in one apply step."),
                html.Div("When extending payload structure, preserve existing keys or provide explicit migration handling to avoid breaking older saved calibrations."),
            ],
            min_height="unset",
        )

    def _compatibility_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Compatibility expectations",
            subtitle="Payload stability is part of the calibration contract across versions and users.",
            body=[
                html.Div("Wrapper schema identifies the record type so apply workflows can dispatch correctly."),
                html.Div("Legacy-compatible blocks are retained where needed so older calibrations continue to load."),
                html.Div("If a payload is incomplete, apply-time checks should fail clearly rather than silently falling back to ambiguous defaults."),
            ],
            min_height="unset",
        )


_page = CalibrationPayloadDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/calibration-payload",
    name="Calibration Payload Documentation",
    layout=layout,
)
