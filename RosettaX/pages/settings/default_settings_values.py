
import json
from typing import Any

from dash import html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from RosettaX.pages.settings.ids import Ids
import dash

from RosettaX.pages.runtime_config import get_runtime_config, list_setting_files, get_saved_profile, save_profile
import re


class DefaultSettingValues():
    def __init__(self) -> None:
        pass

    def _edit_settings_get_layout(self):
        """
        Layout for the Default Values page.
        This page allows users to set default values for their experiments.
        """
        runtime_config = get_runtime_config()

        return dbc.Card(
            [
                dbc.CardHeader("Change Default Values"),
                dbc.CardBody(
                    [
                        html.P("Dropdown of saved profiles with option to load profile values into the inputs below."),
                        dcc.Dropdown(
                            options=[{"label": profile["filename"], "value": profile["filename"]} for profile in list_setting_files()],
                            value=list_setting_files()[0]["filename"] if list_setting_files() else None,
                            placeholder="Select Profile",
                            id=Ids.Default.default_values_profile_dropdown,
                        ),
                        html.P(
                            "Set default values for your experiments. These values will be used when no specific values are provided for a sample."
                        ),
                        html.Div(),
                        
                        html.Div("Default fluorescence page scattering detector:"),
                        dcc.Input(
                            id=Ids.Default.default_fluorescence_page_scattering_detector,
                            value=runtime_config.default_fluorescence_page_scattering_detector,
                        ),
                        html.Div("Default fluorescence page fluorescence detector:"),
                        dcc.Input(
                            id=Ids.Default.default_fluorescence_page_fluorescence_detector,
                            value=runtime_config.default_fluorescence_page_fluorescence_detector,
                        ),

                        html.Div("Default Medium Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_medium_index,
                            type="number",
                            value=runtime_config.default_medium_index,
                            step=0.001,
                            min=0.001,
                            max=2.5
                        ),
                        html.Div("Default Core Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_core_index,
                            type="number",
                            value=runtime_config.default_core_index,
                            step=0.001,
                            min=0.001,
                            max=2.5
                        ),
                        html.Div("Default Shell Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_shell_index,
                            type="number",
                            value=runtime_config.default_shell_index,
                            step=0.001,
                            min=0.001,
                            max=2.5
                        ),
                        html.Div("Default Shell Thickness (nm):"),
                        dcc.Input(
                            id=Ids.Default.default_shell_thickness_nm,
                            type="number",
                            value=runtime_config.default_shell_thickness_nm,
                            step=0.01,
                            min=0.01, 
                            max=1000
                        ),
                        html.Div("Default Core Diameter (nm):"),
                        dcc.Input(
                            id=Ids.Default.default_core_diameter_nm,
                            type="number",
                            value=runtime_config.default_core_diameter_nm,
                            step=0.01,
                            min=0.01,
                            max=1000
                        ),

                        html.Div("Default particle diameter nm:"),
                        dcc.Input(
                            id=Ids.Default.default_particle_diameter_nm,
                            type="number",
                            value=runtime_config.default_particle_diameter_nm,
                            step=1,
                            min=1,
                            max=1000
                        ),
                        html.Div("Default particle index:"),
                        dcc.Input(
                            id=Ids.Default.default_particle_index,
                            type="number",
                            value=runtime_config.default_particle_index,
                            step=0.001,
                            min=0.001,
                            max=2.5
                        ),

                        html.Div("Default max events for analysis:"),
                        dcc.Input(
                            id=Ids.Default.default_max_events_for_analysis,
                            value=runtime_config.default_max_events_for_analysis,
                            type="number",
                            step=1,
                            min=1,
                        ),

                        html.Div("Default n bins for lots:"),
                        dcc.Input(
                            id=Ids.Default.default_n_bins_for_plots,
                            value=runtime_config.default_n_bins_for_plots,
                            type="number",
                            step=10,
                            min=10,
                        ),

                        html.Div("Default peak count:"),
                        dcc.Input(
                            id=Ids.Default.default_peak_count,
                            value=runtime_config.default_peak_count,
                            type="number", 
                            step=1,
                            min=1, 
                            max=10
                        ),

                        html.Div("Default MESF Values:"),
                        dcc.Input(
                            id=Ids.Default.default_mesf_values,
                            value=runtime_config.default_mesf_values,
                        ),
                        html.Br(),
                        html.Br(),
                        dbc.CardHeader("Advanced Settings"),
                        dbc.CardBody(
                            [
                                html.Div("Default FCS File Path:"),
                                dcc.Input(
                                    id=Ids.Default.default_fcs_file_path,
                                    value=runtime_config.default_fcs_file_path,
                                ),

                                html.Div("Debug Mode:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_debug,
                                    value=runtime_config.default_debug,
                                    options=[
                                        {"label": "True", "value": True},
                                        {"label": "False", "value": False}
                                    ]
                                ),

                                html.Div("default_fluorescence_show_scattering_controls"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_show_scattering_controls,
                                    value=runtime_config.default_fluorescence_show_scattering_controls,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),

                                html.Div("default_fluorescence_show_threshold_controls:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_show_threshold_controls,
                                    value=runtime_config.default_fluorescence_show_threshold_controls,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),

                                html.Div("default_fluorescence_show_fluorescence_controls:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_show_fluorescence_controls,
                                    value=runtime_config.default_fluorescence_show_fluorescence_controls,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),

                                html.Div("default_fluorescence_debug_scattering:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_debug_scattering,
                                    value=runtime_config.default_fluorescence_debug_scattering,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),

                                html.Div("default_fluorescence_debug_fluorescence:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_debug_fluorescence,
                                    value=runtime_config.default_fluorescence_debug_fluorescence,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),

                                html.Div("default_fluorescence_debug_load:"),
                                dcc.Dropdown(
                                    id=Ids.Default.default_fluorescence_debug_load,
                                    value=runtime_config.default_fluorescence_debug_load,
                                    options=[{"label": "True", "value": True}, {"label": "False", "value": False}]
                                ),
                            ],
                            style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "5px"},
                        ),

                        dbc.Button("Save Changes", id=Ids.Default.default_save_changes_button, color="primary", style={"marginTop": "10px"}),
                        html.Div(id=Ids.Default.default_save_confirmation, style={"marginTop": "10px", "color": "green"}),
                    ],
                    style=self.card_body_scroll,
                ),
            ]
        )
        
    def _edit_settings_register_callbacks(self) -> None:
        """
        Register callbacks for:
        """

        @callback(
            Output(Ids.Default.default_fluorescence_page_scattering_detector, "value"),
            Output(Ids.Default.default_fluorescence_page_fluorescence_detector, "value"),
            Output(Ids.Default.default_medium_index, "value"),
            Output(Ids.Default.default_core_index, "value"),
            Output(Ids.Default.default_shell_index, "value"),
            Output(Ids.Default.default_shell_thickness_nm, "value"),
            Output(Ids.Default.default_core_diameter_nm, "value"),
            Output(Ids.Default.default_particle_diameter_nm, "value"),
            Output(Ids.Default.default_particle_index, "value"),
            Output(Ids.Default.default_max_events_for_analysis, "value"),
            Output(Ids.Default.default_n_bins_for_plots, "value"),
            Output(Ids.Default.default_peak_count, "value"),
            Output(Ids.Default.default_mesf_values, "value"),
            Output(Ids.Default.default_fcs_file_path, "value"),
            Output(Ids.Default.default_debug, "value"),
            Output(Ids.Default.default_fluorescence_show_scattering_controls, "value"),
            Output(Ids.Default.default_fluorescence_show_threshold_controls, "value"),
            Output(Ids.Default.default_fluorescence_show_fluorescence_controls, "value"),
            Output(Ids.Default.default_fluorescence_debug_scattering, "value"),
            Output(Ids.Default.default_fluorescence_debug_fluorescence, "value"),
            Output(Ids.Default.default_fluorescence_debug_load, "value"),

            Input(Ids.Default.default_values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: str) -> str:
            settings = get_saved_profile(dropdown_value)
            return (
                settings.get("default_fluorescence_page_scattering_detector", ""),
                settings.get("default_fluorescence_page_fluorescence_detector", ""),
                settings.get("default_medium_index", ""),
                settings.get("default_core_index", ""),
                settings.get("default_shell_index", ""),
                settings.get("default_shell_thickness_nm", ""),
                settings.get("default_core_diameter_nm", ""),
                settings.get("default_particle_diameter_nm", ""),
                settings.get("default_particle_index", ""),
                settings.get("default_max_events_for_analysis", ""),
                settings.get("default_n_bins_for_plots", ""),
                settings.get("default_peak_count", ""),
                settings.get("default_mesf_values", ""),
                settings.get("default_fcs_file_path", ""),
                settings.get("default_debug", ""),
                settings.get("default_fluorescence_show_scattering_controls", ""),
                settings.get("default_fluorescence_show_threshold_controls", ""),
                settings.get("default_fluorescence_show_fluorescence_controls", ""),
                settings.get("default_fluorescence_debug_scattering", ""),
                settings.get("default_fluorescence_debug_fluorescence", ""),
                settings.get("default_fluorescence_debug_load", ""),
            )

        
        @callback(
            Input(Ids.Default.default_save_changes_button, "n_clicks"),
            State(Ids.Default.default_values_profile_dropdown, "value"),

            State(Ids.Default.default_fluorescence_page_scattering_detector, "value"),
            State(Ids.Default.default_fluorescence_page_fluorescence_detector, "value"),
            State(Ids.Default.default_medium_index, "value"),
            State(Ids.Default.default_core_index, "value"),
            State(Ids.Default.default_shell_index, "value"),
            State(Ids.Default.default_shell_thickness_nm, "value"),
            State(Ids.Default.default_core_diameter_nm, "value"),
            State(Ids.Default.default_particle_diameter_nm, "value"),
            State(Ids.Default.default_particle_index, "value"),
            State(Ids.Default.default_max_events_for_analysis, "value"),
            State(Ids.Default.default_n_bins_for_plots, "value"),
            State(Ids.Default.default_peak_count, "value"),
            State(Ids.Default.default_mesf_values, "value"),
            State(Ids.Default.default_fcs_file_path, "value"),
            State(Ids.Default.default_debug, "value"),
            State(Ids.Default.default_fluorescence_show_scattering_controls, "value"),
            State(Ids.Default.default_fluorescence_show_threshold_controls, "value"),
            State(Ids.Default.default_fluorescence_show_fluorescence_controls, "value"),
            State(Ids.Default.default_fluorescence_debug_scattering, "value"),
            State(Ids.Default.default_fluorescence_debug_fluorescence, "value"),
            State(Ids.Default.default_fluorescence_debug_load, "value"),
            prevent_initial_call=True,
        )
        def edit_settings(name: Any, profile_target: str, *args) -> str:
            print(name, profile_target, args)
            new_dict = {}
            keys = [
                Ids.Default.default_fluorescence_page_scattering_detector,
                Ids.Default.default_fluorescence_page_fluorescence_detector,
                Ids.Default.default_medium_index,
                Ids.Default.default_core_index,
                Ids.Default.default_shell_index,
                Ids.Default.default_shell_thickness_nm,
                Ids.Default.default_core_diameter_nm,
                Ids.Default.default_particle_diameter_nm,
                Ids.Default.default_particle_index,
                Ids.Default.default_max_events_for_analysis,
                Ids.Default.default_n_bins_for_plots,
                Ids.Default.default_peak_count,
                Ids.Default.default_mesf_values,
                Ids.Default.default_fcs_file_path,
                Ids.Default.default_debug,
                Ids.Default.default_fluorescence_show_scattering_controls,
                Ids.Default.default_fluorescence_show_threshold_controls,
                Ids.Default.default_fluorescence_show_fluorescence_controls,
                Ids.Default.default_fluorescence_debug_scattering,
                Ids.Default.default_fluorescence_debug_fluorescence,
                Ids.Default.default_fluorescence_debug_load,
            ]
            for key, value in zip(keys, args):
                new_dict[key] = value
            
            new_dict[Ids.Default.default_mesf_values] = re.sub(r'[^\d,\s]', '', new_dict[Ids.Default.default_mesf_values])

            save_profile(profile_target, new_dict)