# -*- coding: utf-8 -*-

from typing import Any, Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.pages.settings.utils import get_saved_profile, save_profile
from RosettaX.utils import directories
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.casting import _as_float, _as_float_list


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

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

    def _get_layout(self):
        runtime_config = self._get_default_runtime_config()

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
                    dcc.Dropdown(
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
                        value=self._format_float_list_for_input(
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
                        value=self._format_float_list_for_input(
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
                        value=self._format_float_list_for_input(
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
                        value=self._format_float_list_for_input(
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
                        value=self._coerce_optional_string(
                            runtime_config.get_path("calibration.default_gating_channel", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default gating threshold:",
                    self._persistent_input(
                        id=self.page.ids.Default.default_gating_threshold,
                        value=self._coerce_optional_string(
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

    def _build_miscellaneous_block(self, runtime_config: RuntimeConfig) -> html.Div:
        return html.Div(
            [
                html.H5("Miscellaneous"),
                self._setting_row(
                    "Default Fluorescence FCS file path:",
                    self._persistent_input(
                        id=self.page.ids.Default.fluorescence_fcs_file_path,
                        value=self._coerce_optional_string(
                            runtime_config.get_path("files.fluorescence_fcs_file_path", default=None)
                        ) or "",
                        style={"width": "100%"},
                    ),
                ),
                self._setting_row(
                    "Default Scattering FCS file path:",
                    self._persistent_input(
                        id=self.page.ids.Default.scattering_fcs_file_path,
                        value=self._coerce_optional_string(
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
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: Optional[str]):
            if not dropdown_value:
                return tuple([dash.no_update] * 24)

            saved_profile = get_saved_profile(dropdown_value) or {}
            runtime_config = RuntimeConfig.from_dict(saved_profile)
            flattened_profile = self._flatten_runtime_config(runtime_config)

            return (
                flattened_profile.get("medium_refractive_index"),
                flattened_profile.get("core_refractive_index"),
                flattened_profile.get("shell_refractive_index"),
                self._format_float_list_for_input(flattened_profile.get("shell_thickness_nm")),
                self._format_float_list_for_input(flattened_profile.get("core_diameter_nm")),
                self._format_float_list_for_input(flattened_profile.get("particle_diameter_nm")),
                flattened_profile.get("particle_refractive_index"),
                flattened_profile.get("wavelength_nm"),
                flattened_profile.get("max_events_for_analysis"),
                flattened_profile.get("n_bins_for_plots"),
                flattened_profile.get("peak_count"),
                flattened_profile.get("mie_model"),
                self._format_float_list_for_input(flattened_profile.get("mesf_values")),
                flattened_profile.get("fluorescence_fcs_file_path") or "",
                flattened_profile.get("scattering_fcs_file_path") or "",
                flattened_profile.get("default_gating_channel") or "",
                self._coerce_optional_string(flattened_profile.get("default_gating_threshold")) or "",
                "yes" if flattened_profile.get("show_calibration_plot_by_default") else "no",
                flattened_profile.get("histogram_scale"),
                flattened_profile.get("default_output_suffix") or "",
                flattened_profile.get("operator_name") or "",
                flattened_profile.get("instrument_name") or "",
                flattened_profile.get("theme_mode"),
                "yes" if flattened_profile.get("show_graphs") else "no",
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
            prevent_initial_call=True,
        )
        def edit_settings(n_clicks: Any, profile_target: str, *args):
            if dash.ctx.triggered_id != self.page.ids.Default.save_changes_button:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if not n_clicks:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            try:
                flat_runtime_payload = self._build_flat_runtime_payload_from_form_values(args)
                nested_profile_payload = self._build_nested_profile_payload(flat_runtime_payload)

                if not profile_target:
                    return (
                        "No target profile selected.",
                        dash.no_update,
                        True,
                        "danger",
                    )

                save_profile(profile_target, nested_profile_payload)

                return (
                    f"Saved profile: {profile_target}",
                    nested_profile_payload,
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
            prevent_initial_call=True,
        )
        def clear_save_confirmation(*_args):
            return "", False

    def _build_profile_options(self) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []

        for profile_name in directories.list_profiles():
            profile_file_name = str(profile_name)
            profile_label = profile_file_name[:-5] if profile_file_name.endswith(".json") else profile_file_name
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

    def _build_flat_runtime_payload_from_form_values(self, form_values: tuple[Any, ...]) -> dict[str, Any]:
        keys = [
            "medium_refractive_index",
            "core_refractive_index",
            "shell_refractive_index",
            "shell_thickness_nm",
            "core_diameter_nm",
            "particle_diameter_nm",
            "particle_refractive_index",
            "wavelength_nm",
            "max_events_for_analysis",
            "n_bins_for_plots",
            "peak_count",
            "mie_model",
            "mesf_values",
            "fluorescence_fcs_file_path",
            "scattering_fcs_file_path",
            "default_gating_channel",
            "default_gating_threshold",
            "show_calibration_plot_by_default",
            "histogram_scale",
            "default_output_suffix",
            "operator_name",
            "instrument_name",
            "theme_mode",
            "show_graphs",
        ]

        flat_payload = {key: value for key, value in zip(keys, form_values)}

        flat_payload["mesf_values"] = self._parse_float_list(flat_payload.get("mesf_values", ""))
        flat_payload["particle_diameter_nm"] = self._parse_float_list(flat_payload.get("particle_diameter_nm", ""))
        flat_payload["core_diameter_nm"] = self._parse_float_list(flat_payload.get("core_diameter_nm", ""))
        flat_payload["shell_thickness_nm"] = self._parse_float_list(flat_payload.get("shell_thickness_nm", ""))

        flat_payload["show_graphs"] = (
            str(flat_payload.get("show_graphs", "yes")).strip().lower() == "yes"
        )
        flat_payload["show_calibration_plot_by_default"] = (
            str(flat_payload.get("show_calibration_plot_by_default", "no")).strip().lower() == "yes"
        )

        flat_payload["wavelength_nm"] = self._coerce_optional_number(flat_payload.get("wavelength_nm"))
        flat_payload["medium_refractive_index"] = self._coerce_optional_number(flat_payload.get("medium_refractive_index"))
        flat_payload["core_refractive_index"] = self._coerce_optional_number(flat_payload.get("core_refractive_index"))
        flat_payload["shell_refractive_index"] = self._coerce_optional_number(flat_payload.get("shell_refractive_index"))
        flat_payload["particle_refractive_index"] = self._coerce_optional_number(flat_payload.get("particle_refractive_index"))
        flat_payload["max_events_for_analysis"] = self._coerce_optional_integer(flat_payload.get("max_events_for_analysis"))
        flat_payload["n_bins_for_plots"] = self._coerce_optional_integer(flat_payload.get("n_bins_for_plots"))
        flat_payload["peak_count"] = self._coerce_optional_integer(flat_payload.get("peak_count"))

        flat_payload["fluorescence_fcs_file_path"] = self._coerce_optional_string(
            flat_payload.get("fluorescence_fcs_file_path")
        )
        flat_payload["scattering_fcs_file_path"] = self._coerce_optional_string(
            flat_payload.get("scattering_fcs_file_path")
        )
        flat_payload["default_gating_channel"] = self._coerce_optional_string(
            flat_payload.get("default_gating_channel")
        )
        flat_payload["default_gating_threshold"] = self._coerce_optional_string(
            flat_payload.get("default_gating_threshold")
        )
        flat_payload["default_output_suffix"] = self._coerce_optional_string(
            flat_payload.get("default_output_suffix")
        )
        flat_payload["operator_name"] = self._coerce_optional_string(
            flat_payload.get("operator_name")
        )
        flat_payload["instrument_name"] = self._coerce_optional_string(
            flat_payload.get("instrument_name")
        )
        flat_payload["histogram_scale"] = self._coerce_optional_string(
            flat_payload.get("histogram_scale")
        )
        flat_payload["mie_model"] = self._coerce_optional_string(
            flat_payload.get("mie_model")
        )
        flat_payload["theme_mode"] = self._coerce_optional_string(
            flat_payload.get("theme_mode")
        )

        return flat_payload

    def _build_nested_profile_payload(self, flat_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "files": {
                "fluorescence_fcs_file_path": flat_payload.get("fluorescence_fcs_file_path"),
                "scattering_fcs_file_path": flat_payload.get("scattering_fcs_file_path"),
            },
            "page_defaults": {
                "fluorescence": {
                    "scattering_detector": None,
                    "fluorescence_detector": None,
                }
            },
            "optics": {
                "wavelength_nm": flat_payload.get("wavelength_nm"),
                "medium_refractive_index": flat_payload.get("medium_refractive_index"),
            },
            "particle_model": {
                "mie_model": flat_payload.get("mie_model"),
                "particle_refractive_index": flat_payload.get("particle_refractive_index"),
                "core_refractive_index": flat_payload.get("core_refractive_index"),
                "shell_refractive_index": flat_payload.get("shell_refractive_index"),
                "particle_diameter_nm": flat_payload.get("particle_diameter_nm"),
                "core_diameter_nm": flat_payload.get("core_diameter_nm"),
                "shell_thickness_nm": flat_payload.get("shell_thickness_nm"),
            },
            "calibration": {
                "mesf_values": flat_payload.get("mesf_values"),
                "peak_count": flat_payload.get("peak_count"),
                "max_events_for_analysis": flat_payload.get("max_events_for_analysis"),
                "n_bins_for_plots": flat_payload.get("n_bins_for_plots"),
                "default_gating_channel": flat_payload.get("default_gating_channel"),
                "default_gating_threshold": flat_payload.get("default_gating_threshold"),
                "show_calibration_plot_by_default": flat_payload.get("show_calibration_plot_by_default"),
                "histogram_scale": flat_payload.get("histogram_scale"),
                "default_output_suffix": flat_payload.get("default_output_suffix"),
            },
            "metadata": {
                "operator_name": flat_payload.get("operator_name"),
                "instrument_name": flat_payload.get("instrument_name"),
            },
            "app": {
                "theme_mode": flat_payload.get("theme_mode"),
                "show_graphs": flat_payload.get("show_graphs"),
            },
        }

    def _flatten_runtime_config(self, runtime_config: RuntimeConfig) -> dict[str, Any]:
        return {
            "fluorescence_fcs_file_path": runtime_config.get_path("files.fluorescence_fcs_file_path", default=None),
            "scattering_fcs_file_path": runtime_config.get_path("files.scattering_fcs_file_path", default=None),
            "fluorescence_page_scattering_detector": runtime_config.get_path(
                "page_defaults.fluorescence.scattering_detector",
                default=None,
            ),
            "fluorescence_page_fluorescence_detector": runtime_config.get_path(
                "page_defaults.fluorescence.fluorescence_detector",
                default=None,
            ),
            "wavelength_nm": runtime_config.get_float("optics.wavelength_nm", default=None),
            "medium_refractive_index": runtime_config.get_float("optics.medium_refractive_index", default=None),
            "core_refractive_index": runtime_config.get_float("particle_model.core_refractive_index", default=None),
            "shell_refractive_index": runtime_config.get_float("particle_model.shell_refractive_index", default=None),
            "shell_thickness_nm": runtime_config.get_path("particle_model.shell_thickness_nm", default=[]),
            "core_diameter_nm": runtime_config.get_path("particle_model.core_diameter_nm", default=[]),
            "particle_diameter_nm": runtime_config.get_path("particle_model.particle_diameter_nm", default=[]),
            "particle_refractive_index": runtime_config.get_float(
                "particle_model.particle_refractive_index",
                default=None,
            ),
            "max_events_for_analysis": runtime_config.get_int("calibration.max_events_for_analysis", default=None),
            "n_bins_for_plots": runtime_config.get_int("calibration.n_bins_for_plots", default=None),
            "peak_count": runtime_config.get_int("calibration.peak_count", default=None),
            "mie_model": runtime_config.get_str("particle_model.mie_model", default=""),
            "mesf_values": runtime_config.get_path("calibration.mesf_values", default=[]),
            "default_gating_channel": runtime_config.get_path("calibration.default_gating_channel", default=None),
            "default_gating_threshold": runtime_config.get_path("calibration.default_gating_threshold", default=None),
            "show_calibration_plot_by_default": runtime_config.get_bool(
                "calibration.show_calibration_plot_by_default",
                default=False,
            ),
            "histogram_scale": runtime_config.get_str("calibration.histogram_scale", default="log"),
            "default_output_suffix": runtime_config.get_str("calibration.default_output_suffix", default=""),
            "operator_name": runtime_config.get_str("metadata.operator_name", default=""),
            "instrument_name": runtime_config.get_str("metadata.instrument_name", default=""),
            "theme_mode": runtime_config.get_theme_mode(default="dark"),
            "show_graphs": runtime_config.get_show_graphs(default=False),
        }

    @staticmethod
    def _parse_float_list(value: Any) -> list[float]:
        parsed_values = _as_float_list(value)
        return [float(item) for item in parsed_values.tolist()]

    @staticmethod
    def _coerce_optional_number(value: Any) -> Optional[float]:
        parsed_value = _as_float(value)
        if parsed_value is None:
            return None
        return float(parsed_value)

    @staticmethod
    def _coerce_optional_integer(value: Any) -> Optional[int]:
        parsed_value = _as_float(value)
        if parsed_value is None:
            return None
        return int(parsed_value)

    @staticmethod
    def _coerce_optional_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        resolved_value = str(value).strip()
        return resolved_value if resolved_value else None

    def _format_float_list_for_input(self, value: Any) -> str:
        parsed_values = _as_float_list(value)

        if parsed_values.size == 0:
            return ""

        return ", ".join(f"{float(item):.6g}" for item in parsed_values)

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