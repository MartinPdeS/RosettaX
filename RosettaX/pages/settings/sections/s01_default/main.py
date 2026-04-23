# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import casting
from . import services

logger = logging.getLogger(__name__)

class DefaultProfile:
    def __init__(self, page) -> None:
        self.page = page

    def _persistent_input(self, **kwargs):
        return dcc.Input(
            persistence=True,
            persistence_type="session",
            **kwargs,
        )

    def _persistent_dropdown(self, **kwargs):
        return dcc.Dropdown(
            persistence=True,
            persistence_type="session",
            **kwargs,
        )

    def _get_layout(self):
        runtime_config = RuntimeConfig.from_default_profile()

        return dbc.Card(
            [
                dbc.CardHeader("1. Default values"),
                dbc.CardBody(
                    [
                        self._build_profile_controls_block(),
                        html.Hr(),
                        self._build_fluorescence_block(runtime_config),
                        html.Hr(),
                        self._build_scattering_block(runtime_config),
                        html.Hr(),
                        self._build_calibration_block(runtime_config),
                        html.Hr(),
                        self._build_visualization_block(runtime_config),
                        html.Hr(),
                        self._build_miscellaneous_block(runtime_config),
                        html.Div(style={"height": "12px"}),
                        self._build_save_block(),
                    ]
                ),
            ],
            className="mb-4",
        )

    def _build_profile_controls_block(self) -> html.Div:
        profile_options = services.build_profile_options()
        default_profile_value = services.resolve_default_profile_value(profile_options)

        return html.Div(
            [
                html.H5("Profile"),
                html.P(
                    "Choose a saved profile to load its values into the fields below.",
                    style={"marginBottom": "10px", "opacity": 0.85},
                ),
                self._setting_row(
                    "Saved profile:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.values_profile_dropdown,
                        options=profile_options,
                        value=default_profile_value,
                        placeholder="Select profile",
                        clearable=False,
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_fluorescence_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Fluorescence"),
                self._setting_row(
                    "MESF values:",
                    self._persistent_input(
                        id=self.page.ids.Default.mesf_values,
                        value=casting.format_float_list_for_input(
                            runtime_config.get_path("calibration.mesf_values", default=[])
                        ),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Peak count:",
                    self._persistent_input(
                        id=self.page.ids.Default.peak_count,
                        value=runtime_config.get_int("calibration.peak_count", default=4),
                        type="number",
                        step=1,
                        min=1,
                        max=10,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Histogram scale:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.histogram_scale,
                        options=[
                            {"label": "Linear", "value": "linear"},
                            {"label": "Log", "value": "log"},
                        ],
                        value=runtime_config.get_str("calibration.histogram_scale", default="log"),
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_scattering_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Scattering"),
                self._setting_row(
                    "Medium refractive index:",
                    self._persistent_input(
                        id=self.page.ids.Default.medium_refractive_index,
                        type="number",
                        value=runtime_config.get_float("optics.medium_refractive_index", default=1.334),
                        step=0.001,
                        min=0.001,
                        max=2.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Core refractive index:",
                    self._persistent_input(
                        id=self.page.ids.Default.core_refractive_index,
                        type="number",
                        value=runtime_config.get_float("particle_model.core_refractive_index", default=1.5),
                        step=0.001,
                        min=0.001,
                        max=2.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Shell refractive index:",
                    self._persistent_input(
                        id=self.page.ids.Default.shell_refractive_index,
                        type="number",
                        value=runtime_config.get_float("particle_model.shell_refractive_index", default=1.5),
                        step=0.001,
                        min=0.001,
                        max=2.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Particle refractive index:",
                    self._persistent_input(
                        id=self.page.ids.Default.particle_refractive_index,
                        type="number",
                        value=runtime_config.get_float("particle_model.particle_refractive_index", default=1.59),
                        step=0.001,
                        min=0.001,
                        max=2.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Wavelength (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.wavelength_nm,
                        type="number",
                        value=runtime_config.get_float("optics.wavelength_nm", default=488.0),
                        step=1,
                        min=1,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Shell thickness list (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.shell_thickness_nm,
                        type="text",
                        value=casting.format_float_list_for_input(
                            runtime_config.get_path("particle_model.shell_thickness_nm", default=[])
                        ),
                        placeholder="5, 10, 15",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Core diameter list (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.core_diameter_nm,
                        type="text",
                        value=casting.format_float_list_for_input(
                            runtime_config.get_path("particle_model.core_diameter_nm", default=[])
                        ),
                        placeholder="80, 120, 160",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Particle diameter list (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.particle_diameter_nm,
                        type="text",
                        value=casting.format_float_list_for_input(
                            runtime_config.get_path("particle_model.particle_diameter_nm", default=[])
                        ),
                        placeholder="100, 200, 300",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Particle type:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.mie_model,
                        options=[
                            {"label": "Solid Sphere", "value": "Solid Sphere"},
                            {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
                        ],
                        value=runtime_config.get_str("particle_model.mie_model", default="Solid Sphere"),
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default gating channel:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_gating_channel,
                        value=casting.coerce_optional_string(
                            runtime_config.get_path("calibration.default_gating_channel", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default gating threshold:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_gating_threshold,
                        value=casting.coerce_optional_string(
                            runtime_config.get_path("calibration.default_gating_threshold", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_calibration_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Calibration"),
                self._setting_row(
                    "Max events for analysis:",
                    self._persistent_input(
                        id=self.page.ids.Default.max_events_for_analysis,
                        value=runtime_config.get_int("calibration.max_events_for_analysis", default=100),
                        type="number",
                        step=1,
                        min=1,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Number of bins for plots:",
                    self._persistent_input(
                        id=self.page.ids.Default.n_bins_for_plots,
                        value=runtime_config.get_int("calibration.n_bins_for_plots", default=100),
                        type="number",
                        step=10,
                        min=10,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Show calibration plot by default:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.show_calibration_plot_by_default,
                        options=[
                            {"label": "Yes", "value": "yes"},
                            {"label": "No", "value": "no"},
                        ],
                        value="yes"
                        if runtime_config.get_bool("calibration.show_calibration_plot_by_default", default=False)
                        else "no",
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default output suffix:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_output_suffix,
                        value=runtime_config.get_str("calibration.default_output_suffix", default="_calibrated"),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Operator name:",
                    self._persistent_input(
                        id=self.page.ids.Default.operator_name,
                        value=runtime_config.get_str("metadata.operator_name", default=""),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Instrument name:",
                    self._persistent_input(
                        id=self.page.ids.Default.instrument_name,
                        value=runtime_config.get_str("metadata.instrument_name", default=""),
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_visualization_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Visualization"),
                self._setting_row(
                    "Default marker size:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_marker_size,
                        type="number",
                        value=runtime_config.get_float("visualization.default_marker_size", default=8.0),
                        step=0.5,
                        min=1.0,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default line width:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_line_width,
                        type="number",
                        value=runtime_config.get_float("visualization.default_line_width", default=2.0),
                        step=0.5,
                        min=0.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Show grid by default:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.show_grid_by_default,
                        options=[
                            {"label": "Yes", "value": "yes"},
                            {"label": "No", "value": "no"},
                        ],
                        value="yes"
                        if runtime_config.get_bool("visualization.show_grid_by_default", default=True)
                        else "no",
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_miscellaneous_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Miscellaneous"),
                self._setting_row(
                    "Default Fluorescence FCS file path:",
                    self._persistent_input(
                        id=self.page.ids.Default.fluorescence_fcs_file_path,
                        value=casting.coerce_optional_string(
                            runtime_config.get_path("files.fluorescence_fcs_file_path", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default Scattering FCS file path:",
                    self._persistent_input(
                        id=self.page.ids.Default.scattering_fcs_file_path,
                        value=casting.coerce_optional_string(
                            runtime_config.get_path("files.scattering_fcs_file_path", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Theme mode:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.theme_mode,
                        options=[
                            {"label": "Dark", "value": "dark"},
                            {"label": "Light", "value": "light"},
                        ],
                        value=runtime_config.get_theme_mode(default="dark"),
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Show graphs:",
                    self._persistent_dropdown(
                        id=self.page.ids.Default.show_graphs,
                        options=[
                            {"label": "Yes", "value": "yes"},
                            {"label": "No", "value": "no"},
                        ],
                        value="yes" if runtime_config.get_show_graphs(default=False) else "no",
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
            ]
        )

    def _build_save_block(self) -> html.Div:
        return html.Div(
            [
                dbc.Button(
                    "Save changes",
                    id=self.page.ids.Default.save_changes_button,
                    color="primary",
                    n_clicks=0,
                ),
                dbc.Alert(
                    "",
                    id=self.page.ids.Default.save_confirmation,
                    color="success",
                    is_open=False,
                    style={"marginTop": "10px", "marginBottom": "0px"},
                ),
            ]
        )

    def register_callbacks(self) -> None:
        @callback(
            Output(self.page.ids.Default.medium_refractive_index, "value"),
            Output(self.page.ids.Default.core_refractive_index, "value"),
            Output(self.page.ids.Default.shell_refractive_index, "value"),
            Output(self.page.ids.Default.shell_thickness_nm, "value"),
            Output(self.page.ids.Default.core_diameter_nm, "value"),
            Output(self.page.ids.Default.particle_diameter_nm, "value"),
            Output(self.page.ids.Default.particle_refractive_index, "value"),
            Output(self.page.ids.Default.wavelength_nm, "value"),
            Output(self.page.ids.Default.max_events_for_analysis, "value"),
            Output(self.page.ids.Default.n_bins_for_plots, "value"),
            Output(self.page.ids.Default.peak_count, "value"),
            Output(self.page.ids.Default.mie_model, "value"),
            Output(self.page.ids.Default.mesf_values, "value"),
            Output(self.page.ids.Default.fluorescence_fcs_file_path, "value"),
            Output(self.page.ids.Default.scattering_fcs_file_path, "value"),
            Output(self.page.ids.Default.default_gating_channel, "value"),
            Output(self.page.ids.Default.default_gating_threshold, "value"),
            Output(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            Output(self.page.ids.Default.histogram_scale, "value"),
            Output(self.page.ids.Default.default_output_suffix, "value"),
            Output(self.page.ids.Default.operator_name, "value"),
            Output(self.page.ids.Default.instrument_name, "value"),
            Output(self.page.ids.Default.theme_mode, "value"),
            Output(self.page.ids.Default.show_graphs, "value"),
            Output(self.page.ids.Default.default_marker_size, "value"),
            Output(self.page.ids.Default.default_line_width, "value"),
            Output(self.page.ids.Default.show_grid_by_default, "value"),
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: Optional[str]):
            if not dropdown_value:
                return tuple([dash.no_update] * 27)

            saved_profile = services.get_saved_profile(dropdown_value) or {}
            runtime_config = RuntimeConfig.from_dict(saved_profile)
            flattened_profile = services.flatten_runtime_config(runtime_config)

            return (
                flattened_profile.get("medium_refractive_index"),
                flattened_profile.get("core_refractive_index"),
                flattened_profile.get("shell_refractive_index"),
                casting.format_float_list_for_input(flattened_profile.get("shell_thickness_nm")),
                casting.format_float_list_for_input(flattened_profile.get("core_diameter_nm")),
                casting.format_float_list_for_input(flattened_profile.get("particle_diameter_nm")),
                flattened_profile.get("particle_refractive_index"),
                flattened_profile.get("wavelength_nm"),
                flattened_profile.get("max_events_for_analysis"),
                flattened_profile.get("n_bins_for_plots"),
                flattened_profile.get("peak_count"),
                flattened_profile.get("mie_model"),
                casting.format_float_list_for_input(flattened_profile.get("mesf_values")),
                flattened_profile.get("fluorescence_fcs_file_path") or "",
                flattened_profile.get("scattering_fcs_file_path") or "",
                flattened_profile.get("default_gating_channel") or "",
                casting.coerce_optional_string(flattened_profile.get("default_gating_threshold")) or "",
                "yes" if flattened_profile.get("show_calibration_plot_by_default") else "no",
                flattened_profile.get("histogram_scale"),
                flattened_profile.get("default_output_suffix") or "",
                flattened_profile.get("operator_name") or "",
                flattened_profile.get("instrument_name") or "",
                flattened_profile.get("theme_mode"),
                "yes" if flattened_profile.get("show_graphs") else "no",
                flattened_profile.get("default_marker_size"),
                flattened_profile.get("default_line_width"),
                "yes" if flattened_profile.get("show_grid_by_default") else "no",
            )

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children"),
            Output("runtime-config-store", "data"),
            Output(self.page.ids.Default.save_confirmation, "is_open"),
            Output(self.page.ids.Default.save_confirmation, "color"),
            Input(self.page.ids.Default.save_changes_button, "n_clicks"),
            State(self.page.ids.Default.values_profile_dropdown, "value"),
            State(self.page.ids.Default.medium_refractive_index, "value"),
            State(self.page.ids.Default.core_refractive_index, "value"),
            State(self.page.ids.Default.shell_refractive_index, "value"),
            State(self.page.ids.Default.shell_thickness_nm, "value"),
            State(self.page.ids.Default.core_diameter_nm, "value"),
            State(self.page.ids.Default.particle_diameter_nm, "value"),
            State(self.page.ids.Default.particle_refractive_index, "value"),
            State(self.page.ids.Default.wavelength_nm, "value"),
            State(self.page.ids.Default.max_events_for_analysis, "value"),
            State(self.page.ids.Default.n_bins_for_plots, "value"),
            State(self.page.ids.Default.peak_count, "value"),
            State(self.page.ids.Default.mie_model, "value"),
            State(self.page.ids.Default.mesf_values, "value"),
            State(self.page.ids.Default.fluorescence_fcs_file_path, "value"),
            State(self.page.ids.Default.scattering_fcs_file_path, "value"),
            State(self.page.ids.Default.default_gating_channel, "value"),
            State(self.page.ids.Default.default_gating_threshold, "value"),
            State(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            State(self.page.ids.Default.histogram_scale, "value"),
            State(self.page.ids.Default.default_output_suffix, "value"),
            State(self.page.ids.Default.operator_name, "value"),
            State(self.page.ids.Default.instrument_name, "value"),
            State(self.page.ids.Default.theme_mode, "value"),
            State(self.page.ids.Default.show_graphs, "value"),
            State(self.page.ids.Default.default_marker_size, "value"),
            State(self.page.ids.Default.default_line_width, "value"),
            State(self.page.ids.Default.show_grid_by_default, "value"),
            prevent_initial_call=True,
        )
        def edit_settings(n_clicks: Any, profile_target: str, *args):
            if dash.ctx.triggered_id != self.page.ids.Default.save_changes_button:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            try:
                flat_runtime_payload = services.build_flat_runtime_payload_from_form_values(args)
                nested_profile_payload = services.build_nested_profile_payload(flat_runtime_payload)

                if not profile_target:
                    return (
                        "No target profile selected.",
                        dash.no_update,
                        True,
                        "danger",
                    )

                logger.debug(
                    "Saving profile with profile_target=%r flat_runtime_payload=%r nested_profile_payload=%r",
                    profile_target,
                    flat_runtime_payload,
                    nested_profile_payload,
                )

                services.save_profile(profile_target, nested_profile_payload)

                return (
                    f"Saved profile: {profile_target}",
                    dash.no_update,
                    True,
                    "success",
                )

            except Exception as exc:
                return (
                    f"{type(exc).__name__}: {exc}",
                    dash.no_update,
                    True,
                    "danger",
                )

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children", allow_duplicate=True),
            Output(self.page.ids.Default.save_confirmation, "is_open", allow_duplicate=True),
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            Input(self.page.ids.Default.medium_refractive_index, "value"),
            Input(self.page.ids.Default.core_refractive_index, "value"),
            Input(self.page.ids.Default.shell_refractive_index, "value"),
            Input(self.page.ids.Default.shell_thickness_nm, "value"),
            Input(self.page.ids.Default.core_diameter_nm, "value"),
            Input(self.page.ids.Default.particle_diameter_nm, "value"),
            Input(self.page.ids.Default.particle_refractive_index, "value"),
            Input(self.page.ids.Default.wavelength_nm, "value"),
            Input(self.page.ids.Default.max_events_for_analysis, "value"),
            Input(self.page.ids.Default.n_bins_for_plots, "value"),
            Input(self.page.ids.Default.peak_count, "value"),
            Input(self.page.ids.Default.mie_model, "value"),
            Input(self.page.ids.Default.mesf_values, "value"),
            Input(self.page.ids.Default.fluorescence_fcs_file_path, "value"),
            Input(self.page.ids.Default.scattering_fcs_file_path, "value"),
            Input(self.page.ids.Default.default_gating_channel, "value"),
            Input(self.page.ids.Default.default_gating_threshold, "value"),
            Input(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            Input(self.page.ids.Default.histogram_scale, "value"),
            Input(self.page.ids.Default.default_output_suffix, "value"),
            Input(self.page.ids.Default.operator_name, "value"),
            Input(self.page.ids.Default.instrument_name, "value"),
            Input(self.page.ids.Default.theme_mode, "value"),
            Input(self.page.ids.Default.show_graphs, "value"),
            Input(self.page.ids.Default.default_marker_size, "value"),
            Input(self.page.ids.Default.default_line_width, "value"),
            Input(self.page.ids.Default.show_grid_by_default, "value"),
            prevent_initial_call=True,
        )
        def clear_save_confirmation(*_args):
            return "", False

    def _setting_row(self, label: str, component):
        return html.Div(
            [
                html.Div(
                    label,
                    style={
                        "width": "320px",
                        "fontWeight": "500",
                        "marginBottom": "0",
                    },
                ),
                html.Div(
                    component,
                    style={"flex": "1"},
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "marginBottom": "10px",
            },
        )