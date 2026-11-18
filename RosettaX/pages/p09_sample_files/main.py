import json
import dash
import dash_bootstrap_components as dbc
from dash import html
from RosettaX.utils import directories, styling, ui_forms
from RosettaX.utils.upload_limits import format_upload_size

SAMPLE_FILES_BASE_URL = (
    "https://raw.githubusercontent.com/MartinPdeS/RosettaX/master/"
    "RosettaX/assets/sample-files"
)
SAMPLE_FILES_DIRECTORY = directories.asset_directory / "sample-files"
with (SAMPLE_FILES_DIRECTORY / "sample_file_metadata.json").open(encoding="utf-8") as metadata_file:
    SAMPLE_FILE_METADATA = json.load(metadata_file)


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
                            "Each download lists its file size."
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
                    self._build_validation_downloads(),
                    label="Cross-device validation",
                    tab_id="cross-instrument-validation",
                ),
                dbc.Tab(
                    self._build_download_sections(),
                    label="Summer school",
                    tab_id="summer-school",
                ),
            ],
            active_tab="cross-instrument-validation",
            className="mb-3",
        )

    def _build_validation_downloads(self) -> html.Div:
        """List the reduced cross-device calibration downloads."""
        return html.Div(
            [
                dbc.Alert(
                    [
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
                                title=instrument,
                                subtitle="",
                                color_name=color_name,
                                items=[{"download": filename}],
                            ),
                            md=6,
                            xl=4,
                        )
                        for instrument, color_name, filename in (
                            ("Apogee flow cytometer", "green", "apogee_rosetta_beads_1min_sliced.fcs"),
                            ("Northern Lights flow cytometer", "cyan", "northern_lights_rosetta_beads_2min_sliced.fcs"),
                            ("BD FACSLyric flow cytometer", "blue", "bd_facslyric_rosetta_3um_beads.fcs"),
                            ("BD FACSCanto I", "blue", "bd_facscanto_i_rosetta_beads.fcs"),
                            ("BD LSR II", "blue", "bd_lsrii_rosetta_beads.fcs"),
                            ("BD FACSCalibur", "blue", "bd_facscalibur_rosetta_beads.fcs"),
                            ("BD FACSymphony A1", "blue", "bd_facsymphony_a1_rosetta_beads.fcs"),
                            ("Beckman Coulter CytoFLEX S", "purple", "beckman_cytoflex_s_rosetta_beads.fcs"),
                            ("Miltenyi MACSQuant Analyzer 16", "pink", "miltenyi_macsquant_analyzer_16_rosetta_beads.fcs"),
                            ("Stratedigm S1313EX", "red", "stratedigm_s1313ex_rosetta_beads.fcs"),
                        )
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
                                        "download": "apogee_rainbow_beads.fcs",
                                    },
                                    {
                                        "title": "Mixed reference beads",
                                        "download": "apogee_mixed_reference_beads.fcs",
                                    },
                                    {
                                        "title": "Mystery beads",
                                        "download": "apogee_mystery_beads.fcs",
                                    },
                                    {
                                        "title": "Rosetta beads",
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
                                        "download": "northern_lights_rainbow_beads.fcs",
                                    },
                                    {
                                        "title": "Mixed reference beads",
                                        "download": "northern_lights_mixed_reference_beads.fcs",
                                    },
                                    {
                                        "title": "Mystery beads",
                                        "download": "northern_lights_mystery_beads.fcs",
                                    },
                                    {
                                        "title": "Rosetta beads",
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
                        self._build_download_item(
                            title=title,
                            download=item["download"],
                            color_name=color_name,
                            bordered=False,
                            show_detectors=True,
                        ),
                    ],
                    style={"padding": "10px 12px"},
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
                            title=item["title"],
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
        download: str,
        color_name: str,
        bordered: bool = True,
        show_detectors: bool = False,
    ) -> html.Div:
        """Build a download link with the file size and optional detector names."""
        metadata = SAMPLE_FILE_METADATA[download]
        asset_path = f"sample-files/{download}"
        href = (
            dash.get_asset_url(asset_path)
            if (SAMPLE_FILES_DIRECTORY / download).is_file()
            else f"{SAMPLE_FILES_BASE_URL}/{download}"
        )
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
                        html.Div(format_upload_size(metadata["size_bytes"]), className="small text-body-secondary"),
                        html.Div(
                            ", ".join(metadata["detectors"]),
                            className="small text-body-secondary",
                            style={"overflowWrap": "anywhere"},
                        ) if show_detectors else None,
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
