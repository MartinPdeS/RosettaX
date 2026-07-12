# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.utils.upload_limits import get_max_upload_bytes
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraph
from RosettaX.workflow.plotting.scatter2d import Scatter2DGraphIds

from . import services


logger = logging.getLogger(__name__)


class FilePickerLayout:
    """
    Layout builder for the input FCS file picker section.
    """

    def __init__(
        self,
        *,
        page: Any,
        section_number: int,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color

        self.header_tooltip_target_id = (
            f"{self.page.ids.FilePicker.upload}-section-info-target"
        )

        self.header_tooltip_id = (
            f"{self.page.ids.FilePicker.upload}-section-info-tooltip"
        )

    def build_layout(self) -> dbc.Card:
        """
        Build the file picker layout.
        """
        logger.debug(
            "Building FilePicker layout for page=%s section_number=%r",
            self.page.__class__.__name__,
            self.section_number,
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Upload input FCS",
            tooltip_target_id=self.header_tooltip_target_id,
            tooltip_id=self.header_tooltip_id,
            tooltip_text=(
                "Upload one or more FCS files to apply a saved calibration. "
                "When multiple files are uploaded, RosettaX checks whether "
                "their channel structure is consistent before continuing."
            ),
            subtitle="Select the input cytometry files that will be calibrated.",
            color_name=self.card_color,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_upload_panel(),
                dash.html.Div(
                    style={
                        "height": "14px",
                    },
                ),
                dash.dcc.Loading(
                    self._build_alert(),
                    type="default",
                ),
                dash.html.Div(style={"height": "16px"}),
                self._build_preview_panel(),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_upload_panel(self) -> dash.html.Div:
        """
        Build the upload panel.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        self._build_upload_widget(),
                    ]
                ),
            ]
        )

    def _build_upload_widget(self) -> dash.dcc.Upload:
        """
        Build the Dash upload widget.
        """
        return dash.dcc.Upload(
            id=self.page.ids.FilePicker.upload,
            children=dash.html.Div(
                dash.html.A(
                    "select one or more .fcs files",
                    style={
                        "fontWeight": "650",
                        "textDecoration": "none",
                    },
                )
            ),
            multiple=True,
            style=styling.UPLOAD,
            max_size=get_max_upload_bytes(),
        )

    def _build_alert(self) -> dbc.Alert:
        """
        Build the upload status alert.
        """
        return dbc.Alert(
            services.build_upload_prompt_text(),
            id=self.page.ids.FilePicker.column_consistency_alert,
            color="secondary",
            is_open=True,
            style={
                "marginBottom": "0px",
                "borderRadius": "10px",
            },
        )

    def _build_preview_panel(self) -> dbc.Card:
        """Build the uploaded FCS histogram preview panel."""
        defaults = services.resolve_preview_control_defaults()

        return dbc.Card(
            dbc.CardBody(
                [
                    dash.html.Div(
                        [
                            dash.html.Div(
                                [
                                    dash.html.H5(
                                        "Preview uploaded data",
                                        style={"marginBottom": "4px"},
                                    ),
                                    dash.html.Div(
                                        "Choose an uploaded file and one of the calibration-affected source channels to preview the calibrated values.",
                                        style={"fontSize": "0.88rem", "opacity": 0.76},
                                    ),
                                ]
                            ),
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        [
                                            dash.html.Label("File", style={"fontWeight": "650"}),
                                            ui_forms.persistent_dropdown(
                                                id=self.page.ids.FilePicker.preview_file,
                                                options=[],
                                                value=None,
                                                clearable=False,
                                                placeholder="Upload an FCS file",
                                            ),
                                        ],
                                        style={"minWidth": "260px", "flex": "1 1 320px"},
                                    ),
                                    dash.html.Div(
                                        [
                                            dash.html.Label("Channel", style={"fontWeight": "650"}),
                                            ui_forms.persistent_dropdown(
                                                id=self.page.ids.FilePicker.preview_channel,
                                                options=[],
                                                value=None,
                                                clearable=False,
                                                placeholder="Select an affected channel",
                                            ),
                                        ],
                                        style={"minWidth": "240px", "flex": "1 1 280px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "14px",
                                    "flexWrap": "wrap",
                                    "alignItems": "end",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "14px",
                        },
                    ),
                    dash.html.Div(
                        id=self.page.ids.FilePicker.preview_status,
                        children="Upload an FCS file to preview its histogram.",
                        style={
                            "minHeight": "22px",
                            "marginTop": "12px",
                            "fontSize": "0.88rem",
                            "opacity": 0.78,
                        },
                    ),
                    dash.dcc.Loading(
                        Scatter2DGraph.build_component(
                            component_ids=Scatter2DGraphIds(
                                graph=self.page.ids.FilePicker.preview_graph,
                                axis_scale_toggle=self.page.ids.FilePicker.preview_axis_scale_toggle,
                            ),
                            figure=services.build_empty_preview_figure(
                                "Upload an FCS file to preview its histogram."
                            ),
                            x_log_enabled=bool(defaults["x_log_values"]),
                            y_log_enabled=bool(defaults["y_log_values"]),
                            graph_style={
                                "height": defaults["graph_height"],
                                "width": "100%",
                            },
                            bottom_controls=[
                                self._build_preview_visibility_control(
                                    input_id=self.page.ids.FilePicker.preview_graph_visibility_toggle,
                                ),
                                self._build_number_of_bins_control(
                                    input_id=self.page.ids.FilePicker.preview_nbins_input,
                                    value=defaults["n_bins_for_plots"],
                                ),
                                self._build_event_count_control(
                                    input_id=self.page.ids.FilePicker.preview_event_count_input,
                                    value="0",
                                ),
                            ],
                        ),
                        type="default",
                    ),
                ],
                style=ui_forms.build_workflow_panel_body_style(),
            ),
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_number_of_bins_control(self, *, input_id: str, value: int) -> dash.html.Div:
        """Build the histogram bin count control."""
        return dash.html.Div(
            [
                dbc.Label(
                    "Bins",
                    html_for=input_id,
                    style={
                        "marginBottom": "0px",
                        "fontSize": "0.85rem",
                    },
                ),
                dbc.Input(
                    id=input_id,
                    type="text",
                    inputMode="numeric",
                    value=str(value),
                    debounce=True,
                    size="sm",
                    style={
                        "width": "110px",
                    },
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
            },
        )

    def _build_preview_visibility_control(self, *, input_id: str) -> dash.html.Div:
        """Build the show/hide preview toggle."""
        return dash.html.Div(
            dbc.Checklist(
                id=input_id,
                options=[
                    {
                        "label": "Show plot",
                        "value": "enabled",
                    }
                ],
                value=["enabled"],
                inline=True,
                switch=True,
                persistence=True,
                persistence_type="session",
                style={
                    "display": "block",
                    "width": "fit-content",
                },
            ),
            style={
                "display": "flex",
                "alignItems": "center",
            },
        )

    def _build_event_count_control(self, *, input_id: str, value: str) -> dash.html.Div:
        """Build the read-only total event count control."""
        return dash.html.Div(
            [
                dbc.Label(
                    "Events used",
                    html_for=input_id,
                    style={
                        "marginBottom": "0px",
                        "fontSize": "0.85rem",
                    },
                ),
                dbc.Input(
                    id=input_id,
                    type="text",
                    value=str(value),
                    readonly=True,
                    size="sm",
                    style={
                        "width": "130px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
            },
        )
