# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

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
                dbc.Row(
                    [
                        dbc.Col(self._why_log_regression_card(), lg=7),
                        dbc.Col(self._when_linear_is_right_card(), lg=5),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._example_graph_card(),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._interpretation_card(), lg=7),
                        dbc.Col(self._diagnostics_card(), lg=5),
                    ],
                    className="g-3",
                ),
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

    def _why_log_regression_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Why log regression for fluorescence",
            subtitle="Fluorescence calibration usually behaves closer to multiplicative scaling than additive offset across decades of signal.",
            body=[
                html.Div(
                    "Fluorescence detector signals and reference units such as MESF usually span multiple orders of magnitude. In that regime, absolute errors naturally grow with signal level, so linear-space least squares can over-weight the high end.",
                ),
                html.Div(
                    "Log-space fitting treats proportional error more uniformly: a 10% miss at low signal and a 10% miss at high signal have comparable influence. That is typically closer to how calibration uncertainty behaves in practice.",
                ),
                html.Div(
                    "A log-log line also maps to a power law in original units, which is a practical model for detector-response scaling while preserving positivity of predictions.",
                ),
                self._math_block(
                    "$$\\text{Linear-space model: } y = m x + b$$\n$$\\text{Log-space model: } \\log_{10}(y) = s \\log_{10}(x) + i\\Rightarrow y = 10^i x^s$$"
                ),
            ],
            min_height="unset",
        )

    def _when_linear_is_right_card(self) -> dbc.Card:
        return build_documentation_card(
            title="When linear regression is still the right choice",
            subtitle="RosettaX uses linear response fitting for scattering because the modeled target quantity is treated as affine in measured peak units over the calibration range.",
            body=[
                html.Div(
                    "Scattering calibration in RosettaX maps measured peak positions to modeled coupling under a fixed optical model. In that workflow, a linear response model is used as an instrument conversion relation.",
                ),
                html.Div(
                    "This is not contradictory with fluorescence log fitting: the choice depends on the quantity being modeled, dynamic range behavior, and error structure for that workflow.",
                ),
                html.Div(
                    "In short: use log regression when multiplicative scaling dominates; use linear regression when affine response is the explicit instrument model assumption.",
                ),
            ],
            min_height="unset",
        )

    def _build_log_vs_linear_example_figure(self) -> go.Figure:
        x_values = np.geomspace(1.0e2, 1.0e6, 11)
        multiplicative_noise = np.asarray(
            [0.93, 1.06, 0.97, 1.11, 0.92, 1.08, 0.95, 1.04, 0.9, 1.07, 0.96],
            dtype=float,
        )

        y_values = 0.085 * np.power(x_values, 0.9) * multiplicative_noise

        linear_slope, linear_intercept = np.polyfit(
            x_values,
            y_values,
            deg=1,
        )
        y_linear_fit = linear_slope * x_values + linear_intercept

        log_x_values = np.log10(x_values)
        log_y_values = np.log10(y_values)
        log_slope, log_intercept = np.polyfit(
            log_x_values,
            log_y_values,
            deg=1,
        )
        y_log_fit = np.power(10.0, log_intercept) * np.power(x_values, log_slope)

        figure = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=(
                "Linear Axes",
                "Log-Log Axes",
            ),
            horizontal_spacing=0.12,
        )

        for column in (1, 2):
            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="markers",
                    marker={"size": 8, "color": "#111111"},
                    name="Synthetic fluorescence points",
                    legendgroup="data",
                    showlegend=column == 1,
                ),
                row=1,
                col=column,
            )
            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_linear_fit,
                    mode="lines",
                    line={"width": 2.4, "color": "#d62728"},
                    name="Linear-space fit",
                    legendgroup="linear",
                    showlegend=column == 1,
                ),
                row=1,
                col=column,
            )
            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_log_fit,
                    mode="lines",
                    line={"width": 2.4, "color": "#1f77b4", "dash": "dash"},
                    name="Log-space fit (mapped back)",
                    legendgroup="log",
                    showlegend=column == 1,
                ),
                row=1,
                col=column,
            )

        figure.update_xaxes(
            title_text="Measured signal",
            row=1,
            col=1,
        )
        figure.update_yaxes(
            title_text="Reference quantity",
            row=1,
            col=1,
        )
        figure.update_xaxes(
            type="log",
            title_text="Measured signal (log10)",
            row=1,
            col=2,
        )
        figure.update_yaxes(
            type="log",
            title_text="Reference quantity (log10)",
            row=1,
            col=2,
        )

        figure.update_layout(
            margin={"l": 44, "r": 18, "t": 56, "b": 44},
            legend={"orientation": "h", "y": -0.18, "x": 0.0},
            template="plotly_white",
            height=520,
        )

        return figure

    def _example_graph_card(self) -> dbc.Card:
        code_snippet = (
            "```python\n"
            "import numpy as np\n"
            "\n"
            "x = np.geomspace(1e2, 1e6, 11)\n"
            "y = 0.085 * x**0.9 * np.array([0.93, 1.06, 0.97, 1.11, 0.92, 1.08, 0.95, 1.04, 0.9, 1.07, 0.96])\n"
            "\n"
            "m_lin, b_lin = np.polyfit(x, y, 1)\n"
            "m_log, b_log = np.polyfit(np.log10(x), np.log10(y), 1)\n"
            "\n"
            "y_linear = m_lin * x + b_lin\n"
            "y_log = (10**b_log) * x**m_log\n"
            "```"
        )

        return build_documentation_card(
            title="Python example: linear fit vs log fit",
            subtitle="Synthetic example showing why linear-space fit can visually bias high-intensity points, while log-space fit better tracks proportional structure.",
            body=[
                dcc.Graph(
                    id=self._id("log-vs-linear-example"),
                    figure=self._build_log_vs_linear_example_figure(),
                    config={"displayModeBar": False},
                    style={"height": "540px", "width": "100%"},
                ),
                dcc.Markdown(
                    code_snippet,
                    style={"marginTop": "8px", "marginBottom": "0px"},
                ),
            ],
            min_height="unset",
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

    def _diagnostics_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Fit diagnostics checklist",
            subtitle="Use this checklist before accepting a calibration for export workflows.",
            body=[
                html.Div("Verify fit points span the intended dynamic range; narrow ranges can make coefficients unstable."),
                html.Div("Inspect residual directionality; systematic curvature often means model mismatch rather than random noise."),
                html.Div("Compare repeated runs with the same standards to estimate practical coefficient variability."),
                html.Div("Do not compare coefficients across incompatible payload contexts even if R² appears high."),
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
