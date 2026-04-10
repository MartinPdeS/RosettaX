from typing import Any

from dash import html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from RosettaX.pages.settings.ids import Ids

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.pages.settings.utils import list_setting_files, get_saved_profile, save_profile
import re


class DefaultSection():
    def __init__(self, page) -> None:
        self.page = page

    def _get_layout(self):
        runtime_config = RuntimeConfig()

        default_settings_section = dbc.Card(
            [
                dbc.CardHeader("Default Settings"),
                dbc.CardBody(
                    [
                        self._setting_row(
                            "Medium Refractive Index:",
                            dcc.Input(
                                id=Ids.Default.medium_refractive_index,
                                type="number",
                                value=runtime_config.medium_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Core Refractive Index:",
                            dcc.Input(
                                id=Ids.Default.core_refractive_index,
                                type="number",
                                value=runtime_config.core_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Shell Refractive Index:",
                            dcc.Input(
                                id=Ids.Default.shell_refractive_index,
                                type="number",
                                value=runtime_config.shell_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Shell Thickness (nm):",
                            dcc.Input(
                                id=Ids.Default.shell_thickness_nm,
                                type="number",
                                value=runtime_config.shell_thickness_nm,
                                step=0.01,
                                min=0.01,
                                max=1000,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Core Diameter (nm):",
                            dcc.Input(
                                id=Ids.Default.core_diameter_nm,
                                type="number",
                                value=runtime_config.core_diameter_nm,
                                step=0.01,
                                min=0.01,
                                max=1000,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Particle diameter (nm):",
                            dcc.Input(
                                id=Ids.Default.particle_diameter_nm,
                                type="number",
                                value=runtime_config.particle_diameter_nm,
                                step=1,
                                min=1,
                                max=1000,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Particle refractive index:",
                            dcc.Input(
                                id=Ids.Default.particle_refractive_index,
                                type="number",
                                value=runtime_config.particle_refractive_index,
                                step=0.001,
                                min=0.001,
                                max=2.5,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Max events for analysis:",
                            dcc.Input(
                                id=Ids.Default.max_events_for_analysis,
                                value=runtime_config.max_events_for_analysis,
                                type="number",
                                step=1,
                                min=1,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Number of bins for plots:",
                            dcc.Input(
                                id=Ids.Default.n_bins_for_plots,
                                value=runtime_config.n_bins_for_plots,
                                type="number",
                                step=10,
                                min=10,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "Peak count:",
                            dcc.Input(
                                id=Ids.Default.peak_count,
                                value=runtime_config.peak_count,
                                type="number",
                                step=1,
                                min=1,
                                max=10,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "MESF Values:",
                            dcc.Input(
                                id=Ids.Default.mesf_values,
                                value=runtime_config.mesf_values,
                                style={"width": "100%"},
                            ),
                        ),
                        self._setting_row(
                            "FCS File Path:",
                            dcc.Input(
                                id=Ids.Default.fcs_file_path,
                                value=runtime_config.fcs_file_path,
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
                        dcc.Dropdown(
                            options=[{"label": profile, "value": profile + '.json'} for profile in list_setting_files()],
                            value="default_profile.json" if list_setting_files() else None,
                            placeholder="Select Profile",
                            id=Ids.Default.values_profile_dropdown,
                        ),
                        html.P(
                            "Set default values for your experiments. These values will be used when no specific values are provided for a sample."
                        ),
                        html.Hr(),
                        default_settings_section,
                        dbc.Button(
                            "Save Changes",
                            id=Ids.Default.save_changes_button,
                            color="primary",
                            style={"marginTop": "10px"},
                        ),
                        html.Div(
                            id=Ids.Default.save_confirmation,
                            style={"marginTop": "10px", "color": "green"},
                        ),
                    ]
                ),
            ]
        )


    def _register_callbacks(self) -> None:
        """
        Register callbacks for:
        """

        @callback(
            Output(Ids.Default.medium_refractive_index, "value"),
            Output(Ids.Default.core_refractive_index, "value"),
            Output(Ids.Default.shell_refractive_index, "value"),
            Output(Ids.Default.shell_thickness_nm, "value"),
            Output(Ids.Default.core_diameter_nm, "value"),
            Output(Ids.Default.particle_diameter_nm, "value"),
            Output(Ids.Default.particle_refractive_index, "value"),
            Output(Ids.Default.max_events_for_analysis, "value"),
            Output(Ids.Default.n_bins_for_plots, "value"),
            Output(Ids.Default.peak_count, "value"),
            Output(Ids.Default.mesf_values, "value"),
            Output(Ids.Default.fcs_file_path, "value"),
            Input(Ids.Default.values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: str) -> str:
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
                settings.get("mesf_values", ""),
                settings.get("fcs_file_path", ""),
            )
            runtime_config = RuntimeConfig()
            runtime_config.load_json(dropdown_value)
            return data #, dropdown_value, settings


        @callback(
            Output(Ids.Default.save_confirmation, "children"),
            Input(Ids.Default.save_changes_button, "n_clicks"),
            State(Ids.Default.values_profile_dropdown, "value"),
            State(Ids.Default.medium_refractive_index, "value"),
            State(Ids.Default.core_refractive_index, "value"),
            State(Ids.Default.shell_refractive_index, "value"),
            State(Ids.Default.shell_thickness_nm, "value"),
            State(Ids.Default.core_diameter_nm, "value"),
            State(Ids.Default.particle_diameter_nm, "value"),
            State(Ids.Default.particle_refractive_index, "value"),
            State(Ids.Default.max_events_for_analysis, "value"),
            State(Ids.Default.n_bins_for_plots, "value"),
            State(Ids.Default.peak_count, "value"),
            State(Ids.Default.mesf_values, "value"),
            State(Ids.Default.fcs_file_path, "value"),
            prevent_initial_call=True,
        )
        def edit_settings(name: Any, profile_target: str, *args) -> str:
            new_dict = {}
            keys = [
                Ids.Default.medium_refractive_index,
                Ids.Default.core_refractive_index,
                Ids.Default.shell_refractive_index,
                Ids.Default.shell_thickness_nm,
                Ids.Default.core_diameter_nm,
                Ids.Default.particle_diameter_nm,
                Ids.Default.particle_refractive_index,
                Ids.Default.max_events_for_analysis,
                Ids.Default.n_bins_for_plots,
                Ids.Default.peak_count,
                Ids.Default.mesf_values,
                Ids.Default.fcs_file_path,
            ]
            for key, value in zip(keys, args):
                new_dict[key] = value

            new_dict[Ids.Default.mesf_values] = re.sub(r'[^\d,\s]', '', new_dict[Ids.Default.mesf_values])

            save_profile(profile_target, new_dict)
            runtime_config = RuntimeConfig()
            runtime_config.update(**new_dict)
            return "Changes saved!"


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