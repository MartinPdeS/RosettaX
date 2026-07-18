# -*- coding: utf-8 -*-

from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from RosettaX.ui import (
    WorkflowStep,
    build_workflow_page_header,
    build_workflow_section_card,
)
from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.calibration_cards import make_profile_aware_collapsible_card
from RosettaX.workflow.file_selection.services import (
    build_file_options,
    resolve_selected_file,
)
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
                    title="Upload visualization FCS files",
                    subtitle="Load compatible FCS files, then choose which file to inspect.",
                    tooltip_text=(
                        "Upload one or more FCS files with matching channels, FCS versions, "
                        "and detector voltages. The file selector in the plot settings lets "
                        "you choose which compatible file to inspect."
                    ),
                    body_children=[
                        ui_forms.build_upload_widget(
                            upload_id=self.ids.upload,
                            prompt_text="Select one or more compatible FCS files",
                            accepted_file_extensions=".fcs",
                            multiple=True,
                        ),
                        ui_forms.build_upload_status(
                            status_id=self.ids.upload_feedback,
                            initial_text="No file loaded.",
                        ),
                    ],
                ),
                self._build_plot_workspace(
                    default_controls=default_controls,
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("lg"),
            },
        )

    def _build_plot_workspace(self, *, default_controls: dict[str, Any]) -> html.Div:
        field_label_style = {
            "display": "block",
            "marginBottom": styling.get_spacing_token("xs"),
        }

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("FCS file", style=field_label_style),
                                dcc.Dropdown(
                                    id=self.ids.file_selection,
                                    options=[],
                                    value=None,
                                    clearable=False,
                                    placeholder="Upload compatible FCS files",
                                ),
                            ],
                            style={"minWidth": "260px", "flex": "1"},
                        ),
                        html.Div(
                            [
                                html.Label("Plot type", style=field_label_style),
                                dcc.Dropdown(
                                    id=self.ids.plot_type,
                                    options=[
                                        {
                                            "label": "1D histogram",
                                            "value": services.PLOT_TYPE_HISTOGRAM,
                                        },
                                        {
                                            "label": "Smoothed histogram",
                                            "value": services.PLOT_TYPE_SMOOTHED_HISTOGRAM,
                                        },
                                        {
                                            "label": "2D scatter",
                                            "value": services.PLOT_TYPE_SCATTER,
                                        },
                                    ],
                                    value=services.PLOT_TYPE_HISTOGRAM,
                                    clearable=False,
                                ),
                            ],
                            style={"minWidth": "220px", "flex": "1"},
                        ),
                        html.Div(
                            [
                                html.Label("X channel", style=field_label_style),
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
                                html.Label("Y channel", style=field_label_style),
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
                html.Div(
                    [
                        dbc.Checklist(
                            id=self.ids.x_log,
                            options=[{"label": "Log X", "value": "enabled"}],
                            value=default_controls["x_log_values"],
                            inline=True,
                            switch=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                        dbc.Checklist(
                            id=self.ids.y_log,
                            options=[{"label": "Log Y", "value": "enabled"}],
                            value=default_controls["y_log_values"],
                            inline=True,
                            switch=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                        dbc.Checklist(
                            id=self.ids.colormap_log,
                            options=[
                                {"label": "Log colormap", "value": "enabled"}
                            ],
                            value=default_controls["colormap_log_values"],
                            inline=True,
                            switch=True,
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    id=self.ids.axis_toggle_container,
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": styling.get_spacing_token("lg"),
                        "flexWrap": "wrap",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Max events", style=field_label_style),
                                dcc.Input(
                                    id=self.ids.max_events,
                                    type="number",
                                    value=default_controls["max_events"],
                                    min=0,
                                    step=1000,
                                    style={"width": "160px", "color": "inherit"},
                                ),
                            ],
                            style={"minWidth": "180px"},
                        ),
                        html.Div(
                            [
                                html.Label("Marker size", style=field_label_style),
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
                                html.Label("Marker opacity", style=field_label_style),
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
                        html.Div(
                            [
                                html.Label(
                                    "Smoothing strength (sigma points)",
                                    style=field_label_style,
                                ),
                                dcc.Input(
                                    id=self.ids.histogram_smoothing_sigma,
                                    type="number",
                                    min=0,
                                    max=100,
                                    step=0.5,
                                    value=2.0,
                                    style={"width": "180px", "color": "inherit"},
                                ),
                            ],
                            id=self.ids.histogram_smoothing_container,
                            style={"minWidth": "220px", "display": "none"},
                        ),
                    ],
                    id=self.ids.scatter_controls_container,
                    style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "gap": styling.get_spacing_token("md"),
                        "flexWrap": "wrap",
                    },
                ),
                html.Div(
                    id=self.ids.plot_status,
                    style={"opacity": 0.8},
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
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": styling.get_spacing_token("md"),
                "minWidth": 0,
            },
        )

    def _build_header_card(self) -> dbc.Card:
        return build_workflow_page_header(
            title="Visualization",
            description=(
                "Upload compatible FCS files, choose one to inspect, and view it with a 1D histogram or a 2D scatter colored by local event density."
            ),
            steps=self._build_steps(),
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
        section_key = title.lower().replace(" ", "-")
        card = build_workflow_section_card(
            section_number=section_number,
            title=title,
            subtitle=subtitle,
            body_children=body_children,
            tooltip_text=tooltip_text,
            tooltip_target_id=f"{self.ids.page_prefix}-{section_key}-info-target",
            tooltip_id=f"{self.ids.page_prefix}-{section_key}-info-tooltip",
        )
        return make_profile_aware_collapsible_card(
            card,
            page_name=self.ids.page_prefix,
            section_key=str(section_number),
        )

    def _build_steps(self) -> list[WorkflowStep]:
        return [
            WorkflowStep(
                number="1",
                title="Upload FCS file",
                description=(
                    "Load one or more compatible FCS files so RosettaX can read their channels and metadata for plotting."
                ),
                color_name=styling.get_workflow_section_color(1),
            ),
            WorkflowStep(
                number="2",
                title="Choose plot settings",
                description=(
                    "Pick histogram or 2D scatter, then configure the plotted axes, scaling, and event limit."
                ),
                color_name=styling.get_workflow_section_color(2),
            ),
            WorkflowStep(
                number="3",
                title="Inspect the data",
                description=(
                    "Explore the plotted events to validate channels and distributions."
                ),
                color_name=styling.get_workflow_section_color(3),
            ),
        ]

    def register_callbacks(self) -> "VisualizationPage":
        @dash.callback(
            dash.Output(self.ids.file_store, "data"),
            dash.Output(self.ids.upload_feedback, "children"),
            dash.Output(self.ids.upload_feedback, "color"),
            dash.Input(self.ids.upload, "contents"),
            dash.State(self.ids.upload, "filename"),
            prevent_initial_call=True,
        )
        def upload_visualization_file(
            contents: Any,
            filename: Any,
        ) -> tuple[Any, str, str]:
            if not contents:
                return dash.no_update, "No file loaded.", "secondary"

            try:
                saved_file_paths, safe_filenames = upload_services.save_uploaded_batch(
                    contents=contents,
                    filenames=filename,
                    upload_directory=services.VISUALIZATION_UPLOAD_DIRECTORY,
                )
                consistency_report = upload_services.inspect_compatible_fcs_batch(
                    saved_file_paths,
                )
                feedback_text, feedback_color = upload_services.build_upload_feedback(
                    filenames=safe_filenames,
                    consistency_report=consistency_report,
                )
                if not consistency_report.get("are_all_files_consistent", False):
                    return dash.no_update, feedback_text, feedback_color

                summary = services.build_upload_batch_summary(
                    uploaded_fcs_paths=saved_file_paths,
                    uploaded_filenames=safe_filenames,
                    consistency_report=consistency_report,
                )
            except Exception as exception:
                return (
                    dash.no_update,
                    upload_services.build_upload_error_text(exception),
                    "danger",
                )

            return summary, feedback_text, feedback_color

        @dash.callback(
            dash.Output(self.ids.x_channel, "options"),
            dash.Output(self.ids.x_channel, "value"),
            dash.Output(self.ids.y_channel, "options"),
            dash.Output(self.ids.y_channel, "value"),
            dash.Output(self.ids.file_selection, "options"),
            dash.Output(self.ids.file_selection, "value"),
            dash.Input(self.ids.file_store, "data"),
            dash.State(self.ids.x_channel, "value"),
            dash.State(self.ids.y_channel, "value"),
            dash.State(self.ids.file_selection, "value"),
            prevent_initial_call=False,
        )
        def sync_visualization_controls(
            file_store: Any,
            current_x_channel: Any,
            current_y_channel: Any,
            current_file_path: Any,
        ) -> tuple[list[dict[str, str]], Any, list[dict[str, str]], Any, list[dict[str, str]], Any]:
            if not isinstance(file_store, dict):
                return [], None, [], None, [], None

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
            file_options = build_file_options(file_store)
            selected_file = resolve_selected_file(
                file_store,
                current_path=current_file_path,
            )
            file_path = selected_file.path if selected_file is not None else None

            return options, x_channel, options, y_channel, file_options, file_path

        @dash.callback(
            dash.Output(self.ids.y_channel_container, "style"),
            dash.Output(self.ids.marker_size_container, "style"),
            dash.Output(self.ids.marker_opacity_container, "style"),
            dash.Output(self.ids.colormap_log, "style"),
            dash.Output(self.ids.histogram_smoothing_container, "style"),
            dash.Input(self.ids.plot_type, "value"),
            prevent_initial_call=False,
        )
        def toggle_scatter_control_visibility(
            plot_type: Any,
        ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
            plot_type_string = str(plot_type or "")
            is_histogram = plot_type_string in {
                services.PLOT_TYPE_HISTOGRAM,
                services.PLOT_TYPE_SMOOTHED_HISTOGRAM,
            }
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
            smoothing_style = {
                "minWidth": "220px",
                "display": "block"
                if plot_type_string == services.PLOT_TYPE_SMOOTHED_HISTOGRAM
                else "none",
            }
            return (
                y_channel_style,
                marker_field_style,
                marker_field_style,
                colormap_toggle_style,
                smoothing_style,
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
            dash.Input(self.ids.file_selection, "value"),
            dash.Input(self.ids.plot_type, "value"),
            dash.Input(self.ids.x_channel, "value"),
            dash.Input(self.ids.y_channel, "value"),
            dash.Input(self.ids.x_log, "value"),
            dash.Input(self.ids.y_log, "value"),
            dash.Input(self.ids.colormap_log, "value"),
            dash.Input(self.ids.marker_size, "value"),
            dash.Input(self.ids.marker_opacity, "value"),
            dash.Input(self.ids.histogram_smoothing_sigma, "value"),
            dash.Input(self.ids.max_events, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def update_visualization_plot(
            file_store: Any,
            selected_file_path: Any,
            plot_type: Any,
            x_channel: Any,
            y_channel: Any,
            x_log_values: Any,
            y_log_values: Any,
            colormap_log_values: Any,
            marker_size: Any,
            marker_opacity: Any,
            smoothing_sigma_points: Any,
            max_events: Any,
            runtime_config_data: Any,
        ) -> tuple[Any, str]:
            if not isinstance(file_store, dict):
                return (
                    services.build_empty_figure(
                        message="Upload compatible FCS files to start visualizing events.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "No file loaded.",
                )

            x_channel_string = str(x_channel or "").strip()
            y_channel_string = str(y_channel or "").strip()
            plot_type_string = str(plot_type or services.PLOT_TYPE_HISTOGRAM)
            selected_file = resolve_selected_file(
                file_store,
                current_path=selected_file_path,
            )
            uploaded_fcs_path = selected_file.path if selected_file is not None else ""

            if not x_channel_string:
                return (
                    services.build_empty_figure(
                        message="Select an X channel to render the plot.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "Select an X channel.",
                )

            if plot_type_string == services.PLOT_TYPE_SCATTER and not y_channel_string:
                return (
                    services.build_empty_figure(
                        message="Select a Y channel to render the 2D plot.",
                        runtime_config_data=runtime_config_data,
                    ),
                    "Select a Y channel.",
                )

            try:
                dataframe = services.load_plot_dataframe(
                    uploaded_fcs_path=uploaded_fcs_path,
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
                smoothing_sigma_points=smoothing_sigma_points,
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
