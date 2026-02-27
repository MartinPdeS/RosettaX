from typing import Any, Optional, Sequence

import dash
import dash_bootstrap_components as dbc

from RosettaX.pages.runtime_config import get_runtime_config


class ParametersSection:
    """
    Render and manage the "Example Calculation Parameters" section.

    Responsibilities
    ----------------
    - Render a card containing a particle type selector and a dynamic parameter block.
    - Swap parameter blocks when the particle type changes.
    - Provide refractive index controls where presets populate a numeric input.

    Notes
    -----
    Callbacks are registered via `_parameters_register_callbacks()` and target the container
    `ids.Parameters.mie_model_parameters_container`.
    """

    def _parameters_get_layout(self) -> dbc.Card:
        """
        Build the card layout for the parameters section.

        Returns
        -------
        dbc.Card
            Card containing the particle type selector, the dynamic parameters block,
            and the calibrate button.
        """
        ids = self.ids

        return dbc.Card(
            [
                dbc.CardHeader("2. Set Example Calculation Parameters"),
                dbc.Collapse(
                    dbc.CardBody(
                        dash.html.Div(
                            [
                                self._parameters_build_particle_type_row(),
                                dash.html.Div(id=ids.Parameters.mie_model_parameters_container),
                                self._parameters_build_calibrate_button(),
                            ]
                        )
                    ),
                    id=self.ids.collapse_example,
                    is_open=True,
                ),
            ]
        )

    def _parameters_register_callbacks(self) -> None:
        """
        Register Dash callbacks for this section.

        Callback set
        ------------
        - Render parameter blocks when the particle type changes.
        - Apply refractive index presets by copying dropdown values into numeric inputs.

        Important
        ---------
        Call once during app startup.
        """
        self._parameters_register_render_callbacks()
        self._parameters_register_refractive_index_callbacks()

    def _parameters_register_render_callbacks(self) -> None:
        """
        Register callbacks that render the dynamic parameter block.
        """
        @dash.callback(
            dash.Output(self.ids.Parameters.mie_model_parameters_container, "children"),
            dash.Input(self.ids.Parameters.mie_model, "value"),
            prevent_initial_call=False,
        )
        def _parameters_render_mie_model_parameters(mie_model_value: Optional[str]):
            if mie_model_value == "Core/Shell Sphere":
                return self._parameters_build_core_shell_parameters_block()
            return self._parameters_build_solid_sphere_parameters_block()

    def _parameters_register_refractive_index_callbacks(self) -> None:
        """
        Register callbacks that apply preset dropdown selections to numeric RI inputs.

        Notes
        -----
        The preset dropdown is a convenience input.
        The numeric input always holds the effective value used by computation.
        """
        def _parameters_apply_preset_value(preset_value: Any, current_value: Any):
            if preset_value is None:
                return current_value
            return float(preset_value)

        @dash.callback(
            dash.Output(self.ids.Parameters.medium_index_custom, "value"),
            dash.Input(self.ids.Parameters.medium_index_source, "value"),
            dash.State(self.ids.Parameters.medium_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _parameters_apply_medium_preset(preset_value: Any, current_value: Any):
            return _parameters_apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.ids.Parameters.particle_index_custom, "value"),
            dash.Input(self.ids.Parameters.particle_index_source, "value"),
            dash.State(self.ids.Parameters.particle_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _parameters_apply_particle_preset(preset_value: Any, current_value: Any):
            return _parameters_apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.ids.Parameters.core_index_custom, "value"),
            dash.Input(self.ids.Parameters.core_index_source, "value"),
            dash.State(self.ids.Parameters.core_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _parameters_apply_core_preset(preset_value: Any, current_value: Any):
            return _parameters_apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.ids.Parameters.shell_index_custom, "value"),
            dash.Input(self.ids.Parameters.shell_index_source, "value"),
            dash.State(self.ids.Parameters.shell_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _parameters_apply_shell_preset(preset_value: Any, current_value: Any):
            return _parameters_apply_preset_value(preset_value, current_value)

    def _parameters_build_particle_type_row(self) -> dash.html.Div:
        """
        Build the "Particle Type" selector row.

        Returns
        -------
        dash.html.Div
            Inline row with label and dropdown selector.
        """
        ids = self.ids

        return self._parameters_inline_row(
            "Particle Type:",
            dash.dcc.Dropdown(
                id=ids.Parameters.mie_model,
                options=self._parameters_get_mie_model_options(),
                value="Solid Sphere",
                clearable=False,
                searchable=False,
                style={"width": "220px"},
            ),
            margin_top=False,
        )

    def _parameters_build_calibrate_button(self) -> dash.html.Button:
        """
        Build the calibrate button.

        Returns
        -------
        dash.html.Button
            Button that triggers the example calibration.
        """
        return dash.html.Button(
            "Calibrate",
            id=self.ids.calibrate_example_btn,
            n_clicks=0,
            style={"marginTop": "8px"},
        )

    def _parameters_get_mie_model_options(self) -> list[dict]:
        """
        Options for the particle type dropdown.

        Returns
        -------
        list[dict]
            Dash dropdown options.
        """
        return [
            {"label": "Solid Sphere", "value": "Solid Sphere"},
            {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
        ]

    def _parameters_build_common_medium_parameters_rows(self) -> list:
        """
        Build the shared medium refractive index row.

        Returns
        -------
        list
            Rows shared by all particle types.
        """
        runtime_config = get_runtime_config()

        return [
            self._parameters_refractive_index_picker(
                label="Medium Refractive Index:",
                preset_id=self.ids.Parameters.medium_index_source,
                value_id=self.ids.Parameters.medium_index_custom,
                default_value=getattr(runtime_config, "default_medium_index", 1.333),
                preset_options=self._parameters_get_medium_refractive_index_presets(),
            )
        ]

    def _parameters_get_medium_refractive_index_presets(self) -> list[dict]:
        """
        Preset options for medium refractive index.

        Returns
        -------
        list[dict]
            Dropdown preset options with numeric values.
        """
        return [
            {"label": "Water 1.333", "value": 1.333},
            {"label": "PBS 1.335", "value": 1.335},
        ]

    def _parameters_get_particle_refractive_index_presets(self) -> list[dict]:
        """
        Preset options for particle refractive index (solid sphere).

        Returns
        -------
        list[dict]
            Dropdown preset options with numeric values.
        """
        return [
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
            {"label": "PMMA 1.49", "value": 1.49},
            {"label": "Lipid 1.47", "value": 1.47},
        ]

    def _parameters_get_core_refractive_index_presets(self) -> list[dict]:
        """
        Preset options for core refractive index (core shell).

        Returns
        -------
        list[dict]
            Dropdown preset options with numeric values.
        """
        return [
            {"label": "Soybean oil 1.47", "value": 1.47},
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
        ]

    def _parameters_get_shell_refractive_index_presets(self) -> list[dict]:
        """
        Preset options for shell refractive index (core shell).

        Returns
        -------
        list[dict]
            Dropdown preset options with numeric values.
        """
        return [
            {"label": "Phospholipid 1.46", "value": 1.46},
            {"label": "Waterlike 1.33", "value": 1.33},
        ]

    def _parameters_build_solid_sphere_parameters_block(self) -> dash.html.Div:
        """
        Build the parameter block for a homogeneous solid sphere Mie model.

        Returns
        -------
        dash.html.Div
            Container holding the Solid Sphere input rows.
        """
        runtime_config = get_runtime_config()

        diameter_row = self._parameters_build_numeric_input_row(
            label="Particle Diameter (nm):",
            component_id=self.ids.Parameters.particle_diameter,
            placeholder="Particle Diameter (nm)",
            value=runtime_config.default_particle_diameter_nm,
            min_value=1,
            step=1,
            width_px=220,
        )

        particle_index_row = self._parameters_refractive_index_picker(
            label="Particle Refractive Index:",
            preset_id=self.ids.Parameters.particle_index_source,
            value_id=self.ids.Parameters.particle_index_custom,
            default_value=runtime_config.default_particle_index,
            preset_options=self._parameters_get_particle_refractive_index_presets(),
        )

        common_rows = self._parameters_build_common_medium_parameters_rows()

        return dash.html.Div([*common_rows, particle_index_row, diameter_row])

    def _parameters_build_core_shell_parameters_block(self) -> dash.html.Div:
        """
        Build the parameter block for a concentric core shell sphere Mie model.

        Returns
        -------
        dash.html.Div
            Container holding the Core Shell input rows.
        """
        runtime_config = get_runtime_config()

        common_rows = self._parameters_build_common_medium_parameters_rows()

        core_index_row = self._parameters_refractive_index_picker(
            label="Particle Core Refractive Index:",
            preset_id=self.ids.Parameters.core_index_source,
            value_id=self.ids.Parameters.core_index_custom,
            default_value=runtime_config.default_core_index,
            preset_options=self._parameters_get_core_refractive_index_presets(),
        )

        shell_index_row = self._parameters_refractive_index_picker(
            label="Particle Shell Refractive Index:",
            preset_id=self.ids.Parameters.shell_index_source,
            value_id=self.ids.Parameters.shell_index_custom,
            default_value=runtime_config.default_shell_index,
            preset_options=self._parameters_get_shell_refractive_index_presets(),
        )

        core_diameter_row = self._parameters_build_numeric_input_row(
            label="Particle Core Diameter (nm):",
            component_id=self.ids.Parameters.core_diameter,
            placeholder="Particle Core Diameter (nm)",
            value=runtime_config.default_core_diameter_nm,
            min_value=1,
            step=1,
            width_px=220,
        )

        shell_thickness_row = self._parameters_build_numeric_input_row(
            label="Particle Shell Thickness (nm):",
            component_id=self.ids.Parameters.shell_thickness,
            placeholder="Particle Shell Thickness (nm)",
            value=runtime_config.default_shell_thickness_nm,
            min_value=0,
            step=1,
            width_px=220,
        )

        return dash.html.Div(
            [
                *common_rows,
                core_index_row,
                shell_index_row,
                core_diameter_row,
                shell_thickness_row,
            ]
        )

    def _parameters_build_numeric_input_row(
        self,
        *,
        label: str,
        component_id: str,
        placeholder: str,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
        width_px: int = 220,
    ) -> dash.html.Div:
        """
        Build a standard numeric input row with consistent styling.

        Parameters
        ----------
        label:
            Row label.
        component_id:
            Dash component id for the input.
        placeholder:
            Input placeholder.
        value:
            Default value.
        min_value, max_value, step:
            Numeric constraints.
        width_px:
            Input width in pixels.

        Returns
        -------
        dash.html.Div
            A row containing the label and numeric input.
        """
        return self._parameters_inline_row(
            label,
            dash.dcc.Input(
                id=component_id,
                type="number",
                placeholder=placeholder,
                value=value,
                min=min_value,
                max=max_value,
                step=step,
                style={"width": f"{width_px}px"},
            ),
        )

    def _parameters_refractive_index_picker(
        self,
        *,
        label: str,
        preset_id: str,
        value_id: str,
        default_value: float,
        preset_options: Sequence[dict],
        preset_placeholder_label: str = "Select preset",
    ) -> dash.html.Div:
        """
        Build a refractive index input row.

        UI model
        --------
        - Preset dropdown is optional and only populates the numeric input when selected.
        - Numeric input always stores the effective value.

        Parameters
        ----------
        label:
            Row label.
        preset_id:
            Component id of the preset dropdown.
        value_id:
            Component id of the numeric value input.
        default_value:
            Default numeric value used at startup.
        preset_options:
            Dropdown options, each with "label" and "value".
        preset_placeholder_label:
            First dropdown option label that represents "no selection".

        Returns
        -------
        dash.html.Div
            A row containing the preset dropdown and numeric input.
        """
        preset_dropdown = dash.dcc.Dropdown(
            id=preset_id,
            options=[{"label": preset_placeholder_label, "value": None}, *list(preset_options)],
            value=None,
            clearable=False,
            searchable=False,
            style={"width": "220px", "marginRight": "10px"},
        )

        numeric_input = dash.dcc.Input(
            id=value_id,
            type="number",
            value=default_value,
            min=1.0,
            max=2.5,
            step=0.001,
            style={"width": "160px"},
        )

        control = dash.html.Div(
            [preset_dropdown, numeric_input],
            style={"display": "flex", "alignItems": "center"},
        )

        return self._parameters_inline_row(label, control)

    def _parameters_inline_row(self, label: str, control, *, margin_top: bool = True) -> dash.html.Div:
        """
        Create a single label + control row with strict alignment.

        Layout rules
        ------------
        - Fixed width label column
        - Flexible control column
        - Vertical centering
        - Full width alignment across all rows

        Parameters
        ----------
        label:
            Label text.
        control:
            Dash component or container used as the row control.
        margin_top:
            If False, removes top margin from the row.

        Returns
        -------
        dash.html.Div
            A row container.
        """
        base_style = {
            "display": "flex",
            "alignItems": "center",
            "width": "100%",
            "marginTop": "10px",
        }
        if not margin_top:
            base_style.pop("marginTop", None)

        label_style = {
            "width": "260px",
            "minWidth": "260px",
            "fontWeight": 500,
        }

        control_wrapper_style = {
            "flex": "1",
            "display": "flex",
            "alignItems": "center",
        }

        return dash.html.Div(
            [
                dash.html.Div(label, style=label_style),
                dash.html.Div(control, style=control_wrapper_style),
            ],
            style=base_style,
        )