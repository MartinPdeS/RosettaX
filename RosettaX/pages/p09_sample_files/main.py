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
                            "scattering, and apply-calibration testing."
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
                        subtitle="Real calibration data from an Apogee cytometer with multiple bead sets.",
                        color_name=styling.get_workflow_section_color(1),
                        items=[
                            {
                                "title": "Rainbow beads",
                                "description": "Multi-color calibration standard for detector validation and linearity checks.",
                                "href": "/assets/sample-files/apogee_rainbow_beads.fcs",
                                "download": "apogee_rainbow_beads.fcs",
                            },
                            {
                                "title": "Apogee mix beads",
                                "description": "Mixed Apogee reference particles for multi-parameter calibration.",
                                "href": "/assets/sample-files/apogee_mix.fcs",
                                "download": "apogee_mix.fcs",
                            },
                        ],
                    ),
                    lg=6,
                ),
                dbc.Col(
                    self._build_download_card(
                        title="Cytek Northern Lights samples",
                        subtitle="Real calibration data from a Cytek Northern Lights flow cytometer.",
                        color_name=styling.get_workflow_section_color(2),
                        items=[
                            {
                                "title": "Rainbow beads",
                                "description": "Multi-color calibration standard acquired on Cytek platform.",
                                "href": "/assets/sample-files/cytek_rainbow_beads.fcs",
                                "download": "cytek_rainbow_beads.fcs",
                            },
                            {
                                "title": "Apogee mix beads",
                                "description": "Mixed reference particles measured on Cytek instrument.",
                                "href": "/assets/sample-files/cytek_apogee_mix.fcs",
                                "download": "cytek_apogee_mix.fcs",
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
