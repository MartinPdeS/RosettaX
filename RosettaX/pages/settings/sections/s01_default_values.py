from typing import Any

from dash import html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.pages.settings.utils import list_setting_files, get_saved_profile, save_profile
import re


class DefaultSection:
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

        default_settings_section = dbc.Card(
            [
                dbc.CardHeader("Default Settings"),
                dbc.CardBody(
                    [
                        self._setting_row(
                            "Medium Refractive Index:",
                            self._persistent_input(
                                id=self.page.ids.Default.medium_refractive_index,
                                type="number",
                                value=runtime_config.Default.medium_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Core Refractive Index:",
                            self._persistent_input(
                                id=self.page.ids.Default.core_refractive_index,
                                type="number",
                                value=runtime_config.Default.core_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Shell Refractive Index:",
                            self._persistent_input(
                                id=self.page.ids.Default.shell_refractive_index,
                                type="number",
                                value=runtime_config.Default.shell_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Shell Thickness (nm):",
                            self._persistent_input(
                                id=self.page.ids.Default.shell_thickness_nm,
                                type="number",
                                value=runtime_config.Default.shell_thickness,
                                step=0.01,
                                min=0.01,
                                max=1000,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Core Diameter (nm):",
                            self._persistent_input(
                                id=self.page.ids.Default.core_diameter_nm,
                                type="number",
                                value=runtime_config.Default.core_diameter,
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
                                value=runtime_config.Default.particle_diameter,
                                step=1,
                                min=1,
                                max=1000,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Particle refractive index:",
                            self._persistent_input(
                                id=self.page.ids.Default.particle_refractive_index,
                                type="number",
                                value=runtime_config.Default.particle_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Max events for analysis:",
                            self._persistent_input(
                                id=self.page.ids.Default.max_events_for_analysis,
                                value=runtime_config.Default.max_events_for_analysis,
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
                                value=runtime_config.Default.n_bins_for_plots,
                                type="number",
                                step=10,
                                min=10,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Peak count:",
                            self._persistent_input(
                                id=self.page.ids.Default.peak_count,
                                value=runtime_config.Default.peak_count,
                                type="number",
                                step=1,
                                min=1,
                                max=10,
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
                            "MESF Values:",
                            self._persistent_input(
                                id=self.page.ids.Default.mesf_values,
                                value=runtime_config.Default.mesf_values,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "FCS File Path:",
                            self._persistent_input(
                                id=self.page.ids.Default.fcs_file_path,
                                value=runtime_config.Default.fcs_file_path,
                                style={"width": "100%"},
                            ),
                        ),
                    ]
                ),
            ],
            className="mb-4",
        )

        return dbc.Card(
            [
                dbc.CardHeader("Change Default Values"),
                dbc.CardBody(
                    [
                        html.P("Dropdown of saved profiles with option to load profile values into the inputs below."),
                        self._persistent_dropdown(
                            options=[
                                {"label": profile, "value": profile + ".json"}
                                for profile in list_setting_files()
                            ],
                            value="default_profile.json" if list_setting_files() else None,
                            placeholder="Select Profile",
                            id=self.page.ids.Default.values_profile_dropdown,
                        ),
                        html.P(
                            "Set default values for your experiments. These values will be used when no specific values are provided for a sample."
                        ),
                        html.Hr(),
                        default_settings_section,
                        dbc.Button(
                            "Save Changes",
                            id=self.page.ids.Default.save_changes_button,
                            color="primary",
                            style={"marginTop": "10px"},
                        ),
                        html.Div(
                            id=self.page.ids.Default.save_confirmation,
                            style={"marginTop": "10px", "color": "green"},
                        ),
                    ]
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
            Input(self.page.ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: str):
            settings = get_saved_profile(dropdown_value)
            data = (
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
            )
            runtime_config = RuntimeConfig()
            runtime_config.load_json(dropdown_value)
            return data

        @callback(
            Output(self.page.ids.Default.save_confirmation, "children"),
            Output("runtime-config-store", "data"),
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
            prevent_initial_call=True,
        )
        def edit_settings(name: Any, profile_target: str, *args) -> tuple[str, dict[str, Any]]:
            del name

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
            ]

            new_dict = {key: value for key, value in zip(keys, args)}

            new_dict["mesf_values"] = re.sub(
                r"[^\d,\s]",
                "",
                str(new_dict.get("mesf_values", "")),
            )

            save_profile(profile_target, new_dict)

            runtime_config = RuntimeConfig()
            runtime_config.update(**new_dict)

            runtime_config_data = {
                "medium_refractive_index": new_dict.get("medium_refractive_index"),
                "core_refractive_index": new_dict.get("core_refractive_index"),
                "shell_refractive_index": new_dict.get("shell_refractive_index"),
                "shell_thickness_nm": new_dict.get("shell_thickness_nm"),
                "core_diameter_nm": new_dict.get("core_diameter_nm"),
                "particle_diameter_nm": new_dict.get("particle_diameter_nm"),
                "particle_refractive_index": new_dict.get("particle_refractive_index"),
                "max_events_for_analysis": new_dict.get("max_events_for_analysis"),
                "n_bins_for_plots": new_dict.get("n_bins_for_plots"),
                "peak_count": new_dict.get("peak_count"),
                "mie_model": new_dict.get("mie_model"),
                "mesf_values": new_dict.get("mesf_values"),
                "fcs_file_path": new_dict.get("fcs_file_path"),
            }

            return "Changes saved!", runtime_config_data

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