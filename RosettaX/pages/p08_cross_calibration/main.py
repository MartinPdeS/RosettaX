# -*- coding: utf-8 -*-

import json
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.calibration_cards import make_profile_aware_collapsible_card
from RosettaX.workflow.cross_calibration import services

from .ids import Ids


class CrossCalibrationPage:
    """
    Cross-calibration workflow page.
    """

    def __init__(self) -> None:
        self.ids = Ids()
        self.style = styling.PAGE

    def layout(self) -> dbc.Container:
        return dbc.Container(
            [
                dcc.Store(
                    id=self.ids.primary_summary_store,
                    data=None,
                    storage_type="session",
                ),
                dcc.Store(
                    id=self.ids.secondary_summary_store,
                    data=None,
                    storage_type="session",
                ),
                dcc.Store(
                    id=self.ids.result_store,
                    data=None,
                    storage_type="session",
                ),
                dcc.Download(
                    id=self.ids.export_download,
                ),
                html.Div(
                    [
                        self._build_header_card(),
                        make_profile_aware_collapsible_card(
                            self._build_upload_card(),
                            page_name=self.ids.page_prefix,
                            section_key="1",
                        ),
                        make_profile_aware_collapsible_card(
                            self._build_result_card(),
                            page_name=self.ids.page_prefix,
                            section_key="2",
                        ),
                        make_profile_aware_collapsible_card(
                            self._build_export_card(),
                            page_name=self.ids.page_prefix,
                            section_key="3",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "18px",
                    },
                ),
            ],
            fluid=True,
            style={
                **self.style,
                "paddingLeft": "0px",
                "paddingRight": "0px",
                "paddingBottom": "48px",
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Cross calibration",
                        title_component="H2",
                        description=(
                            "Create a transfer calibration from a primary reference bead set "
                            "used less often to a cheaper routine bead set measured more often."
                        ),
                    ),
                    dbc.Alert(
                        "Experimental workflow: this page is still under active development and may change as the transfer-calibration workflow matures.",
                        color="warning",
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                self._build_step_card(
                                    number=step["number"],
                                    title=step["title"],
                                    description=step["description"],
                                    color_name=step["color_name"],
                                ),
                                xs=12,
                                md=6,
                                xl=True,
                                style={"marginBottom": "10px"},
                            )
                            for step in self._build_header_steps()
                        ],
                        className="g-2",
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

    def _build_header_steps(self) -> list[dict[str, str]]:
        return [
            {
                "number": "1",
                "title": "Load primary calibration",
                "description": (
                    "Upload the high-confidence calibration built from the expensive bead set. "
                    "This defines the primary calibrated scale you want to preserve over time."
                ),
                "color_name": styling.get_workflow_section_color(1),
            },
            {
                "number": "2",
                "title": "Load routine-bead calibration",
                "description": (
                    "Upload the cheaper secondary bead calibration measured more often on the same detector."
                ),
                "color_name": styling.get_workflow_section_color(2),
            },
            {
                "number": "3",
                "title": "Build transfer relation",
                "description": (
                    "Fit the routine bead peaks onto the primary calibrated scale so the secondary bead set can act as a weekly bridge."
                ),
                "color_name": styling.get_workflow_section_color(3),
            },
        ]

    def _build_step_card(
        self,
        *,
        number: str,
        title: str,
        description: str,
        color_name: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        number,
                        style={
                            "width": "28px",
                            "height": "28px",
                            "borderRadius": "50%",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "fontWeight": "700",
                            "fontSize": "0.9rem",
                            "backgroundColor": styling.build_rgba(color_name, 0.12),
                            "border": f"1px solid {styling.build_rgba(color_name, 0.35)}",
                            "marginBottom": "10px",
                        },
                    ),
                    html.H6(
                        title,
                        style={"marginBottom": "6px"},
                    ),
                    html.P(
                        description,
                        style={
                            "marginBottom": "0px",
                            "fontSize": "0.86rem",
                            "opacity": 0.78,
                        },
                    ),
                ],
                style={
                    "height": "100%",
                    "padding": "14px",
                },
            ),
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=color_name,
                style_overrides={"height": "100%"},
            ),
        )

    def _build_upload_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    "1. Load primary and secondary calibrations",
                    style=ui_forms.build_workflow_section_header_style(
                        color_name=styling.get_workflow_section_color(1),
                    ),
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    self._build_upload_panel(
                                        title="Primary reference calibration",
                                        upload_id=self.ids.primary_upload,
                                        feedback_id=self.ids.primary_feedback,
                                        summary_id=self.ids.primary_summary,
                                        button_text=services.build_upload_prompt_text(
                                            "primary reference",
                                        ),
                                        empty_summary_text="No primary calibration loaded.",
                                    ),
                                    xs=12,
                                    lg=6,
                                ),
                                dbc.Col(
                                    self._build_upload_panel(
                                        title="Secondary routine-bead calibration",
                                        upload_id=self.ids.secondary_upload,
                                        feedback_id=self.ids.secondary_feedback,
                                        summary_id=self.ids.secondary_summary,
                                        button_text=services.build_upload_prompt_text(
                                            "secondary routine-bead",
                                        ),
                                        empty_summary_text="No secondary calibration loaded.",
                                    ),
                                    xs=12,
                                    lg=6,
                                ),
                            ],
                            className="g-3",
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Create transfer calibration",
                                    id=self.ids.build_button,
                                    n_clicks=0,
                                    color="primary",
                                ),
                                html.Div(
                                    id=self.ids.status,
                                    style={
                                        "minHeight": "24px",
                                        "display": "flex",
                                        "alignItems": "center",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "14px",
                                "alignItems": "center",
                                "marginTop": "16px",
                                "flexWrap": "wrap",
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_section_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=styling.get_workflow_section_color(1),
            ),
        )

    def _build_upload_panel(
        self,
        *,
        title: str,
        upload_id: str,
        feedback_id: str,
        summary_id: str,
        button_text: str,
        empty_summary_text: str,
    ) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        title,
                        style={"marginBottom": "10px"},
                    ),
                    dcc.Upload(
                        id=upload_id,
                        children=html.Div(button_text),
                        style=styling.UPLOAD,
                        multiple=False,
                    ),
                    html.Div(
                        "No file loaded.",
                        id=feedback_id,
                        style={
                            "marginTop": styling.get_spacing_token("sm"),
                            "opacity": 0.76,
                        },
                    ),
                    html.Hr(),
                    html.Div(
                        [
                            html.Strong("Summary"),
                            html.Div(
                                self._build_summary_children([empty_summary_text]),
                                id=summary_id,
                                style={
                                    "marginTop": "8px",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "4px",
                                    "opacity": 0.86,
                                },
                            ),
                        ]
                    ),
                ]
            ),
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=styling.get_workflow_section_color(1),
            ),
        )

    def _build_summary_children(
        self,
        summary_rows: list[Any],
    ) -> list[Any]:
        if not summary_rows:
            return []

        first_row = summary_rows[0]

        if isinstance(first_row, str):
            return [html.Div(str(first_row))]

        children: list[Any] = []

        for row in summary_rows:
            if not isinstance(row, dict):
                continue

            children.append(
                html.Div(
                    [
                        html.Span(
                            f"{row.get('label')}:",
                            style={
                                "fontWeight": "600",
                                "minWidth": "120px",
                                "display": "inline-block",
                            },
                        ),
                        html.Span(str(row.get("value") or "n/a")),
                    ],
                    style={
                        "display": "flex",
                        "gap": "12px",
                        "alignItems": "flex-start",
                    },
                )
            )

        return children

    def _build_result_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    "2. Review transfer relation",
                    style=ui_forms.build_workflow_section_header_style(
                        color_name=styling.get_workflow_section_color(2),
                    ),
                ),
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id=self.ids.graph,
                            figure=services.build_empty_result_figure(
                                message="Upload a primary and a secondary calibration to build a transfer relation.",
                            ),
                            config=styling.PLOTLY_GRAPH_CONFIG,
                            style=services.resolve_graph_style(),
                        ),
                        dash_table.DataTable(
                            id=self.ids.table,
                            columns=[
                                {"name": "Bead", "id": "Bead"},
                                {"name": "Secondary peak", "id": "Secondary peak"},
                                {"name": "Primary calibrated value", "id": "Primary calibrated value"},
                                {"name": "Primary peak", "id": "Primary peak"},
                            ],
                            data=[],
                            page_size=8,
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "8px"},
                            style_header={"fontWeight": "700"},
                        ),
                    ],
                    style=ui_forms.build_workflow_section_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=styling.get_workflow_section_color(2),
            ),
        )

    def _build_export_card(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader(
                    "3. Export transfer relation",
                    style=ui_forms.build_workflow_section_header_style(
                        color_name=styling.get_workflow_section_color(3),
                    ),
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            "Provide a file name to export the generated transfer calibration JSON.",
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                dcc.Input(
                                    id=self.ids.export_name,
                                    type="text",
                                    value=services.DEFAULT_EXPORT_FILE_NAME,
                                    placeholder="cross_calibration",
                                    style={"width": "280px"},
                                ),
                                dbc.Button(
                                    "Download transfer calibration JSON",
                                    id=self.ids.export_button,
                                    n_clicks=0,
                                    color="secondary",
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "12px",
                                "alignItems": "center",
                                "flexWrap": "wrap",
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_section_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=styling.get_workflow_section_color(3),
            ),
        )

    def register_callbacks(self) -> "CrossCalibrationPage":
        @dash.callback(
            dash.Output(self.ids.primary_summary_store, "data"),
            dash.Output(self.ids.primary_feedback, "children"),
            dash.Output(self.ids.primary_summary, "children"),
            dash.Input(self.ids.primary_upload, "contents"),
            dash.State(self.ids.primary_upload, "filename"),
            prevent_initial_call=True,
        )
        def upload_primary_calibration(
            contents: Any,
            filename: Any,
        ) -> tuple[Any, str, list[Any]]:
            if not contents:
                return dash.no_update, "No file loaded.", ["No primary calibration loaded."]

            try:
                resolved_filename, payload = services.parse_uploaded_calibration(
                    contents=contents,
                    filename=filename,
                )
                summary = services.build_calibration_summary(
                    filename=resolved_filename,
                    calibration_payload=payload,
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    f"{type(exception).__name__}: {exception}",
                    self._build_summary_children(["No primary calibration loaded."]),
                )

            return (
                summary,
                f"Loaded file: {resolved_filename}",
                self._build_summary_children(
                    services.build_calibration_summary_children(
                        summary,
                        empty_message="No primary calibration loaded.",
                    )
                ),
            )

        @dash.callback(
            dash.Output(self.ids.secondary_summary_store, "data"),
            dash.Output(self.ids.secondary_feedback, "children"),
            dash.Output(self.ids.secondary_summary, "children"),
            dash.Input(self.ids.secondary_upload, "contents"),
            dash.State(self.ids.secondary_upload, "filename"),
            prevent_initial_call=True,
        )
        def upload_secondary_calibration(
            contents: Any,
            filename: Any,
        ) -> tuple[Any, str, list[Any]]:
            if not contents:
                return dash.no_update, "No file loaded.", ["No secondary calibration loaded."]

            try:
                resolved_filename, payload = services.parse_uploaded_calibration(
                    contents=contents,
                    filename=filename,
                )
                summary = services.build_calibration_summary(
                    filename=resolved_filename,
                    calibration_payload=payload,
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    f"{type(exception).__name__}: {exception}",
                    self._build_summary_children(["No secondary calibration loaded."]),
                )

            return (
                summary,
                f"Loaded file: {resolved_filename}",
                self._build_summary_children(
                    services.build_calibration_summary_children(
                        summary,
                        empty_message="No secondary calibration loaded.",
                    )
                ),
            )

        @dash.callback(
            dash.Output(self.ids.result_store, "data"),
            dash.Output(self.ids.status, "children"),
            dash.Output(self.ids.graph, "figure"),
            dash.Output(self.ids.table, "data"),
            dash.Input(self.ids.build_button, "n_clicks"),
            dash.State(self.ids.primary_summary_store, "data"),
            dash.State(self.ids.secondary_summary_store, "data"),
            dash.State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def build_cross_calibration(
            n_clicks: Any,
            primary_summary: Any,
            secondary_summary: Any,
            runtime_config_data: Any,
        ) -> tuple[Any, str, Any, list[dict[str, Any]]]:
            if not n_clicks:
                return (
                    dash.no_update,
                    "No transfer calibration generated yet.",
                    services.build_empty_result_figure(
                        message="Upload a primary and a secondary calibration to build a transfer relation.",
                        runtime_config_data=runtime_config_data,
                    ),
                    [],
                )

            if not isinstance(primary_summary, dict) or not isinstance(secondary_summary, dict):
                empty_figure = services.build_empty_result_figure(
                    message="Load a primary and a secondary calibration first.",
                    runtime_config_data=runtime_config_data,
                )
                return (
                    dash.no_update,
                    "Load a primary and a secondary calibration first.",
                    empty_figure,
                    [],
                )

            try:
                result = services.build_cross_calibration_result(
                    primary_summary=primary_summary,
                    secondary_summary=secondary_summary,
                )
                result_dict = result.to_dict()
            except Exception as exception:
                empty_figure = services.build_empty_result_figure(
                    message=f"Failed to build transfer calibration: {type(exception).__name__}: {exception}",
                    runtime_config_data=runtime_config_data,
                )
                return (
                    dash.no_update,
                    f"Failed to build transfer calibration: {type(exception).__name__}: {exception}",
                    empty_figure,
                    [],
                )

            return (
                result_dict,
                services.build_result_status_text(result_dict),
                services.build_result_figure(
                    result_dict,
                    runtime_config_data=runtime_config_data,
                ),
                services.build_result_table_data(result_dict),
            )

        @dash.callback(
            dash.Output(self.ids.graph, "style"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_graph_style(
            runtime_config_data: Any,
        ) -> dict[str, Any]:
            return services.resolve_graph_style(runtime_config_data)

        @dash.callback(
            dash.Output(self.ids.graph, "figure", allow_duplicate=True),
            dash.Input("runtime-config-store", "data"),
            dash.State(self.ids.result_store, "data"),
            prevent_initial_call=True,
        )
        def sync_graph_figure_style_from_profile(
            runtime_config_data: Any,
            result: Any,
        ) -> Any:
            if isinstance(result, dict):
                return services.build_result_figure(
                    result,
                    runtime_config_data=runtime_config_data,
                )

            return services.build_empty_result_figure(
                message="Upload a primary and a secondary calibration to build a transfer relation.",
                runtime_config_data=runtime_config_data,
            )

        @dash.callback(
            dash.Output(self.ids.export_button, "disabled"),
            dash.Input(self.ids.result_store, "data"),
            dash.Input(self.ids.export_name, "value"),
            prevent_initial_call=False,
        )
        def toggle_export_button(
            result: Any,
            export_name: Any,
        ) -> bool:
            return not isinstance(result, dict) or not bool(str(export_name or "").strip())

        @dash.callback(
            dash.Output(self.ids.export_download, "data"),
            dash.Input(self.ids.export_button, "n_clicks"),
            dash.State(self.ids.result_store, "data"),
            dash.State(self.ids.export_name, "value"),
            prevent_initial_call=True,
        )
        def download_cross_calibration(
            n_clicks: Any,
            result: Any,
            export_name: Any,
        ) -> Any:
            if not n_clicks or not isinstance(result, dict):
                return dash.no_update

            payload = services.build_export_payload(
                result=result,
                export_name=str(export_name or services.DEFAULT_EXPORT_FILE_NAME),
            )

            return dcc.send_string(
                json.dumps(payload, indent=2),
                services.build_export_filename(export_name),
            )

        return self


_page = CrossCalibrationPage().register_callbacks()
layout = _page.layout


dash.register_page(
    __name__,
    path="/cross-calibration",
    name="Cross Calibration",
    order=3,
    layout=layout,
)
