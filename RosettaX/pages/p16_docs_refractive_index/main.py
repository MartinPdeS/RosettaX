# -*- coding: utf-8 -*-

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
                self._resolution_card(),
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


_page = RefractiveIndexDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/refractive-index",
    name="Refractive Index Documentation",
    layout=layout,
)
