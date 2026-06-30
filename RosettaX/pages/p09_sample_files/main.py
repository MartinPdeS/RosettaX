# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import styling, ui_forms


class SampleFilesPage:
    """
    Download page for RosettaX sample files.
    """

    def __init__(self) -> None:
        self.style = styling.PAGE

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                self._build_header_card(),
                self._build_download_sections(),
            ],
            fluid=True,
            style={
                **self.style,
                "paddingLeft": "0px",
                "paddingRight": "0px",
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Sample files",
                        title_component="H2",
                        description=(
                            "Download example FCS files and calibration JSON templates for fluorescence, "
                            "scattering, and apply-calibration testing. These bundled FCS examples come "
                            "from the Vesicle Center summer school on flow cytometry."
                        ),
                    ),
                ],
                style=ui_forms.build_workflow_section_body_style(),
            ),
            style={
                **ui_forms.build_workflow_section_card_style(
                    color_name=styling.get_workflow_page_header_color(),
                ),
                "marginBottom": "16px",
            },
        )

    def _build_download_sections(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(
                    self._build_download_card(
                        title="Apogee flow cytometer samples",
                        subtitle=(
                            "Four FCS datasets from the Vesicle Center summer school on flow cytometry, "
                            "acquired on an Apogee instrument."
                        ),
                        color_name=styling.get_workflow_section_color(1),
                        items=[
                            {
                                "title": "Rainbow beads",
                                "description": "Multi-color calibration standard for detector validation and linearity checks.",
                                "href": "/assets/sample-files/apogee_rainbow_beads.fcs",
                                "download": "apogee_rainbow_beads.fcs",
                            },
                            {
                                "title": "Mixed reference beads",
                                "description": "Apogee mix sample with multiple bead populations for scatter and fluorescence exercises.",
                                "href": "/assets/sample-files/apogee_mixed_reference_beads.fcs",
                                "download": "apogee_mixed_reference_beads.fcs",
                            },
                            {
                                "title": "Mystery beads",
                                "description": "Unknown bead mixture intended for identification and comparison exercises.",
                                "href": "/assets/sample-files/apogee_mystery_beads.fcs",
                                "download": "apogee_mystery_beads.fcs",
                            },
                            {
                                "title": "Rosetta beads (1 min)",
                                "description": "Rosetta bead acquisition with a one-minute run, useful for Rosetta Script testing.",
                                "href": "/assets/sample-files/apogee_rosetta_beads_1min.fcs",
                                "download": "apogee_rosetta_beads_1min.fcs",
                            },
                        ],
                    ),
                    lg=6,
                ),
                dbc.Col(
                    self._build_download_card(
                        title="Northern Lights flow cytometer samples",
                        subtitle=(
                            "Four FCS datasets from the Vesicle Center summer school on flow cytometry, "
                            "acquired on a Northern Lights instrument."
                        ),
                        color_name=styling.get_workflow_section_color(2),
                        items=[
                            {
                                "title": "Rainbow beads",
                                "description": "Multi-color calibration standard acquired on the Northern Lights platform.",
                                "href": "/assets/sample-files/northern_lights_rainbow_beads.fcs",
                                "download": "northern_lights_rainbow_beads.fcs",
                            },
                            {
                                "title": "Mixed reference beads",
                                "description": "Compressed Northern Lights acquisition of the Apogee mix reference sample.",
                                "href": "/assets/sample-files/northern_lights_mixed_reference_beads.fcs",
                                "download": "northern_lights_mixed_reference_beads.fcs",
                            },
                            {
                                "title": "Mystery beads",
                                "description": "Compressed Northern Lights acquisition of the unknown bead mixture.",
                                "href": "/assets/sample-files/northern_lights_mystery_beads.fcs",
                                "download": "northern_lights_mystery_beads.fcs",
                            },
                            {
                                "title": "Rosetta beads (2 min)",
                                "description": "Compressed Rosetta bead acquisition with a two-minute run for Rosetta workflow practice.",
                                "href": "/assets/sample-files/northern_lights_rosetta_beads_2min.fcs",
                                "download": "northern_lights_rosetta_beads_2min.fcs",
                            },
                        ],
                    ),
                    lg=6,
                ),
            ],
            className="g-3",
        )

    def _build_download_card(
        self,
        *,
        title: str,
        subtitle: str,
        color_name: str,
        items: list[dict[str, str]],
    ) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            title,
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            subtitle,
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=color_name,
                    ),
                ),
                dbc.CardBody(
                    [
                        self._build_download_item(
                            title=item["title"],
                            description=item["description"],
                            href=item["href"],
                            download=item["download"],
                            color_name=color_name,
                        )
                        for item in items
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "12px",
                        "padding": "16px",
                    },
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=color_name,
                style_overrides={
                    "height": "100%",
                },
            ),
        )

    def _build_download_item(
        self,
        *,
        title: str,
        description: str,
        href: str,
        download: str,
        color_name: str,
    ) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            title,
                            style={
                                "fontWeight": "700",
                                "marginBottom": "2px",
                            },
                        ),
                        html.Div(
                            description,
                            style={
                                "fontSize": "0.9rem",
                                "opacity": 0.78,
                            },
                        ),
                    ],
                    style={
                        "flex": "1 1 auto",
                        "minWidth": "0",
                    },
                ),
                html.A(
                    dbc.Button(
                        "Download",
                        color="primary",
                        outline=True,
                        size="sm",
                    ),
                    href=href,
                    download=download,
                    style={
                        "textDecoration": "none",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "gap": "12px",
                "padding": "11px 12px",
                "border": f"1px solid {styling.build_rgba(color_name, 0.22)}",
                "borderRadius": "10px",
                "background": styling.build_rgba(color_name, 0.04),
            },
        )


_page = SampleFilesPage()
layout = _page.layout


dash.register_page(
    __name__,
    path="/sample-files",
    name="Sample files",
    order=8,
    layout=layout,
)
