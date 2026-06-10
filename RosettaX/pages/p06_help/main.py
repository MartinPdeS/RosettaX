# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc
from dash import html

from RosettaX.utils import ui_forms


class HelpPage:
    """
    Help page for RosettaX.

    Responsibilities
    ----------------
    - Provide a short getting-started surface for new users.
    - Provide operational help when something looks wrong.
    - Keep troubleshooting and diagnostics separate from the documentation page.
    - Focus on debugging context rather than workflow orientation.
    """

    def __init__(
        self,
    ) -> None:
        self.page_name = "help"

    def _id(
        self,
        name: str,
    ) -> str:
        return f"{self.page_name}-{name}"

    def layout(
        self,
        **_kwargs,
    ) -> dbc.Container:
        return dbc.Container(
            [
                self._hero_section(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._support_scope_row(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._troubleshooting_card(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._diagnostics_card(),
            ],
            fluid=True,
            style={
                "paddingTop": "12px",
                "paddingBottom": "40px",
            },
        )

    def _hero_section(self) -> dbc.Card:
        """
        Build the help page hero section.
        """
        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            "Help",
                            style={
                                "fontWeight": "800",
                                "fontSize": "2.35rem",
                                "lineHeight": "1.08",
                                "marginBottom": "8px",
                            },
                        ),
                        html.Div(
                            (
                                "Use this page when you need the shortest route to getting started or when a fit, "
                                "table, plot, sidebar state, or export looks wrong and you need debugging context."
                            ),
                            style={
                                "fontSize": "1.06rem",
                                "opacity": 0.86,
                                "maxWidth": "980px",
                                "marginBottom": "0px",
                            },
                        ),
                    ],
                    style={
                        "padding": "26px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _support_scope_row(self) -> dbc.Row:
        """
        Build support scope cards.
        """
        return dbc.Row(
            [
                dbc.Col(
                    self._getting_started_card(),
                    lg=4,
                ),
                dbc.Col(
                    self._when_to_use_help_card(),
                    lg=4,
                ),
                dbc.Col(
                    self._before_debugging_card(),
                    lg=4,
                ),
            ],
            className="g-3",
        )

    def _getting_started_card(self) -> dbc.Card:
        """
        Build a quick getting-started card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Getting started",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Use Help for first-run orientation. Use Documentation for internals.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                self._numbered_instruction(
                                    index=1,
                                    title="Choose the workflow first",
                                    description=(
                                        "Fluorescence builds empirical intensity calibrations, scattering builds model-based "
                                        "optical calibrations, and Apply calibration reuses a saved JSON on experimental files."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=2,
                                    title="Inspect before fitting",
                                    description=(
                                        "Look at the detector selection, histogram or peak graph, and calibration table before "
                                        "treating the fit button as the real decision point."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=3,
                                    title="Save the JSON, then export with the PDF",
                                    description=(
                                        "The calibration JSON is the reusable record. The PDF report explains one apply/export run."
                                    ),
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "10px",
                            },
                        ),
                        html.Hr(
                            style={
                                "margin": "14px 0px",
                                "opacity": 0.18,
                            }
                        ),
                        html.Div(
                            "Try RosettaX with sample files",
                            style={
                                "fontWeight": "700",
                                "marginBottom": "6px",
                            },
                        ),
                        html.Div(
                            "Download a sample FCS file and matching saved calibrations to explore the workflows before using your own data.",
                            style={
                                "fontSize": "0.92rem",
                                "opacity": 0.78,
                                "marginBottom": "12px",
                            },
                        ),
                        html.Div(
                            [
                                self._sample_download_item(
                                    title="Sample FCS file",
                                    description="Use this file to inspect detector columns and try the calibration pages.",
                                    file_name="sample_fcs.fcs",
                                ),
                                self._sample_download_item(
                                    title="Sample fluorescence calibration",
                                    description="Load this JSON in Apply calibration to see the fluorescence export flow.",
                                    file_name="sample_fluorescence_calibration.json",
                                ),
                                self._sample_download_item(
                                    title="Sample scattering calibration",
                                    description="Load this JSON in Apply calibration to try the scattering target-model workflow.",
                                    file_name="sample_scatter_calibration.json.json",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "10px",
                            },
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ],
            style={
                "height": "100%",
            },
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _sample_download_item(
        self,
        *,
        title: str,
        description: str,
        file_name: str,
    ) -> html.Div:
        """
        Build one sample-download row.
        """
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
                                "opacity": 0.74,
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
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
                    href=f"/assets/{file_name}",
                    download=file_name,
                    style={
                        "flex": "0 0 auto",
                        "textDecoration": "none",
                    },
                ),
            ],
            style={
                "display": "flex",
                "gap": "12px",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": "10px 12px",
                "border": "1px solid rgba(13, 110, 253, 0.14)",
                "borderRadius": "10px",
                "background": "rgba(13, 110, 253, 0.04)",
            },
        )

    def _when_to_use_help_card(self) -> dbc.Card:
        """
        Build the help-scope card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "When to use Help",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "This page is for first-run orientation and diagnosis, not deep technical reference.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                self._numbered_instruction(
                                    index=1,
                                    title="Something behaved unexpectedly",
                                    description=(
                                        "Use Help when a detector list, peak result, fit, warning, "
                                        "or export outcome does not match what you expected."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=2,
                                    title="You already know which page triggered it",
                                    description=(
                                        "Documentation explains what RosettaX is doing under the hood. "
                                        "Help stays focused on working out what to do next."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=3,
                                    title="You want the smallest useful debugging package",
                                    description=(
                                        "Use the troubleshooting and diagnostics sections below to "
                                        "collect only the context needed to understand the issue."
                                    ),
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "10px",
                            },
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ],
            style={
                "height": "100%",
            },
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _before_debugging_card(self) -> dbc.Card:
        """
        Build pre-debug checklist card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Before digging deeper",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Check these first before treating the issue as larger than it is.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                self._checklist_item(
                                    "Confirm the selected detector names before blaming the fit."
                                ),
                                self._checklist_item(
                                    "Look at the most recent plot or table state, not only the final message."
                                ),
                                self._checklist_item(
                                    "If export output looks wrong, inspect the saved calibration JSON and the PDF report together."
                                ),
                                self._checklist_item(
                                    "For batch apply issues, check cross-file detector consistency first."
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "10px",
                            },
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ],
            style={
                "height": "100%",
            },
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )


    def _troubleshooting_card(self) -> dbc.Card:
        """
        Build the troubleshooting card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Troubleshooting",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Common symptoms and where to look first.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    self._troubleshooting_panel(
                                        title="Upload and detector issues",
                                        items=[
                                            (
                                                "No dropdown options after upload",
                                                "Confirm that the file uploaded correctly and that FCS columns are readable.",
                                            ),
                                            (
                                                "Expected detector is missing",
                                                "Check whether the FCS file uses a different channel naming convention.",
                                            ),
                                            (
                                                "Multi file upload warning",
                                                "Verify that all files have matching detector names and structure.",
                                            ),
                                        ],
                                    ),
                                    lg=4,
                                ),
                                dbc.Col(
                                    self._troubleshooting_panel(
                                        title="Peak and table issues",
                                        items=[
                                            (
                                                "Histogram looks empty",
                                                "Check detector selection, log scale, event count, and thresholding.",
                                            ),
                                            (
                                                "Peak detection is poor",
                                                "Adjust peak process settings or use a manual peak selection process.",
                                            ),
                                            (
                                                "Calibration fit looks wrong",
                                                "Verify that the reference values correspond to the correct measured peaks.",
                                            ),
                                        ],
                                    ),
                                    lg=4,
                                ),
                                dbc.Col(
                                    self._troubleshooting_panel(
                                        title="Export and sidebar issues",
                                        items=[
                                            (
                                                "Apply export is incomplete",
                                                "Check the selected calibration, target channel, and extra export columns.",
                                            ),
                                            (
                                                "Sidebar looks stale",
                                                "Refresh the sidebar or verify that the calibration JSON was written to the expected folder.",
                                            ),
                                            (
                                                "Scattering inversion warning",
                                                "Inspect the target Mie relation and the automatically selected monotonic branch.",
                                            ),
                                        ],
                                    ),
                                    lg=4,
                                ),
                            ],
                            className="g-3",
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _troubleshooting_panel(
        self,
        *,
        title: str,
        items: list[tuple[str, str]],
    ) -> dbc.Card:
        """
        Build one troubleshooting subpanel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    title,
                    style={
                        "background": "rgba(13, 110, 253, 0.06)",
                        "borderBottom": "1px solid rgba(13, 110, 253, 0.16)",
                        "padding": "11px 14px",
                        "fontWeight": "700",
                        "borderTopLeftRadius": "10px",
                        "borderTopRightRadius": "10px",
                    },
                ),
                dbc.CardBody(
                    [
                        self._issue_item(
                            title=item_title,
                            description=item_description,
                        )
                        for item_title, item_description in items
                    ],
                    style={
                        "padding": "14px",
                    },
                ),
            ],
            style={
                "height": "100%",
                "borderRadius": "10px",
                "border": "1px solid rgba(13, 110, 253, 0.16)",
                "overflow": "visible",
            },
        )

    def _diagnostics_card(self) -> dbc.Card:
        """
        Build diagnostics collection card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "What to collect when something looks wrong",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "The smallest useful debugging package.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                self._diagnostic_item(
                                    "Page and workflow step",
                                    "The page you were using and the action that triggered the issue.",
                                ),
                                self._diagnostic_item(
                                    "Uploaded file name",
                                    "The FCS file name, or the list of file names for batch export.",
                                ),
                                self._diagnostic_item(
                                    "Selected detector names",
                                    "The detector columns selected in the active workflow.",
                                ),
                                self._diagnostic_item(
                                    "Threshold or peak settings",
                                    "Any threshold, bin count, peak count, or process specific setting involved.",
                                ),
                                self._diagnostic_item(
                                    "Screenshot of the plot",
                                    "A screenshot of the histogram, peak graph, Mie relation, or calibration fit.",
                                ),
                                self._diagnostic_item(
                                    "Calibration JSON",
                                    "The saved calibration payload if the issue appears during apply or export.",
                                ),
                            ],
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))",
                                "gap": "10px",
                                "marginBottom": "14px",
                            },
                        ),
                        dbc.Alert(
                            (
                                "In practice, a screenshot of the relevant plot plus the selected "
                                "detector names is enough to diagnose most UI level calibration issues."
                            ),
                            color="secondary",
                            style={
                                "marginBottom": "0px",
                                "borderRadius": "10px",
                            },
                        ),
                    ],
                    style={
                        "padding": "16px",
                    },
                ),
            ]
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _numbered_instruction(
        self,
        *,
        index: int,
        title: str,
        description: str,
    ) -> html.Div:
        """
        Build one numbered instruction row.
        """
        return html.Div(
            [
                html.Div(
                    str(index),
                    style={
                        "width": "28px",
                        "height": "28px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontSize": "0.82rem",
                        "fontWeight": "800",
                        "backgroundColor": "rgba(13, 110, 253, 0.10)",
                        "border": "1px solid rgba(13, 110, 253, 0.28)",
                        "flex": "0 0 auto",
                    },
                ),
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
                                "fontSize": "0.92rem",
                                "opacity": 0.76,
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
                    },
                ),
            ],
            style={
                "display": "flex",
                "gap": "10px",
                "alignItems": "flex-start",
            },
        )

    def _checklist_item(
        self,
        label: str,
    ) -> html.Div:
        """
        Build one compact checklist item.
        """
        return html.Div(
            [
                html.Div(
                    "✓",
                    style={
                        "width": "22px",
                        "height": "22px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontSize": "0.78rem",
                        "fontWeight": "800",
                        "background": "rgba(25, 135, 84, 0.10)",
                        "border": "1px solid rgba(25, 135, 84, 0.28)",
                        "flex": "0 0 auto",
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.9rem",
                        "opacity": 0.86,
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "9px",
            },
        )

    def _issue_item(
        self,
        *,
        title: str,
        description: str,
    ) -> html.Div:
        """
        Build one troubleshooting issue item.
        """
        return html.Div(
            [
                html.Div(
                    title,
                    style={
                        "fontWeight": "700",
                        "fontSize": "0.92rem",
                        "marginBottom": "3px",
                    },
                ),
                html.Div(
                    description,
                    style={
                        "fontSize": "0.88rem",
                        "opacity": 0.74,
                    },
                ),
            ],
            style={
                "padding": "9px 0px",
                "borderBottom": "1px solid rgba(128, 128, 128, 0.14)",
            },
        )

    def _diagnostic_item(
        self,
        title: str,
        description: str,
    ) -> html.Div:
        """
        Build one diagnostic information box.
        """
        return html.Div(
            [
                html.Div(
                    title,
                    style={
                        "fontWeight": "700",
                        "fontSize": "0.92rem",
                        "marginBottom": "3px",
                    },
                ),
                html.Div(
                    description,
                    style={
                        "fontSize": "0.88rem",
                        "opacity": 0.74,
                    },
                ),
            ],
            style={
                "padding": "10px 12px",
                "border": "1px solid rgba(128, 128, 128, 0.18)",
                "borderRadius": "10px",
                "background": "rgba(128, 128, 128, 0.045)",
            },
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