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


class PeakScriptsDocumentationPage:
    """
    Detailed documentation for RosettaX peak identification scripts.
    """

    def __init__(self) -> None:
        self.page_name = "documentation-peak-scripts"

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Peak Process Scripts",
                    description=(
                        "This page goes deeper into RosettaX peak identification processes: what each script sees, "
                        "which graph mode it uses, when it is a good fit, and what to adjust when the first result "
                        "does not match the populations you expect."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                build_documentation_card(
                    title="Related pages",
                    subtitle="Use the documentation hub to jump across topics.",
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
                        dbc.Col(self._manual_scripts_card(), lg=6),
                        dbc.Col(self._automatic_histogram_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                dbc.Row(
                    [
                        dbc.Col(self._clustering_scripts_card(), lg=6),
                        dbc.Col(self._rosetta_script_card(), lg=6),
                    ],
                    className="g-3",
                ),
                html.Div(style={"height": "18px"}),
                self._comparison_matrix_card(),
                html.Div(style={"height": "18px"}),
                self._workflow_advice_card(),
                html.Div(style={"height": "18px"}),
                self._troubleshooting_card(),
            ]
        )

    def _manual_scripts_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Manual scripts",
            subtitle="Best when your eye can recognize peaks more reliably than a generic detector.",
            body=[
                html.Div(
                    "Manual 1D uses one histogram and stores the x-position of every click. It is the safest fallback when you only trust a single detector axis and want to decide each peak yourself.",
                ),
                html.Div(
                    "Manual 2D uses two detector channels and records the x-coordinate of the clicked event or snapped local mode. Use it when fluorescence or a second scatter-like channel helps separate populations that overlap on x alone.",
                ),
                html.Div(
                    "For both manual scripts, the graph itself is part of the input. Zooming, panning, and choosing the right axis scale can change how easy it is to place peaks accurately.",
                ),
            ],
        )

    def _automatic_histogram_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Histogram and density peak finders",
            subtitle="Good first choices when populations are reasonably separated and you want repeatable automation.",
            body=[
                html.Div(
                    "Automatic 1D and Prominence 1D both work from a smoothed histogram in log space. Automatic 1D is the simpler preset-driven option; Prominence 1D exposes the sensitivity controls so you can reject shallow shoulders or split broad modes more aggressively.",
                ),
                html.Div(
                    "Prominence 2D works in a density view rather than a single histogram. It is more helpful when the peak structure is visible as separated clouds in 2D even if the 1D projection looks merged.",
                ),
                html.Div(
                    "If these scripts return too many peaks, increase the minimum prominence or minimum distance. If they miss small but real peaks, loosen those thresholds before switching to a different family.",
                ),
            ],
        )

    def _clustering_scripts_card(self) -> dbc.Card:
        return build_documentation_card(
            title="K-means scripts",
            subtitle="Choose these when you know approximately how many populations should exist.",
            body=[
                html.Div(
                    "Gated K-means 1D clusters one channel in log10 space and reports cluster centroids as peak positions. It is useful when the populations are broad and the histogram contains plateaus instead of sharp maxima.",
                ),
                html.Div(
                    "Gated K-means 2D clusters in joint x-y space and then reports the x-coordinate of each centroid back into the calibration table. This can separate overlapping x populations when y provides the missing contrast.",
                ),
                html.Div(
                    "The main tradeoff is that K-means always partitions the data into the requested number of clusters, even if one of those clusters is weak or not physically meaningful. The cluster count therefore matters more than in prominence-based workflows.",
                ),
            ],
        )

    def _rosetta_script_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Rosetta script",
            subtitle="Specialized for Rosetta mixtures with fluorescent marker beads and non-fluorescent polystyrene peaks.",
            body=[
                html.Div(
                    "The Rosetta workflow uses the fluorescence channel to identify the marker populations first, then uses those markers to interpret the scattering populations. This makes it more robust when the largest beads saturate or the smallest beads disappear into noise.",
                ),
                html.Div(
                    "Marker peaks are used as anchors. Non-fluorescent peaks are the ones written into the calibration table by default, while marker-derived scatter peaks remain visible on the graph as orientation cues.",
                ),
                html.Div(
                    "Use this script when the sample composition is known in advance and you want RosettaX to exploit that prior structure instead of treating the mixture like a generic unknown histogram.",
                ),
            ],
        )

    def _workflow_advice_card(self) -> dbc.Card:
        return build_documentation_card(
            title="How to choose quickly",
            subtitle="A practical decision rule for day-to-day calibration work.",
            body=[
                html.Div("Start with Automatic 1D or Prominence 1D when one detector clearly carries the separation you need."),
                html.Div("Move to Manual 2D or Prominence 2D when a second channel makes the populations visually obvious."),
                html.Div("Use K-means when the number of populations is known but their shapes are broad or uneven."),
                html.Div("Use the Rosetta script when you are specifically working with the Rosetta bead mixture and want marker-guided interpretation."),
            ],
            min_height="unset",
        )

    def _comparison_matrix_card(self) -> dbc.Card:
        table = dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Script family"),
                            html.Th("Best when"),
                            html.Th("Main control"),
                            html.Th("Common failure mode"),
                        ]
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td("Manual 1D / 2D", style={"fontWeight": "700"}),
                                html.Td("Peaks are visually clear but automation is unstable."),
                                html.Td("User clicks and axis scaling."),
                                html.Td("Inconsistent click placement across repeats."),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td("Automatic / Prominence", style={"fontWeight": "700"}),
                                html.Td("Histogram or density ridges are distinct."),
                                html.Td("Prominence, width, and minimum distance thresholds."),
                                html.Td("Over-splitting shoulders or missing weak peaks."),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td("K-means", style={"fontWeight": "700"}),
                                html.Td("Population count is known but peaks are broad."),
                                html.Td("Number of clusters and selected channel(s)."),
                                html.Td("Forced clusters for weak or absent populations."),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td("Rosetta script", style={"fontWeight": "700"}),
                                html.Td("Rosetta mixture with marker-guided structure."),
                                html.Td("Correct fluorescence marker channel."),
                                html.Td("Marker mismatch when fluorescence channel selection is wrong."),
                            ]
                        ),
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
            title="Script comparison matrix",
            subtitle="Use this matrix to pick the first script family before tuning parameters.",
            body=[table],
            min_height="unset",
        )

    def _troubleshooting_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Troubleshooting pattern",
            subtitle="A repeatable escalation path when first-pass peak selection is poor.",
            body=[
                html.Div("Step 1: verify detector channel selection and axis scale before changing script parameters."),
                html.Div("Step 2: tighten or loosen one parameter at a time, then compare resulting peak tables."),
                html.Div("Step 3: switch script family only after confirming the data topology does not suit the current method."),
                html.Div("Step 4: if ambiguity remains, keep manual picks and document why automation was rejected for that run."),
            ],
            min_height="unset",
        )


_page = PeakScriptsDocumentationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/documentation/peak-scripts",
    name="Peak Scripts Documentation",
    layout=layout,
)
