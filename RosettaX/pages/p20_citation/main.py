# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.pages.p07_documentation.components import (
    build_documentation_card,
    build_documentation_container,
    build_documentation_hero,
)


class CitationPage:
    """Citation and archival information for the versioned RosettaX release."""

    def __init__(self) -> None:
        self.page_name = "citation"
        self.zenodo_record_url = "https://zenodo.org/records/21309433"
        self.github_release_url = "https://github.com/MartinPdeS/RosettaX/tree/v0.5.0"
        self.bibtex = """@software{poinsinet_de_sivry_houle_2026_21309433,
  author = {Poinsinet de Sivry-Houle, Martin},
  title = {MartinPdeS/RosettaX: v0.5.0},
  year = {2026},
  publisher = {Zenodo},
  version = {v0.5.0},
  doi = {10.5281/zenodo.21309433},
  url = {https://doi.org/10.5281/zenodo.21309433}
}"""

    def _id(self, name: str) -> str:
        return f"{self.page_name}-{name}"

    def layout(self, **_kwargs) -> dbc.Container:
        return build_documentation_container(
            [
                build_documentation_hero(
                    hero_id=self._id("hero"),
                    title="Cite RosettaX",
                    description=(
                        "Use the archived v0.5.0 Zenodo record when RosettaX contributes "
                        "to a scientific workflow, analysis, or publication."
                    ),
                ),
                html.Div(style={"height": "18px"}),
                self._reference_card(),
                html.Div(style={"height": "18px"}),
                self._record_card(),
                html.Div(style={"height": "18px"}),
                self._citation_guidance_card(),
            ]
        )

    def _reference_card(self) -> dbc.Card:
        return build_documentation_card(
            title="BibTeX",
            subtitle="Copy this version-specific reference into your bibliography file.",
            body=[
                html.Pre(
                    self.bibtex,
                    id=self._id("bibtex"),
                    style={
                        "marginBottom": "0px",
                        "padding": "14px",
                        "backgroundColor": "rgba(0, 0, 0, 0.06)",
                        "borderRadius": "6px",
                        "whiteSpace": "pre-wrap",
                        "overflowX": "auto",
                    },
                )
            ],
            min_height="unset",
        )

    def _record_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Archived release",
            subtitle="RosettaX v0.5.0, published July 11, 2026.",
            body=[
                html.Div("DOI: 10.5281/zenodo.21309433", style={"marginBottom": "12px"}),
                html.Div(
                    [
                        dbc.Button(
                            "View Zenodo record",
                            href=self.zenodo_record_url,
                            color="primary",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"fontWeight": "700", "width": "100%"},
                        ),
                        dbc.Button(
                            "View source release",
                            href=self.github_release_url,
                            color="secondary",
                            outline=True,
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"width": "100%"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "10px",
                        "maxWidth": "320px",
                    },
                ),
            ],
            min_height="unset",
        )

    def _citation_guidance_card(self) -> dbc.Card:
        return build_documentation_card(
            title="Citation guidance",
            subtitle="Record the exact release used for reproducible analysis.",
            body=[
                html.Div(
                    "This citation identifies the archived software release that supplied the workflow and calibration tooling."
                ),
                html.Div(style={"height": "10px"}),
                html.Div(
                    "For work performed with another RosettaX version, cite that version's Zenodo record instead."
                ),
            ],
            min_height="unset",
        )


_page = CitationPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/citation",
    name="Citation",
    layout=layout,
)