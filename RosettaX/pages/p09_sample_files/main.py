import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.utils import styling, ui_forms

SAMPLE_FILES_BASE_URL = (
    "https://raw.githubusercontent.com/MartinPdeS/RosettaX/master/"
    "RosettaX/assets/sample-files"
)


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
                self._build_tabs(),
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
                            "Browse the summer-school examples or cross-instrument Rosetta bead datasets. "
                            "Each collection includes source and acquisition details where available."
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

    def _build_tabs(self) -> dbc.Tabs:
        return dbc.Tabs(
            [
                dbc.Tab(
                    self._build_download_sections(),
                    label="Summer school",
                    tab_id="summer-school",
                ),
                dbc.Tab(
                    self._build_validation_placeholder(),
                    label="Cross-device validation",
                    tab_id="cross-instrument-validation",
                ),
            ],
            active_tab="summer-school",
            className="mb-3",
        )

    def _build_validation_placeholder(self) -> html.Div:
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H5(
                            "Cross-device Rosetta bead datasets",
                            className="alert-heading",
                        ),
                        html.P(
                            "Acquisition conditions and samples differ between files, "
                            "so these examples are not directly matched measurements.",
                            className="mb-0",
                        ),
                    ],
                    color="light",
                    className="mt-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self._build_download_card(
                                title="Apogee flow cytometer",
                                subtitle="1 minute",
                                color_name="green",
                                items=[
                                    {
                                        "title": "Rosetta beads (1 min)",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/apogee_rosetta_beads_1min.fcs",
                                        "download": "apogee_rosetta_beads_1min.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="Northern Lights flow cytometer",
                                subtitle="2 minutes",
                                color_name="cyan",
                                items=[
                                    {
                                        "title": "Rosetta beads (2 min)",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/northern_lights_rosetta_beads_2min.fcs",
                                        "download": "northern_lights_rosetta_beads_2min.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="BD FACSLyric flow cytometer",
                                subtitle="3 µm beads added · FSC and SSC at 350 V",
                                color_name="blue",
                                items=[
                                    {
                                        "title": "Rosetta beads + 3 µm beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/bd_facslyric_rosetta_3um_beads.fcs",
                                        "download": "bd_facslyric_rosetta_3um_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="BD FACSCanto I",
                                subtitle="15 May 2015",
                                color_name="blue",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/bd_facscanto_i_rosetta_beads.fcs",
                                        "download": "bd_facscanto_i_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="BD LSR II",
                                subtitle="10 June 2014",
                                color_name="blue",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/bd_lsrii_rosetta_beads.fcs",
                                        "download": "bd_lsrii_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="BD FACSCalibur",
                                subtitle="8 February 2023",
                                color_name="blue",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/bd_facscalibur_rosetta_beads.fcs",
                                        "download": "bd_facscalibur_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="BD FACSymphony A1",
                                subtitle="16 November 2022",
                                color_name="blue",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/bd_facsymphony_a1_rosetta_beads.fcs",
                                        "download": "bd_facsymphony_a1_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="Beckman Coulter CytoFLEX S",
                                subtitle="5 January 2023",
                                color_name="purple",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "Compressed FCS file; extract it before uploading to RosettaX.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/beckman_cytoflex_s_rosetta_beads.fcs.gz",
                                        "download": "beckman_cytoflex_s_rosetta_beads.fcs.gz",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="Miltenyi MACSQuant Analyzer 16",
                                subtitle="13 May 2022",
                                color_name="pink",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/miltenyi_macsquant_analyzer_16_rosetta_beads.fcs",
                                        "download": "miltenyi_macsquant_analyzer_16_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                        dbc.Col(
                            self._build_download_card(
                                title="Stratedigm S1313EX",
                                subtitle="15 May 2014",
                                color_name="red",
                                items=[
                                    {
                                        "title": "Rosetta beads",
                                        "description": "",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/stratedigm_s1313ex_rosetta_beads.fcs",
                                        "download": "stratedigm_s1313ex_rosetta_beads.fcs",
                                    },
                                ],
                            ),
                            md=6, xl=4,
                        ),
                    ],
                    className="g-2",
                ),
            ],
        )

    def _build_download_sections(self) -> html.Div:
        return html.Div(
            [
                html.P(
                    "The Flow Cytometry Summer School is held each summer at Amsterdam UMC. "
                    "These example FCS files come from the course and are shared for "
                    "hands-on practice with bead standards, instrument data, and "
                    "calibration workflows. The collection includes acquisitions from "
                    "Apogee and Northern Lights flow cytometers."
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self._build_download_card(
                                title="Apogee flow cytometer samples",
                                subtitle=(
                                    "Four FCS datasets shared for the Flow Cytometry Summer School at Amsterdam UMC, "
                                    "acquired on an Apogee instrument."
                                ),
                                color_name=styling.get_workflow_section_color(1),
                                items=[
                                    {
                                        "title": "Rainbow beads",
                                        "description": "Multi-color calibration standard for detector validation and linearity checks.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/apogee_rainbow_beads.fcs",
                                        "download": "apogee_rainbow_beads.fcs",
                                    },
                                    {
                                        "title": "Mixed reference beads",
                                        "description": "Apogee mix sample with multiple bead populations for scatter and fluorescence exercises.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/apogee_mixed_reference_beads.fcs",
                                        "download": "apogee_mixed_reference_beads.fcs",
                                    },
                                    {
                                        "title": "Mystery beads",
                                        "description": "Unknown bead mixture intended for identification and comparison exercises.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/apogee_mystery_beads.fcs",
                                        "download": "apogee_mystery_beads.fcs",
                                    },
                                    {
                                        "title": "Rosetta beads (1 min)",
                                        "description": "Rosetta bead acquisition with a one-minute run, useful for Rosetta Script testing.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/apogee_rosetta_beads_1min.fcs",
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
                                    "Four FCS datasets shared for the Flow Cytometry Summer School at Amsterdam UMC, "
                                    "acquired on a Northern Lights instrument."
                                ),
                                color_name=styling.get_workflow_section_color(2),
                                items=[
                                    {
                                        "title": "Rainbow beads",
                                        "description": "Multi-color calibration standard acquired on the Northern Lights platform.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/northern_lights_rainbow_beads.fcs",
                                        "download": "northern_lights_rainbow_beads.fcs",
                                    },
                                    {
                                        "title": "Mixed reference beads",
                                        "description": "Compressed Northern Lights acquisition of the Apogee mix reference sample.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/northern_lights_mixed_reference_beads.fcs",
                                        "download": "northern_lights_mixed_reference_beads.fcs",
                                    },
                                    {
                                        "title": "Mystery beads",
                                        "description": "Compressed Northern Lights acquisition of the unknown bead mixture.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/northern_lights_mystery_beads.fcs",
                                        "download": "northern_lights_mystery_beads.fcs",
                                    },
                                    {
                                        "title": "Rosetta beads (2 min)",
                                        "description": "Compressed Rosetta bead acquisition with a two-minute run for Rosetta workflow practice.",
                                        "href": f"{SAMPLE_FILES_BASE_URL}/northern_lights_rosetta_beads_2min.fcs",
                                        "download": "northern_lights_rosetta_beads_2min.fcs",
                                    },
                                ],
                            ),
                            lg=6,
                        ),
                    ],
                    className="g-3",
                ),
            ]
        )

    def _build_download_card(
        self,
        *,
        title: str,
        subtitle: str,
        color_name: str,
        items: list[dict[str, str]],
    ) -> dbc.Card:
        if len(items) == 1:
            item = items[0]
            return dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.Div(title, style={"fontWeight": "700"}),
                                html.Div(subtitle, style={"fontSize": "0.85rem", "opacity": 0.75}),
                                html.Div(item["description"], style={"fontSize": "0.85rem", "opacity": 0.75}) if item["description"] else None,
                            ],
                            style={"minWidth": "0", "flex": "1 1 auto"},
                        ),
                        html.A(
                            dbc.Button("Download", color="primary", outline=True, size="sm"),
                            href=item["href"],
                            download=item["download"],
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "12px", "padding": "10px 12px"},
                ),
                style=ui_forms.build_workflow_subpanel_card_style(
                    color_name=color_name,
                    style_overrides={"background": styling.build_rgba(color_name, 0.04), "height": "100%"},
                ),
            )
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
                            title=item["title"] if len(items) > 1 else "",
                            description=item["description"],
                            href=item["href"],
                            download=item["download"],
                            color_name=color_name,
                            bordered=len(items) > 1,
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
        bordered: bool = True,
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
                        ) if title else None,
                        html.Div(
                            description,
                            style={
                                "fontSize": "0.9rem",
                                "opacity": 0.78,
                            },
                        ) if description else None,
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
                **({
                    "padding": "11px 12px",
                    "border": f"1px solid {styling.build_rgba(color_name, 0.22)}",
                    "borderRadius": "10px",
                    "background": styling.build_rgba(color_name, 0.04),
                } if bordered else {}),
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
