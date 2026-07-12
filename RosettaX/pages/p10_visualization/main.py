# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.calibration_cards import make_profile_aware_collapsible_card
from RosettaX.workflow.upload import services as upload_services

from .ids import Ids
from . import services


class VisualizationPage:
    """
    Floreada-style FCS visualization page.
    """

    def __init__(self) -> None:
        self.ids = Ids()

    def layout(self) -> html.Div:
        default_controls = services.resolve_visualization_control_defaults()

        return html.Div(
            [
                dcc.Store(
                    id=self.ids.file_store,
                    data=None,
                    storage_type="session",
                ),
                self._build_header_card(),
                self._build_section_card(
                    section_number=1,
                    title="Upload visualization FCS file",
                    subtitle="Load one FCS file to inspect its channels, metadata, and event distributions.",
                    tooltip_text=(
                        "Upload one FCS file that you want to inspect. "
                        "The visualization page reads the file metadata and exposes "
                        "its channels for histogram or 2D scatter plotting."
                    ),
                    body_children=[
                        dcc.Upload(
                            id=self.ids.upload,
                            children=html.Div("Select FCS file"),
                            style=styling.UPLOAD,
                            multiple=False,
                        ),
                        html.Div(
                            "No file loaded.",
                            id=self.ids.upload_feedback,
                            style={
                                "marginTop": styling.get_spacing_token("sm"),
                                "opacity": 0.76,
                            },
                        ),
                    ],
                ),
                self._build_section_card(
                    section_number=2,
                    title="Configure plot",
                    subtitle="Choose the plot type, channels, scales, and sampling limits before rendering the graph.",
                    tooltip_text=(
                        "Configure how RosettaX draws the plot. "
                        "Histogram mode uses one channel, while 2D scatter mode adds a Y "
                        "channel and density-based coloring controls."
                    ),
                    body_children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("Plot type"),
                                        dcc.Dropdown(
                                            id=self.ids.plot_type,
                                            options=[
                                                {"label": "1D histogram", "value": services.PLOT_TYPE_HISTOGRAM},
                                                {"label": "2D scatter", "value": services.PLOT_TYPE_SCATTER},
                                            ],
                                            value=services.PLOT_TYPE_HISTOGRAM,
                                            clearable=False,
                                        ),
                                    ],
                                    style={"minWidth": "220px", "flex": "1"},
                                ),
                                html.Div(
                                    [
                                        html.Label("X channel"),
                                        dcc.Dropdown(
                                            id=self.ids.x_channel,
                                            options=[],
                                            value=None,
                                            clearable=False,
                                            placeholder="Select X channel",
                                        ),
                                    ],
                                    style={"minWidth": "260px", "flex": "1"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Y channel"),
                                        dcc.Dropdown(
                                            id=self.ids.y_channel,
                                            options=[],
                                            value=None,
                                            clearable=False,
                                            placeholder="Select Y channel",
                                        ),
                                    ],
                                    id=self.ids.y_channel_container,
                                    style={"minWidth": "260px", "flex": "1"},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": styling.get_spacing_token("md"),
                                "flexWrap": "wrap",
                            },
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Checklist(
                                        id=self.ids.x_log,
                                        options=[{"label": "Log X", "value": "enabled"}],
                                        value=default_controls["x_log_values"],
                                        inline=True,
                                        switch=True,
                                        persistence=True,
                                        persistence_type="session",
                                        style={
                                            "display": "block",
                                            "width": "fit-content",
                                        },
                                    ),
                                    dbc.Checklist(
                                        id=self.ids.y_log,
                                        options=[{"label": "Log Y", "value": "enabled"}],
                                        value=default_controls["y_log_values"],
                                        inline=True,
                                        switch=True,
                                        persistence=True,
                                        persistence_type="session",
                                        style={
                                            "display": "block",
                                            "width": "fit-content",
                                        },
                                    ),
                                    dbc.Checklist(
                                        id=self.ids.colormap_log,
                                        options=[{"label": "Log colormap", "value": "enabled"}],
                                        value=default_controls["colormap_log_values"],
                                        inline=True,
                                        switch=True,
                                        persistence=True,
                                        persistence_type="session",
                                        style={
                                            "display": "block",
                                            "width": "fit-content",
                                        },
                                    ),
                                ],
                                style={
                                    "padding": "8px 10px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "16px",
                                    "flexWrap": "wrap",
                                },
                            ),
                            id=self.ids.axis_toggle_container,
                            style={
                                **ui_forms.build_compact_control_panel_style(),
                                "display": "inline-block",
                                "marginTop": styling.get_spacing_token("md"),
                                "opacity": 0.95,
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label(
                                            "Max events",
                                            style={
                                                "display": "block",
                                                "marginBottom": styling.get_spacing_token("xs"),
                                            },
                                        ),
                                        dcc.Input(
                                            id=self.ids.max_events,
                                            type="number",
                                            value=default_controls["max_events"],
                                            min=0,
                                            step=1000,
                                            style={
                                                "width": "160px",
                                                "color": "inherit",
                                            },
                                        ),
                                    ],
                                    style={"minWidth": "180px"},
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            "Marker size",
                                            style={
                                                "display": "block",
                                                "marginBottom": styling.get_spacing_token("xs"),
                                            },
                                        ),
                                        dcc.Input(
                                            id=self.ids.marker_size,
                                            type="number",
                                            value=default_controls["marker_size"],
                                            min=1,
                                            max=24,
                                            step=1,
                                            style={"width": "160px"},
                                        ),
                                    ],
                                    id=self.ids.marker_size_container,
                                    style={"minWidth": "180px"},
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            "Marker opacity",
                                            style={
                                                "display": "block",
                                                "marginBottom": styling.get_spacing_token("xs"),
                                            },
                                        ),
                                        dcc.Input(
                                            id=self.ids.marker_opacity,
                                            type="number",
                                            value=default_controls["marker_opacity"],
                                            min=0.05,
                                            max=1.0,
                                            step=0.05,
                                            style={"width": "160px"},
                                        ),
                                    ],
                                    id=self.ids.marker_opacity_container,
                                    style={"minWidth": "180px"},
                                ),
                            ],
                            id=self.ids.scatter_controls_container,
                            style={
                                "display": "flex",
                                "alignItems": "flex-start",
                                "gap": styling.get_spacing_token("md"),
                                "marginTop": styling.get_spacing_token("md"),
                                "flexWrap": "wrap",
                            },
                        ),
                    ],
                ),
                self._build_section_card(
                    section_number=3,
                    title="Inspect metadata and plot",
                    subtitle="Review the loaded file summary and interact with the rendered graph.",
                    tooltip_text=(
                        "RosettaX summarizes the uploaded file alongside the active plot "
                        "so you can verify the file context while exploring channels and scales."
                    ),
                    body_children=[
                        html.Div(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "File summary",
                                            style=ui_forms.build_workflow_subpanel_header_style(
                                                color_name=styling.get_workflow_section_color(3),
                                            ),
                                        ),
                                        dbc.CardBody(
                                            html.Div(
                                                id=self.ids.metadata,
                                            ),
                                            style=ui_forms.build_workflow_panel_body_style(),
                                        ),
                                    ],
                                    style={
                                        **ui_forms.build_workflow_subpanel_card_style(
                                            color_name=styling.get_workflow_section_color(3),
                                        ),
                                        "flex": "0 0 320px",
                                    },
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Visualization",
                                            style=ui_forms.build_workflow_subpanel_header_style(
                                                color_name=styling.get_workflow_section_color(3),
                                            ),
                                        ),
                                        dbc.CardBody(
                                            [
                                                html.Div(
                                                    id=self.ids.plot_status,
                                                    style={
                                                        "marginBottom": styling.get_spacing_token("sm"),
                                                        "opacity": 0.8,
                                                    },
                                                ),
                                                dcc.Graph(
                                                    id=self.ids.graph,
                                                    figure=services.build_empty_figure(
                                                        message="Upload an FCS file to start visualizing events.",
                                                        runtime_config_data=None,
                                                    ),
                                                    config=styling.PLOTLY_GRAPH_CONFIG,
                                                    style=default_controls["graph_style"],
                                                ),
                                            ],
                                            style=ui_forms.build_workflow_panel_body_style(),
                                        ),
                                    ],
                                    style={
                                        **ui_forms.build_workflow_subpanel_card_style(
                                            color_name=styling.get_workflow_section_color(3),
                                        ),
                                        "flex": "1 1 auto",
                                        "minWidth": 0,
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": styling.get_spacing_token("lg"),
                                "alignItems": "stretch",
                                "flexWrap": "wrap",
                            },
                        ),
                    ],
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("lg"),
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    ui_forms.build_section_intro(
                        title="Visualization",
                        title_component="H2",
                        description=(
                            "Upload one FCS file and inspect it with a 1D histogram or a 2D scatter colored by local event density."
                        ),
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
                                lg=4,
                                style={"marginBottom": "10px"},
                            )
                            for step in self._build_steps()
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

    def _build_section_card(
        self,
        *,
        section_number: int,
        title: str,
        subtitle: str,
        tooltip_text: str,
        body_children: list[Any],
    ) -> dbc.Card:
        color_name = styling.get_workflow_section_color(section_number)
        section_key = title.lower().replace(" ", "-")

        card = dbc.Card(
            [
                ui_forms.build_card_header_with_info(
                    title=f"{section_number}. {title}",
                    tooltip_target_id=f"{self.ids.page_prefix}-{section_key}-info-target",
                    tooltip_id=f"{self.ids.page_prefix}-{section_key}-info-tooltip",
                    tooltip_text=tooltip_text,
                    subtitle=subtitle,
                    color_name=color_name,
                ),
                dbc.CardBody(
                    body_children,
                    style=ui_forms.build_workflow_section_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=color_name,
            ),
        )
        return make_profile_aware_collapsible_card(
            card,
            page_name=self.ids.page_prefix,
            section_key=str(section_number),
        )

    def _build_steps(self) -> list[dict[str, str]]:
        return [
            {
                "number": "1",
                "title": "Upload FCS file",
                "description": (
                    "Load one FCS file so RosettaX can read its channels and metadata for plotting."
                ),
                "color_name": styling.get_workflow_section_color(1),
            },
            {
                "number": "2",
                "title": "Choose plot settings",
                "description": (
                    "Pick histogram or 2D scatter, then configure the plotted axes, scaling, and event limit."
                ),
                "color_name": styling.get_workflow_section_color(2),
            },
            {
                "number": "3",
                "title": "Inspect the data",
                "description": (
                    "Review the file summary and explore the plotted events to validate channels and distributions."
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
                style_overrides={
                    "height": "100%",
                },
            ),
        )

    def register_callbacks(self) -> "VisualizationPage":
        @dash.callback(
            dash.Output(self.ids.file_store, "data"),
            dash.Output(self.ids.upload_feedback, "children"),
            dash.Input(self.ids.upload, "contents"),
            dash.State(self.ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def upload_visualization_file(
            contents: Any,
            filename: Any,
        ) -> tuple[Any, str]:
            if not contents:
                return dash.no_update, "No file loaded."

            try:
                saved_file_path = upload_services.save_uploaded_file(
                    contents=str(contents),
                    filename=filename,
                    upload_directory=services.VISUALIZATION_UPLOAD_DIRECTORY,
                )
                summary = services.build_upload_summary(
                    uploaded_fcs_path=str(saved_file_path),
                    uploaded_filename=str(filename or Path(saved_file_path).name),
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    upload_services.build_upload_error_text(exception),
                )

            return summary, upload_services.build_loaded_filename_text(summary["uploaded_filename"])

        @dash.callback(
            dash.Output(self.ids.x_channel, "options"),
            dash.Output(self.ids.x_channel, "value"),
            dash.Output(self.ids.y_channel, "options"),
            dash.Output(self.ids.y_channel, "value"),
            dash.Output(self.ids.metadata, "children"),
            dash.Input(self.ids.file_store, "data"),
            dash.State(self.ids.x_channel, "value"),
            dash.State(self.ids.y_channel, "value"),
            prevent_initial_call=False,
        )
        def sync_visualization_controls(
            file_store: Any,
            current_x_channel: Any,
            current_y_channel: Any,
        ) -> tuple[list[dict[str, str]], Any, list[dict[str, str]], Any, Any]:
            if not isinstance(file_store, dict):
                empty_metadata = [
                    html.H5("File summary"),
                    html.Div("No FCS file loaded."),
                ]
                return [], None, [], None, empty_metadata

            column_names = list(file_store.get("column_names") or [])
            options = services.build_channel_options(column_names)
            x_channel = services.resolve_default_channel(
                column_names,
                current_value=current_x_channel,
                fallback_index=0,
            )
            y_channel = services.resolve_default_channel(
                column_names,
                current_value=current_y_channel,
                fallback_index=1,
            )

            metadata_children = [
                html.H5(
                    "File summary",
                    style={"marginBottom": styling.get_spacing_token("sm")},
                ),
                html.Div(f"File: {file_store.get('uploaded_filename') or 'n/a'}"),
                html.Div(f"Events: {file_store.get('number_of_events') or 'n/a'}"),
                html.Div(f"Parameters: {file_store.get('number_of_parameters') or 'n/a'}"),
                html.Div(f"$DATATYPE: {file_store.get('datatype') or 'n/a'}"),
                html.Div(f"$MODE: {file_store.get('mode') or 'n/a'}"),
            ]

            return options, x_channel, options, y_channel, metadata_children

        @dash.callback(
            dash.Output(self.ids.y_channel_container, "style"),
            dash.Output(self.ids.marker_size_container, "style"),
            dash.Output(self.ids.marker_opacity_container, "style"),
            dash.Output(self.ids.colormap_log, "style"),
            dash.Input(self.ids.plot_type, "value"),
            prevent_initial_call=False,
        )
        def toggle_scatter_control_visibility(
            plot_type: Any,
        ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            is_histogram = str(plot_type or "") == services.PLOT_TYPE_HISTOGRAM
            y_channel_style = {
                "minWidth": "260px",
                "flex": "1",
                "display": "none" if is_histogram else "block",
            }
            marker_field_style = {
                "minWidth": "180px",
                "display": "none" if is_histogram else "block",
            }
            colormap_toggle_style = {
                "display": "none" if is_histogram else "block",
                "width": "fit-content",
            }
            return (
                y_channel_style,
                marker_field_style,
                marker_field_style,
                colormap_toggle_style,
            )

        @dash.callback(
            dash.Output(self.ids.max_events, "value"),
            dash.Output(self.ids.x_log, "value"),
            dash.Output(self.ids.y_log, "value"),
            dash.Output(self.ids.colormap_log, "value"),
            dash.Output(self.ids.marker_size, "value"),
            dash.Output(self.ids.marker_opacity, "value"),
            dash.Output(self.ids.graph, "style"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_visualization_defaults_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any, Any, Any, Any, dict[str, Any]]:
            defaults = services.resolve_visualization_control_defaults(
                runtime_config_data,
            )
            return (
                defaults["max_events"],
                defaults["x_log_values"],
                defaults["y_log_values"],
                defaults["colormap_log_values"],
                defaults["marker_size"],
                defaults["marker_opacity"],
                defaults["graph_style"],
            )

        @dash.callback(
            dash.Output(self.ids.graph, "figure"),
            dash.Output(self.ids.plot_status, "children"),
            dash.Input(self.ids.file_store, "data"),
            dash.Input(self.ids.plot_type, "value"),
            dash.Input(self.ids.x_channel, "value"),
            dash.Input(self.ids.y_channel, "value"),
            dash.Input(self.ids.x_log, "value"),
            dash.Input(self.ids.y_log, "value"),
            dash.Input(self.ids.colormap_log, "value"),
            dash.Input(self.ids.marker_size, "value"),
            dash.Input(self.ids.marker_opacity, "value"),
            dash.Input(self.ids.max_events, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def update_visualization_plot(
            file_store: Any,
            plot_type: Any,
            x_channel: Any,
            y_channel: Any,
            x_log_values: Any,
            y_log_values: Any,
            colormap_log_values: Any,
            marker_size: Any,
            marker_opacity: Any,
            max_events: Any,
            runtime_config_data: Any,
        ) -> tuple[Any, str]:
            if not isinstance(file_store, dict):
                return (
                    services.build_empty_figure(
                        message="Upload an FCS file to start visualizing events.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "No file loaded.",
                )

            x_channel_string = str(x_channel or "").strip()
            y_channel_string = str(y_channel or "").strip()
            plot_type_string = str(plot_type or services.PLOT_TYPE_HISTOGRAM)
            uploaded_fcs_path = str(
                file_store.get("uploaded_fcs_path") or ""
            ).strip()

            if not x_channel_string:
                return (
                    services.build_empty_figure(
                        message="Select an X channel to render the plot.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "Select an X channel.",
                )

            if plot_type_string != services.PLOT_TYPE_HISTOGRAM and not y_channel_string:
                return (
                    services.build_empty_figure(
                        message="Select a Y channel to render the 2D plot.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "Select a Y channel.",
                )

            try:
                dataframe = services.load_plot_dataframe(
                    uploaded_fcs_path=str(file_store["uploaded_fcs_path"]),
                    x_channel=x_channel_string,
                    y_channel=y_channel_string,
                    max_events=services.clamp_max_events(max_events),
                )
                filtered_dataframe, skipped_events = services.filter_dataframe_for_plot(
                    dataframe,
                    x_channel=x_channel_string,
                    y_channel=y_channel_string,
                    log_x="enabled" in (x_log_values or []),
                    log_y="enabled" in (y_log_values or []),
                )
            except Exception as exception:
                return (
                    services.build_empty_figure(
                        message=f"Could not load FCS data: {type(exception).__name__}: {exception}",
                        runtime_config_data=runtime_config_data,
                    ),
                    "Could not render plot.",
                )

            if filtered_dataframe.empty:
                return (
                    services.build_empty_figure(
                        message="No events remain after filtering for finite/log-compatible values.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "No plottable events remain for the current axes and scales.",
                )

            figure = services.build_visualization_figure(
                dataframe=filtered_dataframe,
                uploaded_fcs_path=uploaded_fcs_path,
                plot_type=plot_type_string,
                x_channel=x_channel_string,
                y_channel=y_channel_string,
                log_x="enabled" in (x_log_values or []),
                log_y="enabled" in (y_log_values or []),
                colormap_log_scale="enabled" in (colormap_log_values or []),
                marker_size=marker_size,
                marker_opacity=marker_opacity,
                runtime_config_data=runtime_config_data,
            )

            return (
                figure,
                services.build_plot_status_text(
                    plotted_events=len(filtered_dataframe),
                    skipped_events=skipped_events,
                ),
            )

        return self


_page = VisualizationPage().register_callbacks()
layout = _page.layout

dash.register_page(
    __name__,
    path="/visualization",
    name="Visualization",
    order=7,
    layout=layout,
)
