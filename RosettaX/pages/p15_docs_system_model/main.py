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


class SystemModelDocumentationPage:
    """
    Detailed documentation for RosettaX system assumptions and scattering optics.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-system-model"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="System Model and Optics",
                    description=(
                        "This page explains what kind of instrument output RosettaX assumes, where the software sits in the "
                        "workflow after acquisition, and how the scattering backend models optical collection geometry."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use the documentation hub to move between system assumptions and downstream calibration behavior.",
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
                        dbc.Col(self._fcs_system_card(), lg=6),
                        dbc.Col(self._scattering_optics_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._assumption_boundaries_card(), lg=6),
                        dbc.Col(self._practical_validation_card(), lg=6),
                    ],
                    className="g-3",
                ),
            ]
        )

    def _fcs_system_card(self) -> dbc.Card:
        return build_documentation_card(
            title="What kind of system RosettaX assumes",
            subtitle="RosettaX analyzes exported FCS data. It does not control the cytometer.",
            body=[
                html.Div(
                    "RosettaX assumes a standard event table exported from a flow cytometer, where each row is one event and each selected channel is an already processed instrument observable rather than a raw optical power trace.",
                ),
                html.Div(
                    "For fluorescence, the software works with one selected detector column plus optional gating context. For scattering, it treats the selected detector column as the measured instrument response that must be mapped to modeled optical coupling.",
                ),
                html.Div(
                    "The application therefore sits after acquisition: it inspects histograms and tables, fits calibration relations, serializes calibration records, and later re-applies those records to other FCS files.",
                ),
            ],
        )

    def _scattering_optics_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Scattering optical model",
            subtitle="The scattering workflow uses a single-wavelength source plus photodiode-style collection geometry.",
            body=[
                html.Div(
                    "The scattering backend builds a Gaussian illumination source and a photodiode detector model through PyMieSim. The configurable optical terms are wavelength, detector NA, cache NA, blocker-bar NA, detector phi offset, detector gamma offset, and detector sampling.",
                ),
                html.Div(
                        "Internally, the modeled source defaults to optical power = 1.0 W, source numerical aperture = 0.1, and polarization angle = 0 degrees. Detector presets can inject angular weights and effective geometry corrections before coupling is computed.",
                ),
                html.Div(
                    "That means RosettaX is calibrating a measured scatter channel against a modeled collection geometry, not against raw Mie intensity integrated over an unspecified instrument.",
                ),
            ],
        )

    def _assumption_boundaries_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Assumption boundaries",
            subtitle="Use these boundaries to decide when a packaged detector preset is adequate versus when custom tuning is required.",
            body=[
                html.Div("Preset support means the geometry is documented and reproducible, not that every hardware detail of an instrument is reverse engineered."),
                html.Div("If your cytometer uses unusual collection optics, aperture masks, or channel definitions, treat packaged presets as starting points and verify against known standards."),
                html.Div("Strong calibration agreement across standards is a practical validation signal; weak agreement usually points to geometry mismatch, peak selection issues, or sample/model incompatibility."),
            ],
            min_height="unset",
        )

    def _practical_validation_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Practical validation checklist",
            subtitle="A compact set of checks before trusting fitted scattering coefficients.",
            body=[
                html.Div("Check that peak positions are stable under small script parameter changes and not driven by one ambiguous peak."),
                html.Div("Confirm detector preset and channel mapping match expected FSC/SSC semantics for the instrument family."),
                html.Div("Verify refractive index inputs and wavelength are physically reasonable for the actual sample and buffer."),
                html.Div("Inspect the fitted line and residual behavior before exporting; do not rely only on one scalar metric."),
            ],
            min_height="unset",
        )


_page = SystemModelDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/system-model",
    name="System Model Documentation",
    layout=layout,
)
