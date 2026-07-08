# -*- coding: utf-8 -*-

import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
    build_documentation_link_chip,
)


class RefractiveIndexDocumentationPage:
    """
    Detailed documentation for material refractive index resolution.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-refractive-index"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    @staticmethod
    def _load_sellmeier_material_catalog() -> list[dict[str, str]]:
        sellmeier_bank_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "sellmeier_equations.json"
        )

        with sellmeier_bank_path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)

        materials = payload.get("materials", {})

        if not isinstance(materials, dict):
            return []

        rows: list[dict[str, str]] = []

        for material_id, material_payload in sorted(materials.items()):
            if not isinstance(material_payload, dict):
                continue

            coefficient_payload = material_payload.get("coefficients", {})

            if not isinstance(coefficient_payload, dict):
                continue

            b_coefficients = coefficient_payload.get("b", [])
            c_coefficients = coefficient_payload.get("c", [])

            b_text = ", ".join(f"{float(value):.10g}" for value in (b_coefficients or []))
            c_text = ", ".join(f"{float(value):.10g}" for value in (c_coefficients or []))

            rows.append(
                {
                    "id": str(material_id),
                    "label": str(material_payload.get("label") or material_id),
                    "a": f"{float(coefficient_payload.get('a', 1.0)):.10g}",
                    "b": b_text,
                    "c": c_text,
                    "notes": str(material_payload.get("notes") or ""),
                    "source": str(material_payload.get("source") or ""),
                }
            )

        return rows

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Material Refractive Index Resolution",
                    description=(
                        "This page explains how RosettaX resolves material presets into numeric refractive indices "
                        "at the selected wavelength and how that propagates into scattering calibration modeling."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use these pages to connect refractive-index handling to full calibration behavior.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="System model and optics",
                                    href="/documentation/system-model",
                                ),
                                build_documentation_link_chip(
                                    label="Regression models",
                                    href="/documentation/regression-models",
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
                        dbc.Col(self._resolution_card(), lg=7),
                        dbc.Col(self._resolution_order_card(), lg=5),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._quality_checks_card(),
                html.Div(style={"height": "18px"}),
                self._sellmeier_catalog_card(),
            ]
        )

    def _math_block(self, expression: str) -> dcc.Markdown:
        return dcc.Markdown(
            expression,
            mathjax=True,
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
        )

    def _resolution_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How RosettaX resolves refractive indices",
            subtitle="Material presets are converted to numeric refractive indices at the selected wavelength.",
            body=[
                html.Div(
                    "When you choose a material such as water, PBS, polystyrene, silica, PMMA, lipid, or phospholipid, RosettaX resolves the refractive index from the packaged Sellmeier bank in RosettaX/assets/sellmeier_equations.json.",
                ),
                self._math_block(
                    "$$n^2 = a + \\sum_i \\frac{B_i \\lambda^2}{\\lambda^2 - C_i}$$\nwith $\\lambda$ converted from nm to $\\mu$m before evaluation.",
                ),
                html.Div(
                    "If the preset is a plain number, RosettaX uses that number directly. If a material source is empty or cannot be resolved, the workflow falls back to the numeric value already present in the input box.",
                ),
                html.Div(
                    "This matters in scattering because wavelength changes can update both medium and particle refractive indices before the Mie relation or calibration-standard model is computed.",
                ),
            ],
            min_height="unset",
        )

    def _resolution_order_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Resolution precedence",
            subtitle="RosettaX follows a deterministic order so the same input state yields the same numeric index values.",
            body=[
                html.Div(
                    [
                        html.Div("1. Source preset value", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("If a material source is selected, RosettaX attempts to resolve it at the current wavelength."),
                    ],
                    style={"marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div("2. Direct numeric source", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("If the source itself is numeric, that value is used directly without Sellmeier evaluation."),
                    ],
                    style={"marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div("3. Current input fallback", style={"fontWeight": "700", "marginBottom": "3px"}),
                        html.Div("If source resolution fails, RosettaX keeps the current numeric value entered in the field."),
                    ]
                ),
            ],
            min_height="unset",
        )

    def _quality_checks_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Quality checks before fitting",
            subtitle="Refractive index errors propagate directly into modeled coupling and can dominate scattering fit drift.",
            body=[
                html.Div("Re-check wavelength units and selected laser line when switching between instrument configurations."),
                html.Div("Ensure medium and particle values are physically plausible for the sample temperature and composition."),
                html.Div("When using core-shell models, verify core and shell values are intentionally different and consistent with the standard material."),
                html.Div("If calibration fit quality changes unexpectedly, re-validate refractive index sources before changing regression settings."),
            ],
            min_height="unset",
        )

    def _sellmeier_catalog_card(self) -> dbc.Card:
        material_rows = self._load_sellmeier_material_catalog()

        table = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Material ID", style={"width": "11%"}),
                            html.Th("Label", style={"width": "16%"}),
                            html.Th("a", style={"width": "7%"}),
                            html.Th("b coefficients", style={"width": "20%"}),
                            html.Th("c coefficients", style={"width": "20%"}),
                            html.Th("Notes", style={"width": "16%"}),
                            html.Th("Source", style={"width": "10%"}),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(row["id"], style={"fontFamily": "monospace", "fontSize": "0.82rem"}),
                                html.Td(row["label"], style={"fontWeight": "700"}),
                                html.Td(row["a"], style={"fontFamily": "monospace", "fontSize": "0.82rem"}),
                                html.Td(row["b"], style={"fontFamily": "monospace", "fontSize": "0.8rem"}),
                                html.Td(row["c"], style={"fontFamily": "monospace", "fontSize": "0.8rem"}),
                                html.Td(row["notes"], style={"fontSize": "0.82rem", "opacity": 0.9}),
                                html.Td(
                                    html.A("link", href=row["source"], target="_blank", style={"textDecoration": "none"})
                                    if row["source"]
                                    else "",
                                    style={"fontSize": "0.82rem"},
                                ),
                            ]
                        )
                        for row in material_rows
                    ]
                ),
            ],
            bordered=False,
            hover=False,
            responsive=True,
            size="sm",
            style={"marginBottom": "0px"},
        )

        return build_documentation_card(
            title="Sellmeier model catalog and coefficients",
            subtitle="Packaged refractive index models in RosettaX. Formula used: n^2 = a + sum(B_i * lambda^2 / (lambda^2 - C_i)), with wavelength in um.",
            body=[
                html.Div(
                    "The table below is loaded directly from RosettaX/assets/sellmeier_equations.json so documentation stays aligned with runtime behavior.",
                    style={"marginBottom": "10px"},
                ),
                table,
            ],
            min_height="unset",
        )


_page = RefractiveIndexDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/refractive-index",
    name="Refractive Index Documentation",
    layout=layout,
)
