
import json
from typing import Any

from dash import html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from RosettaX.pages.settings.ids import Ids
import dash

from RosettaX.pages.runtime_config import get_runtime_config, get_saved_profiles


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
                            options=[{"label": profile["filename"], "value": profile["filename"]} for profile in get_saved_profiles()],
                            value=None,
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
                            value=runtime_config.fluorescence_page_scattering_detector,
                        ),
                        html.Div("Default fluorescence page fluorescence detector:"),
                        dcc.Input(
                            id=Ids.Default.default_fluorescence_page_fluorescence_detector,
                            value=runtime_config.fluorescence_page_fluorescence_detector,
                        ),

                        html.Div("Default Medium Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_medium_index_input,
                            type="number",
                            value=runtime_config.default_medium_index,
                            step=0.001,
                        ),
                        html.Div("Default Core Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_core_index_input,
                            type="number",
                            value=runtime_config.default_core_index,
                            step=0.001,
                        ),
                        html.Div("Default Shell Refractive Index:"),
                        dcc.Input(
                            id=Ids.Default.default_shell_index_input,
                            type="number",
                            value=runtime_config.default_shell_index,
                            step=0.001,
                        ),
                        html.Div("Default Shell Thickness (nm):"),
                        dcc.Input(
                            id=Ids.Default.default_shell_thickness_input,
                            type="number",
                            value=runtime_config.default_shell_thickness_nm,
                            step=1,
                        ),
                        html.Div("Default Core Diameter (nm):"),
                        dcc.Input(
                            id=Ids.Default.default_core_diameter_input,
                            type="number",
                            value=runtime_config.default_core_diameter_nm,
                            step=1,
                        ),

                        html.Div("Default default particle diameter nm:"),
                        dcc.Input(
                            id=Ids.Default.default_particle_diameter_input,
                            type="number",
                            value=runtime_config.default_particle_diameter_nm,
                            step=1,
                        ),
                        html.Div("Default default particle index:"),
                        dcc.Input(
                            id=Ids.Default.default_particle_index_input,
                            type="number",
                            value=runtime_config.default_particle_index,
                            step=0.001,
                        ),

                        html.Div("Default max events for analysis:"),
                        dcc.Input(
                            id=Ids.Default.default_max_events_for_analysis_input,
                            value=runtime_config.max_events_for_analysis,
                        ),

                        html.Div("Default n bins for lots:"),
                        dcc.Input(
                            id=Ids.Default.default_n_bins_for_plots_input,
                            value=runtime_config.n_bins_for_plots,
                        ),

                        html.Div("Default peak count:"),
                        dcc.Input(
                            id=Ids.Default.default_peak_count_input,
                            value=runtime_config.default_peak_count,
                        ),

                        html.Div("Default MESF Values:"),
                        dcc.Input(
                            id=Ids.Default.default_mesf_values_input,
                            value=runtime_config.default_mesf_values,
                        ),
                        dbc.Button("Save Changes", id=Ids.Default.save_changes_button, color="primary", style={"marginTop": "10px"}),
                    ],
                    style=self.card_body_scroll,
                ),
            ]
        )
    print(Ids.Default.save_changes_button)
        
    def _edit_settings_register_callbacks(self) -> None:
        """
        Register callbacks for:
        """
        @callback(
            Input(Ids.Default.save_changes_button, "n_clicks"),
            State(Ids.NewProfile.new_profile_name_input, "value"),
            State(Ids.Default.default_fluorescence_page_scattering_detector, "value"),
            State(Ids.Default.default_fluorescence_page_fluorescence_detector, "value"),
            State(Ids.Default.default_medium_index_input, "value"),
            State(Ids.Default.default_core_index_input, "value"),
            State(Ids.Default.default_shell_index_input, "value"),
            State(Ids.Default.default_shell_thickness_input, "value"),
            State(Ids.Default.default_core_diameter_input, "value"),
            State(Ids.Default.default_particle_diameter_input, "value"),
            State(Ids.Default.default_particle_index_input, "value"),
            State(Ids.Default.default_max_events_for_analysis_input, "value"),
            State(Ids.Default.default_n_bins_for_plots_input, "value"),
            State(Ids.Default.default_peak_count_input, "value"),
            State(Ids.Default.default_mesf_values_input, "value"),
            prevent_initial_call=True,
        )
        def edit_settings(name: Any, *args) -> str:
            with open(f"RosettaX/data/settings/{name}.json", "r") as f:
                settings = json.load(f)
                keys = [
                    Ids.Default.default_fluorescence_page_scattering_detector,
                    Ids.Default.default_fluorescence_page_fluorescence_detector,
                    Ids.Default.default_medium_index_input,
                    Ids.Default.default_core_index_input,
                    Ids.Default.default_shell_index_input,
                    Ids.Default.default_shell_thickness_input,
                    Ids.Default.default_core_diameter_input,
                    Ids.Default.default_particle_diameter_input,
                    Ids.Default.default_particle_index_input,
                    Ids.Default.default_max_events_for_analysis_input,
                    Ids.Default.default_n_bins_for_plots_input,
                    Ids.Default.default_peak_count_input,
                    Ids.Default.default_mesf_values_input
                ]
                for key, value in zip(keys, args):
                    settings[key] = value
            with open(f"RosettaX/data/settings/{name}.json", "w") as f:
                json.dump(settings, f, indent=4)
            return f"Profile '{name}' updated with new default values."
        @callback(
            Output(Ids.Default.default_fluorescence_page_scattering_detector, "value"),
            Output(Ids.Default.default_fluorescence_page_fluorescence_detector, "value"),
            Output(Ids.Default.default_medium_index_input, "value"),
            Output(Ids.Default.default_core_index_input, "value"),
            Output(Ids.Default.default_shell_index_input, "value"),
            Output(Ids.Default.default_shell_thickness_input, "value"),
            Output(Ids.Default.default_core_diameter_input, "value"),
            Output(Ids.Default.default_particle_diameter_input, "value"),
            Output(Ids.Default.default_particle_index_input, "value"),
            Output(Ids.Default.default_max_events_for_analysis_input, "value"),
            Output(Ids.Default.default_n_bins_for_plots_input, "value"),
            Output(Ids.Default.default_peak_count_input, "value"),
            Output(Ids.Default.default_mesf_values_input, "value"),
            Input(Ids.Default.default_values_profile_dropdown, "value"),
            prevent_initial_call=True,
        )
        def load_profile_defaults(dropdown_value: str) -> str:
            profile = get_saved_profiles(filename=dropdown_value)[0]
            settings = profile["settings"]
            return (
                settings.get("fluorescence_page_scattering_detector", ""),
                settings.get("fluorescence_page_fluorescence_detector", ""),
                settings.get("default_medium_index", ""),
                settings.get("default_core_index", ""),
                settings.get("default_shell_index", ""),
                settings.get("default_shell_thickness_nm", ""),
                settings.get("default_core_diameter_nm", ""),
                settings.get("default_particle_diameter_nm", ""),
                settings.get("default_particle_index", ""),
                settings.get("max_events_for_analysis", ""),
                settings.get("n_bins_for_plots", ""),
                settings.get("default_peak_count", ""),
                settings.get("default_mesf_values", ""),
            )