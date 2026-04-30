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
    - Explain the three main RosettaX workflows.
    - Provide quick entry points to workflow pages.
    - Keep workflow guidance and troubleshooting separate from the home page.
    - Present diagnostics information for debugging calibration issues.
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
                self._quick_start_row(),
                html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._workflow_help_row(),
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
                                "RosettaX is organized around three workflows: "
                                "building fluorescence calibrations, building scattering "
                                "calibrations, and applying saved calibrations to FCS files."
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

    def _quick_start_row(self) -> dbc.Row:
        """
        Build quick start and navigation cards.
        """
        return dbc.Row(
            [
                dbc.Col(
                    self._quick_start_card(),
                    lg=8,
                ),
                dbc.Col(
                    self._where_to_go_card(),
                    lg=4,
                ),
            ],
            className="g-3",
        )

    def _quick_start_card(self) -> dbc.Card:
        """
        Build the quick start card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Quick start",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "The shortest path through the application.",
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
                                    title="Choose the workflow",
                                    description=(
                                        "Open Fluorescence or Scattering when building a new "
                                        "calibration. Open Apply calibration when reusing an "
                                        "existing calibration."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=2,
                                    title="Upload the FCS file",
                                    description=(
                                        "Use the calibration bead file for calibration workflows, "
                                        "or one or more experimental files for the apply workflow."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=3,
                                    title="Inspect intermediate outputs",
                                    description=(
                                        "Check detector selections, peak positions, model parameters, "
                                        "tables, and preview graphs before fitting or exporting."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=4,
                                    title="Fit and save",
                                    description=(
                                        "Create the calibration, inspect the fit, then save the JSON "
                                        "payload for reuse."
                                    ),
                                ),
                                self._numbered_instruction(
                                    index=5,
                                    title="Apply and export",
                                    description=(
                                        "Select a saved calibration and export calibrated FCS files."
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

    def _where_to_go_card(self) -> dbc.Card:
        """
        Build direct navigation card.
        """
        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            "Go directly to",
                            style={
                                "fontWeight": "750",
                                "fontSize": "1.02rem",
                            },
                        ),
                        html.Div(
                            "Open a workflow page.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        self._navigation_button(
                            label="Fluorescence",
                            href="/fluorescence",
                            color="primary",
                            button_id=self._id("fluorescence-link"),
                        ),
                        self._navigation_button(
                            label="Scattering",
                            href="/scattering",
                            color="primary",
                            button_id=self._id("scattering-link"),
                            outline=True,
                        ),
                        self._navigation_button(
                            label="Apply calibration",
                            href="/calibrate",
                            color="success",
                            button_id=self._id("apply-link"),
                            outline=True,
                        ),
                        self._navigation_button(
                            label="Settings",
                            href="/settings",
                            color="secondary",
                            button_id=self._id("settings-link"),
                            outline=True,
                            margin_bottom=False,
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

    def _workflow_help_row(self) -> dbc.Row:
        """
        Build workflow specific help cards.
        """
        return dbc.Row(
            [
                dbc.Col(
                    self._workflow_help_card(
                        title="Fluorescence calibration",
                        subtitle="MESF based fluorescence calibration.",
                        description=(
                            "Use this workflow when the bead populations have known "
                            "fluorescence reference values."
                        ),
                        items=[
                            "Upload the fluorescence bead FCS file.",
                            "Select the detector channel used by the peak process.",
                            "Detect or manually select bead population peaks.",
                            "Review the MESF reference table.",
                            "Create the fluorescence calibration and inspect the fit.",
                            "Save the calibration JSON for reuse.",
                        ],
                        alert_text=(
                            "If the fluorescence histogram looks messy, first verify "
                            "the selected detector channel and the retained peak positions."
                        ),
                        alert_color="info",
                    ),
                    lg=4,
                ),
                dbc.Col(
                    self._workflow_help_card(
                        title="Scattering calibration",
                        subtitle="Mie based scattering calibration.",
                        description=(
                            "Use this workflow when measured bead peak positions need "
                            "to be linked to modeled scattering coupling."
                        ),
                        items=[
                            "Upload the scattering calibration FCS file.",
                            "Select the scattering detector or detector pair.",
                            "Configure the optical and particle model.",
                            "Fill or compute the calibration standard table.",
                            "Fit the instrument response.",
                            "Save the scattering calibration JSON.",
                        ],
                        alert_text=(
                            "If the fit is unstable, check the detector selection, the "
                            "particle model, and the standard table before changing the fit."
                        ),
                        alert_color="warning",
                    ),
                    lg=4,
                ),
                dbc.Col(
                    self._workflow_help_card(
                        title="Apply saved calibration",
                        subtitle="Batch export calibrated FCS files.",
                        description=(
                            "Use this workflow when a calibration JSON already exists "
                            "and should be applied to experimental files."
                        ),
                        items=[
                            "Upload one or more input FCS files.",
                            "Select a saved fluorescence or scattering calibration.",
                            "For scattering, configure the target particle model.",
                            "Choose extra raw channels to export unchanged.",
                            "Run the apply and export step.",
                            "Download the calibrated output files.",
                        ],
                        alert_text=(
                            "For multi file export, uploaded files should have compatible "
                            "detector names and a consistent FCS structure."
                        ),
                        alert_color="info",
                    ),
                    lg=4,
                ),
            ],
            className="g-3",
        )

    def _workflow_help_card(
        self,
        *,
        title: str,
        subtitle: str,
        description: str,
        items: list[str],
        alert_text: str,
        alert_color: str,
    ) -> dbc.Card:
        """
        Build a workflow help card.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Div(
                            title,
                            style={
                                "fontWeight": "760",
                                "fontSize": "1rem",
                            },
                        ),
                        html.Div(
                            subtitle,
                            style={
                                "fontSize": "0.84rem",
                                "opacity": 0.72,
                                "marginTop": "3px",
                            },
                        ),
                    ],
                    style={
                        "background": "rgba(13, 110, 253, 0.06)",
                        "borderBottom": "1px solid rgba(13, 110, 253, 0.16)",
                        "padding": "12px 16px",
                        "borderTopLeftRadius": "12px",
                        "borderTopRightRadius": "12px",
                    },
                ),
                dbc.CardBody(
                    [
                        html.P(
                            description,
                            style={
                                "opacity": 0.82,
                                "marginBottom": "14px",
                            },
                        ),
                        html.Div(
                            [
                                self._checklist_item(
                                    item,
                                )
                                for item in items
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "8px",
                                "marginBottom": "14px",
                            },
                        ),
                        dbc.Alert(
                            alert_text,
                            color=alert_color,
                            style={
                                "marginBottom": "0px",
                                "borderRadius": "10px",
                                "fontSize": "0.9rem",
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
                "borderRadius": "12px",
                "border": "1px solid rgba(13, 110, 253, 0.16)",
                "boxShadow": "0 0.25rem 0.65rem rgba(0, 0, 0, 0.06)",
                "overflow": "visible",
            },
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

    def _navigation_button(
        self,
        *,
        label: str,
        href: str,
        color: str,
        button_id: str,
        outline: bool = False,
        margin_bottom: bool = True,
    ) -> dbc.Button:
        """
        Build one full width navigation button.
        """
        return dbc.Button(
            label,
            href=href,
            id=button_id,
            color=color,
            outline=outline,
            style={
                "width": "100%",
                "marginBottom": "10px" if margin_bottom else "0px",
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