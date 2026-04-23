# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms


class HelpPage:
    def __init__(self) -> None:
        self.path = "/help"
        self.name = "Help"
        self.page_title = "Help"
        self.container_style = {
            "paddingTop": "24px",
            "paddingBottom": "48px",
        }

    def layout(self, **_kwargs) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(style={"height": "20px"}),
                self._quick_start_row(),
                html.Div(style={"height": "20px"}),
                self._accordion_section(),
                html.Div(style={"height": "20px"}),
                self._diagnostics_card(),
            ],
            fluid=True,
            style=self.container_style,
        )

    def _hero_section(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title=self.page_title,
                        title_component="H2",
                        description=(
                            "RosettaX is organized around three main tasks: building a fluorescence calibration, "
                            "building a scattering calibration, and applying a saved calibration to one or more FCS files."
                        ),
                    ),
                ]
            )
        )

    def _quick_start_row(self) -> dbc.Row:
        return dbc.Row(
            [
                dbc.Col(self._quick_start_card(), md=8),
                dbc.Col(self._where_to_go_card(), md=4),
            ],
            className="g-3",
        )

    def _quick_start_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Quick start"),
                dbc.CardBody(
                    [
                        html.Ol(
                            [
                                html.Li("Go to Fluorescence or Scattering depending on the calibration you want to build."),
                                html.Li("Upload the FCS file used for the calibration workflow."),
                                html.Li("Select the relevant detector channels and review the intermediate outputs."),
                                html.Li("Fit the calibration and save it as a JSON payload."),
                                html.Li("Use Apply Calibration to reuse that saved payload on new files."),
                            ],
                            style={"marginBottom": "0px"},
                        )
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _where_to_go_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("Go directly to"),
                dbc.CardBody(
                    [
                        dbc.Button(
                            "Fluorescence",
                            href="/fluorescence",
                            color="success",
                            style={"width": "100%", "marginBottom": "10px"},
                        ),
                        dbc.Button(
                            "Scattering",
                            href="/scattering",
                            color="secondary",
                            style={"width": "100%", "marginBottom": "10px"},
                        ),
                        dbc.Button(
                            "Apply calibration",
                            href="/calibrate",
                            color="primary",
                            outline=True,
                            style={"width": "100%", "marginBottom": "10px"},
                        ),
                        dbc.Button(
                            "Settings",
                            href="/settings",
                            color="dark",
                            outline=True,
                            style={"width": "100%"},
                        ),
                    ]
                ),
            ],
            style={"height": "100%"},
        )

    def _accordion_section(self) -> dbc.Accordion:
        return dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        html.H4("What RosettaX does"),
                        html.P(
                            "RosettaX provides a structured workflow to inspect FCS data, derive calibration parameters, save those parameters as JSON, and later reuse them through the apply page."
                        ),
                        html.Ul(
                            [
                                html.Li("Fluorescence workflow for deriving an intensity based calibration."),
                                html.Li("Scattering workflow for deriving a scatter based calibration."),
                                html.Li("Apply workflow for exporting calibrated FCS files."),
                                html.Li("Sidebar based access to saved calibration payloads."),
                            ]
                        ),
                    ],
                    title="Overview",
                ),
                dbc.AccordionItem(
                    [
                        html.H4("Fluorescence calibration workflow"),
                        html.P(
                            "This workflow is intended for building a fluorescence calibration from bead data."
                        ),
                        html.Ol(
                            [
                                html.Li("Upload the bead FCS file."),
                                html.Li("Choose the scattering channel used to gate out low signal noise."),
                                html.Li("Estimate or manually enter a threshold."),
                                html.Li("Choose the fluorescence detector and inspect the gated fluorescence histogram."),
                                html.Li("Find the fluorescence peaks corresponding to the bead populations."),
                                html.Li("Fill the MESF table and fit the calibration."),
                                html.Li("Save the resulting calibration payload for reuse."),
                            ]
                        ),
                        dbc.Alert(
                            "The scattering threshold controls the quality of fluorescence peak detection. If the fluorescence histogram looks messy, inspect the gating first.",
                            color="info",
                        ),
                    ],
                    title="Fluorescence calibration",
                ),
                dbc.AccordionItem(
                    [
                        html.H4("Scattering calibration workflow"),
                        html.P(
                            "This workflow is intended for building a scattering calibration from an uploaded calibration file and the required model or fit parameters."
                        ),
                        html.Ul(
                            [
                                html.Li("Upload the file used for the scattering calibration workflow."),
                                html.Li("Select the scattering detector that should be analyzed."),
                                html.Li("Adjust the required parameters and inspect the fit output."),
                                html.Li("Save the resulting calibration so it can be reused later."),
                            ]
                        ),
                        dbc.Alert(
                            "If the fit is unstable or unexpected, verify that the selected detector and parameter values are consistent with the intended calibration dataset.",
                            color="warning",
                        ),
                    ],
                    title="Scattering calibration",
                ),
                dbc.AccordionItem(
                    [
                        html.H4("Apply calibration workflow"),
                        html.P(
                            "Use the apply page when you already have a saved calibration and want to export calibrated FCS files."
                        ),
                        html.Ul(
                            [
                                html.Li("Select a saved calibration from the dropdown or from the sidebar Apply link."),
                                html.Li("Upload one or more FCS files."),
                                html.Li("Use the first file as the detector schema reference."),
                                html.Li("Choose the target channel to calibrate."),
                                html.Li("Choose the additional channels to export unchanged."),
                                html.Li("Export calibrated outputs. Multi file export should produce one calibrated file per uploaded file."),
                            ]
                        ),
                        dbc.Alert(
                            "When applying a calibration to multiple files, the uploaded files should have matching detector names and compatible structure.",
                            color="info",
                        ),
                    ],
                    title="Apply saved calibration",
                ),
                dbc.AccordionItem(
                    [
                        html.H4("Saved calibrations and sidebar behavior"),
                        html.P(
                            "Saved calibrations are stored as JSON files and listed in the sidebar."
                        ),
                        html.Ul(
                            [
                                html.Li("Click the calibration name to inspect the JSON payload."),
                                html.Li("Click Apply to open the apply page with that calibration preselected."),
                                html.Li("Use Refresh if you added or modified calibration files externally."),
                                html.Li("Use Open folder to inspect the calibration directory directly in your file manager."),
                            ]
                        ),
                    ],
                    title="Saved calibrations",
                ),
                dbc.AccordionItem(
                    [
                        html.H4("Typical issues"),
                        html.Ul(
                            [
                                html.Li("No dropdown options after upload: confirm the file uploaded correctly and that the FCS columns are readable."),
                                html.Li("Histograms look empty: check detector selection, threshold values, and whether the file contains events in the expected range."),
                                html.Li("Peak finding is poor: revisit the thresholding and the chosen histogram settings."),
                                html.Li("Calibration fit looks wrong: verify that the reference values correspond to the correct measured peaks."),
                                html.Li("Apply page export is incomplete: check target channel selection and the selected export columns."),
                                html.Li("Sidebar looks stale: use Refresh or verify that the calibration files were actually written to the expected calibration directory."),
                            ]
                        ),
                    ],
                    title="Troubleshooting",
                ),
            ],
            start_collapsed=True,
            always_open=False,
        )

    def _diagnostics_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("What to collect when something looks wrong"),
                dbc.CardBody(
                    [
                        html.P(
                            "When diagnosing a workflow issue, the most useful information is usually:"
                        ),
                        html.Ul(
                            [
                                html.Li("the page you were using"),
                                html.Li("the uploaded file name"),
                                html.Li("the selected detector names"),
                                html.Li("the threshold value if thresholding was involved"),
                                html.Li("a screenshot of the histogram or fit result"),
                                html.Li("the saved calibration JSON if the issue is in the apply step"),
                            ],
                            style={"marginBottom": "12px"},
                        ),
                        dbc.Alert(
                            "In practice, screenshots of the relevant plots plus the selected detector names are enough to diagnose most UI level calibration problems.",
                            color="secondary",
                            style={"marginBottom": "0px"},
                        ),
                    ]
                ),
            ]
        )


_page = HelpPage()
layout = _page.layout

dash.register_page(
    __name__,
    path="/help",
    name="Help",
    order=3,
    layout=layout,
)