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


class RegressionModelsDocumentationPage:
    """
    Detailed documentation for RosettaX regression models.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-regression-models"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Regression Models",
                    description=(
                        "This page explains the fitted relations behind RosettaX fluorescence and scattering calibrations: "
                        "which quantities are paired, which transforms are applied before fitting, and what assumptions "
                        "you should keep in mind when reading or comparing calibration records."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use the hub for the broader technical overview.",
                    body=[
                        html.Div(
                            [
                                build_documentation_link_chip(
                                    label="Back to documentation hub",
                                    href="/documentation",
                                ),
                                build_documentation_link_chip(
                                    label="Peak scripts",
                                    href="/documentation/peak-scripts",
                                ),
                                build_documentation_link_chip(
                                    label="Supported cytometers",
                                    href="/documentation/supported-cytometers",
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
                        dbc.Col(self._fluorescence_card(), lg=6),
                        dbc.Col(self._scattering_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._interpretation_card(),
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

    def _fluorescence_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Fluorescence fit model",
            subtitle="A log-log linear fit, which is equivalent to a power law in the original units.",
            body=[
                self._math_block(
                    "$$\\log_{10}(y) = \\text{slope} \\cdot \\log_{10}(x) + \\text{intercept}$$\n$$y = 10^{\\text{intercept}} \\cdot x^{\\text{slope}}$$",
                ),
                html.Div(
                    "Here x is the measured detector value and y is the calibrated fluorescence reference quantity such as MESF. RosettaX removes non-finite or non-positive pairs before fitting because the logarithm must be defined on both axes.",
                ),
                html.Div(
                    "A slope near 1 means the measured axis already scales almost proportionally to the calibrated quantity on log axes. The intercept then captures the multiplicative offset between the two scales.",
                ),
            ],
        )

    def _scattering_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Scattering fit model",
            subtitle="A linear instrument-response fit from measured peak positions to modeled optical coupling.",
            body=[
                self._math_block(
                    "$$\\text{theoretical coupling} = \\text{slope} \\cdot \\text{measured peak} + \\text{intercept}$$",
                ),
                html.Div(
                    "The theoretical values come from the chosen Mie model plus the detector geometry assumptions. RosettaX is therefore fitting instrument response against a modeled optical target, not fitting bead diameter directly against detector counts.",
                ),
                html.Div(
                    "The default workflow usually fixes the intercept to zero. When that assumption is used, the fitted slope represents the conversion factor from measured channel units into modeled coupling units under the chosen optical model.",
                ),
            ],
        )

    def _interpretation_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to interpret and compare calibrations",
            subtitle="The fitted coefficients only make sense in the context of the payload and the modeling choices they came from.",
            body=[
                html.Div(
                    "For fluorescence, compare slopes and intercepts only when the same detector channel and reference bead family were used. A different detector gain regime or different bead standard can change the coefficients even if the workflow is correct.",
                ),
                html.Div(
                    "For scattering, compare fits only when the optical geometry, wavelength, particle model, refractive indices, and standard table assumptions are compatible. The response coefficients are downstream of all of those modeling choices.",
                ),
                html.Div(
                    "In both cases, the saved calibration JSON should be treated as the authoritative context. The regression numbers alone are not enough to decide whether two calibrations are scientifically equivalent.",
                ),
            ],
            min_height="unset",
        )


_page = RegressionModelsDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/regression-models",
    name="Regression Models Documentation",
    layout=layout,
)
