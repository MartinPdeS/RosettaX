from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.settings.utils import get_saved_profile, save_profile
from RosettaX.utils import directories
from RosettaX.utils.runtime_config import RuntimeConfig
import re


class DefaultProfile:
    def __init__(self, page) -> None:
        self.page = page
        self.persistence_type = "session"

    def _persistent_input(self, **kwargs):
        return dcc.Input(
            persistence=True,
            persistence_type=self.persistence_type,
            **kwargs,
        )

    def _persistent_dropdown(self, **kwargs):
        return dcc.Dropdown(
            persistence=True,
            persistence_type=self.persistence_type,
            **kwargs,
        )

    def _get_layout(self):
        runtime_config = RuntimeConfig()

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
                        self._build_miscellaneous_block(runtime_config),
                        html.Div(style={"height": "12px"}),
                        self._build_save_block(),
                    ]
                ),
            ],
            className="mb-4",
        )

    def _build_profile_controls_block(self) -> html.Div:
        profile_options = self._build_profile_options()
        default_profile_value = self._resolve_default_profile_value(profile_options)

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
                        value=getattr(runtime_config.Default, "mesf_values", ""),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Peak count:",
                    self._persistent_input(
                        id=self.page.ids.Default.peak_count,
                        value=getattr(runtime_config.Default, "peak_count", 3),
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
                        value=getattr(runtime_config.Default, "histogram_scale", "linear"),
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
                        value=getattr(runtime_config.Default, "medium_refractive_index", ""),
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
                        value=getattr(runtime_config.Default, "core_refractive_index", ""),
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
                        value=getattr(runtime_config.Default, "shell_refractive_index", ""),
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
                        value=getattr(runtime_config.Default, "particle_refractive_index", ""),
                        step=0.001,
                        min=0.001,
                        max=2.5,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Shell thickness (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.shell_thickness_nm,
                        type="number",
                        value=getattr(runtime_config.Default, "shell_thickness", ""),
                        step=0.01,
                        min=0.01,
                        max=1000,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Core diameter (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.core_diameter_nm,
                        type="number",
                        value=getattr(runtime_config.Default, "core_diameter", ""),
                        step=0.01,
                        min=0.01,
                        max=1000,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Particle diameter (nm):",
                    self._persistent_input(
                        id=self.page.ids.Default.particle_diameter_nm,
                        type="number",
                        value=getattr(runtime_config.Default, "particle_diameter", ""),
                        step=1,
                        min=1,
                        max=1000,
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
                        value=getattr(runtime_config.Default, "mie_model", "Solid Sphere"),
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default gating channel:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_gating_channel,
                        value=getattr(runtime_config.Default, "default_gating_channel", ""),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default gating threshold:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_gating_threshold,
                        value=getattr(runtime_config.Default, "default_gating_threshold", ""),
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
                        value=getattr(runtime_config.Default, "max_events_for_analysis", ""),
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
                        value=getattr(runtime_config.Default, "n_bins_for_plots", ""),
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
                        value=getattr(runtime_config.Default, "show_calibration_plot_by_default", "no"),
                        clearable=False,
                        searchable=False,
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default output suffix:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_output_suffix,
                        value=getattr(runtime_config.Default, "default_output_suffix", "_calibrated"),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Operator name:",
                    self._persistent_input(
                        id=self.page.ids.Default.operator_name,
                        value=getattr(runtime_config.Default, "operator_name", ""),
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Instrument name:",
                    self._persistent_input(
                        id=self.page.ids.Default.instrument_name,
                        value=getattr(runtime_config.Default, "instrument_name", ""),
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
                    "Default FCS file path:",
                    self._persistent_input(
                        id=self.page.ids.Default.fcs_file_path,
                        value=getattr(runtime_config.Default, "fcs_file_path", ""),
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
                        value=getattr(runtime_config.Default, "theme_mode", "dark"),
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
            Output(self.page.ids.Default.max_events_for_analysis, "value"),
            Output(self.page.ids.Default.n_bins_for_plots, "value"),
            Output(self.page.ids.Default.peak_count, "value"),
            Output(self.page.ids.Default.mie_model, "value"),
            Output(self.page.ids.Default.mesf_values, "value"),
            Output(self.page.ids.Default.fcs_file_path, "value"),
            Output(self.page.ids.Default.default_gating_channel, "value"),
            Output(self.page.ids.Default.default_gating_threshold, "value"),
            Output(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            Output(self.page.ids.Default.histogram_scale, "value"),
            Output(self.page.ids.Default.default_output_suffix, "value"),
            Output(self.page.ids.Default.operator_name, "value"),
            Output(self.page.ids.Default.instrument_name, "value"),
            Output(self.page.ids.Default.theme_mode, "value"),
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: Optional[str]):
            if not dropdown_value:
                return tuple([dash.no_update] * 21)

            settings = get_saved_profile(dropdown_value) or {}

            runtime_config = RuntimeConfig()
            runtime_config.load_json(dropdown_value)

            return (
                settings.get("medium_refractive_index", ""),
                settings.get("core_refractive_index", ""),
                settings.get("shell_refractive_index", ""),
                settings.get("shell_thickness_nm", ""),
                settings.get("core_diameter_nm", ""),
                settings.get("particle_diameter_nm", ""),
                settings.get("particle_refractive_index", ""),
                settings.get("max_events_for_analysis", ""),
                settings.get("n_bins_for_plots", ""),
                settings.get("peak_count", ""),
                settings.get("mie_model", "Solid Sphere"),
                settings.get("mesf_values", ""),
                settings.get("fcs_file_path", ""),
                settings.get("default_gating_channel", ""),
                settings.get("default_gating_threshold", ""),
                settings.get("show_calibration_plot_by_default", "no"),
                settings.get("histogram_scale", "linear"),
                settings.get("default_output_suffix", "_calibrated"),
                settings.get("operator_name", ""),
                settings.get("instrument_name", ""),
                settings.get("theme_mode", "dark"),
            )

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children"),
            Output("runtime-config-store", "data"),
            Output(self.page.ids.Default.save_confirmation, "is_open"),
            Output(self.page.ids.Default.save_confirmation, "color"),
            Output("theme-switch", "value"),
            Input(self.page.ids.Default.save_changes_button, "n_clicks"),
            State(self.page.ids.Default.values_profile_dropdown, "value"),
            State(self.page.ids.Default.medium_refractive_index, "value"),
            State(self.page.ids.Default.core_refractive_index, "value"),
            State(self.page.ids.Default.shell_refractive_index, "value"),
            State(self.page.ids.Default.shell_thickness_nm, "value"),
            State(self.page.ids.Default.core_diameter_nm, "value"),
            State(self.page.ids.Default.particle_diameter_nm, "value"),
            State(self.page.ids.Default.particle_refractive_index, "value"),
            State(self.page.ids.Default.max_events_for_analysis, "value"),
            State(self.page.ids.Default.n_bins_for_plots, "value"),
            State(self.page.ids.Default.peak_count, "value"),
            State(self.page.ids.Default.mie_model, "value"),
            State(self.page.ids.Default.mesf_values, "value"),
            State(self.page.ids.Default.fcs_file_path, "value"),
            State(self.page.ids.Default.default_gating_channel, "value"),
            State(self.page.ids.Default.default_gating_threshold, "value"),
            State(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            State(self.page.ids.Default.histogram_scale, "value"),
            State(self.page.ids.Default.default_output_suffix, "value"),
            State(self.page.ids.Default.operator_name, "value"),
            State(self.page.ids.Default.instrument_name, "value"),
            State(self.page.ids.Default.theme_mode, "value"),
            prevent_initial_call=True,
        )
        def edit_settings(_n_clicks: Any, profile_target: str, *args):
            del _n_clicks

            try:
                keys = [
                    "medium_refractive_index",
                    "core_refractive_index",
                    "shell_refractive_index",
                    "shell_thickness_nm",
                    "core_diameter_nm",
                    "particle_diameter_nm",
                    "particle_refractive_index",
                    "max_events_for_analysis",
                    "n_bins_for_plots",
                    "peak_count",
                    "mie_model",
                    "mesf_values",
                    "fcs_file_path",
                    "default_gating_channel",
                    "default_gating_threshold",
                    "show_calibration_plot_by_default",
                    "histogram_scale",
                    "default_output_suffix",
                    "operator_name",
                    "instrument_name",
                    "theme_mode",
                ]

                new_dict = {key: value for key, value in zip(keys, args)}

                new_dict["mesf_values"] = re.sub(
                    r"[^\d,\s]",
                    "",
                    str(new_dict.get("mesf_values", "")),
                )

                if not profile_target:
                    return (
                        "No target profile selected.",
                        dash.no_update,
                        True,
                        "danger",
                        dash.no_update,
                    )

                save_profile(profile_target, new_dict)

                runtime_config = RuntimeConfig()
                runtime_config.update(**new_dict)

                theme_is_dark = str(new_dict.get("theme_mode", "dark")).strip().lower() == "dark"

                return (
                    f"Saved profile: {profile_target}",
                    new_dict,
                    True,
                    "success",
                    theme_is_dark,
                )

            except Exception as exc:
                return (
                    f"{type(exc).__name__}: {exc}",
                    dash.no_update,
                    True,
                    "danger",
                    dash.no_update,
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
            Input(self.page.ids.Default.max_events_for_analysis, "value"),
            Input(self.page.ids.Default.n_bins_for_plots, "value"),
            Input(self.page.ids.Default.peak_count, "value"),
            Input(self.page.ids.Default.mie_model, "value"),
            Input(self.page.ids.Default.mesf_values, "value"),
            Input(self.page.ids.Default.fcs_file_path, "value"),
            Input(self.page.ids.Default.default_gating_channel, "value"),
            Input(self.page.ids.Default.default_gating_threshold, "value"),
            Input(self.page.ids.Default.show_calibration_plot_by_default, "value"),
            Input(self.page.ids.Default.histogram_scale, "value"),
            Input(self.page.ids.Default.default_output_suffix, "value"),
            Input(self.page.ids.Default.operator_name, "value"),
            Input(self.page.ids.Default.instrument_name, "value"),
            Input(self.page.ids.Default.theme_mode, "value"),
            prevent_initial_call=True,
        )
        def clear_save_confirmation(*_args):
            return "", False

    def _build_profile_options(self) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []

        for profile_name in directories.list_profiles():
            profile_file_name = str(profile_name)
            profile_label = (
                profile_file_name[:-5]
                if profile_file_name.endswith(".json")
                else profile_file_name
            )
            options.append(
                {
                    "label": profile_label,
                    "value": profile_file_name,
                }
            )

        return options

    @staticmethod
    def _resolve_default_profile_value(profile_options: list[dict[str, str]]) -> Optional[str]:
        if not profile_options:
            return None

        available_values = {option["value"] for option in profile_options}

        if "default_profile.json" in available_values:
            return "default_profile.json"

        return profile_options[0]["value"]

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