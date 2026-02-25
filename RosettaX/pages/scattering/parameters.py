from typing import Optional

import dash_bootstrap_components as dbc
import dash
from RosettaX.pages.runtime_config import get_runtime_config

class ParametersSection:
    """
    Render and manage the "Example Calculation Parameters" section.

    Responsibilities
    ----------------
    - Render a card containing a Mie model selector and a dynamic parameter block.
    - Update the parameter block based on the selected Mie model.

    Notes
    -----
    The callback is registered via `register_callbacks()` and targets the container
    `ids.mie_model_parameters_container`.
    """
    def _parameters_get_layout(self) -> dbc.Card:
        """
        Create the card layout for the parameters section.

        The dynamic subsection is rendered into `ids.mie_model_parameters_container`
        by a callback.

        Returns
        -------
        dbc.Card
            Dash Bootstrap card containing the controls for this section.
        """
        ids = self.ids

        return dbc.Card(
            [
                dbc.CardHeader("2. Set Example Calculation Parameters"),
                dbc.Collapse(
                    dbc.CardBody(
                        dash.html.Div(
                            [
                                self._parameters_inline_row(
                                    "Mie Model:",
                                    dash.dcc.RadioItems(
                                        ["Solid Sphere", "Core/Shell Sphere"],
                                        "Solid Sphere",
                                        id=ids.mie_model,
                                        inline=True,
                                        labelClassName="me-3",
                                    ),
                                    margin_top=False,
                                ),
                                dash.html.Div(id=ids.mie_model_parameters_container),
                                dash.html.Button(
                                    "Calibrate",
                                    id=ids.calibrate_example_btn,
                                    n_clicks=0,
                                    style={"marginTop": "8px"},
                                ),
                            ]
                        ),
                        style=self.scroll_style,
                    ),
                    id=f"collapse-{ids.page_name}-example",
                    is_open=True,
                ),
            ]
        )

    def _parameters_register_callbacks(self) -> None:
        """
        Register callbacks for this section.

        Callback behavior
        -----------------
        When the Mie model changes, the section under
        `ids.mie_model_parameters_container` is replaced with the correct set of
        input rows.

        Important
        ---------
        Call this once during app startup. Do not call it repeatedly per request.
        """
        @dash.callback(
            dash.Output(self.ids.mie_model_parameters_container, "children"),
            dash.Input(self.ids.mie_model, "value"),
            prevent_initial_call=False,
        )
        def _render_mie_model_parameters(mie_model_value: Optional[str]):
            if mie_model_value == "Core/Shell Sphere":
                return self._parameters_build_core_shell_parameters_block()
            return self._parameters_build_solid_sphere_parameters_block()

    def _parameters_build_common_medium_parameters_rows(self) -> list:
        """
        Build the shared medium refractive index controls.

        UI elements
        -----------
        - Medium Refractive Index: radio (water, PBS, other)
        - Custom Refractive Index: numeric input (only meaningful when "other" is selected)

        Returns
        -------
        list
            List of Dash components representing the shared medium selection rows.
        """
        return [
            self._parameters_inline_row(
                "Medium Refractive Index:",
                dash.dcc.RadioItems(
                    ["water", "PBS", "other"],
                    "water",
                    id=self.ids.medium_index,
                    inline=True,
                    labelClassName="me-3",
                ),
            ),
            self._parameters_inline_row(
                "Custom Refractive Index:",
                dash.dcc.Input(
                    id=self.ids.custom_medium_index,
                    type="number",
                    placeholder="Custom Refractive Index",
                    style={"width": "160px"},
                ),
            ),
        ]

    def _parameters_build_solid_sphere_parameters_block(self) -> dash.html.Div:
        """
        Build the parameter block for a homogeneous solid sphere Mie model.

        Parameters shown
        ---------------
        - Medium refractive index selection (preset or custom)
        - Particle diameter (nm)
        - Particle refractive index

        Returns
        -------
        dash.html.Div
            Container holding the Solid Sphere input rows.
        """
        runtime_config = get_runtime_config()

        return dash.html.Div(
            [
                *self._parameters_build_common_medium_parameters_rows(),
                self._parameters_inline_row(
                    "Particle Diameter (nm):",
                    dash.dcc.Input(
                        id=self.ids.particle_diameter,
                        type="number",
                        placeholder="Particle Diameter (nm)",
                        value=runtime_config.default_particle_diameter_nm,
                        min=1,
                        step=1,
                        style={"width": "160px"},
                    ),
                ),
                self._parameters_inline_row(
                    "Particle Refractive Index:",
                    dash.dcc.Input(
                        id=self.ids.particle_index,
                        type="number",
                        placeholder="Particle Refractive Index",
                        value=runtime_config.default_particle_index,
                        min=1.0,
                        max=2.5,
                        step=0.001,
                        style={"width": "160px"},
                    ),
                ),
            ]
        )

    def _parameters_build_core_shell_parameters_block(self) -> dash.html.Div:
        """
        Build the parameter block for a concentric core shell sphere Mie model.

        Parameters shown
        ---------------
        - Medium refractive index selection (preset or custom)
        - Core refractive index
        - Shell refractive index
        - Core diameter (nm)
        - Shell thickness (nm)

        Conventions
        -----------
        - Core diameter is the inner diameter of the core.
        - Shell thickness is the radial thickness added on top of the core radius.

        Returns
        -------
        dash.html.Div
            Container holding the Core Shell input rows.
        """
        runtime_config = get_runtime_config()

        return dash.html.Div(
            [
                *self._parameters_build_common_medium_parameters_rows(),
                self._parameters_inline_row(
                    "Particle Core Refractive Index:",
                    dash.dcc.Input(
                        id=self.ids.core_index,
                        type="number",
                        placeholder="Particle Core Refractive Index",
                        value=runtime_config.default_core_index,
                        min=1.0,
                        max=2.5,
                        step=0.001,
                        style={"width": "160px"},
                    ),
                ),
                self._parameters_inline_row(
                    "Particle Shell Refractive Index:",
                    dash.dcc.Input(
                        id=self.ids.shell_index,
                        type="number",
                        placeholder="Particle Shell Refractive Index",
                        value=runtime_config.default_shell_index,
                        min=1.0,
                        max=2.5,
                        step=0.001,
                        style={"width": "160px"},
                    ),
                ),
                self._parameters_inline_row(
                    "Particle Core Diameter (nm):",
                    dash.dcc.Input(
                        id=self.ids.core_diameter,
                        type="number",
                        placeholder="Particle Core Diameter (nm)",
                        value=runtime_config.default_core_diameter_nm,
                        min=1,
                        step=1,
                        style={"width": "160px"},
                    ),
                ),
                self._parameters_inline_row(
                    "Particle Shell Thickness (nm):",
                    dash.dcc.Input(
                        id=self.ids.shell_thickness,
                        type="number",
                        placeholder="Particle Shell Thickness (nm)",
                        value=runtime_config.default_shell_thickness_nm,
                        min=0,
                        step=1,
                        style={"width": "160px"},
                    ),
                ),
            ]
        )

    def _parameters_inline_row(self, label: str, control, *, margin_top: bool = True) -> dash.html.Div:
        """
        Create a single label + control row with consistent styling.

        Parameters
        ----------
        label:
            Text shown in the left label column.
        control:
            Dash component placed to the right of the label.
        margin_top:
            If False, removes top margin from the row (useful for the first row).

        Returns
        -------
        dash.html.Div
            A row container with label and control.
        """
        style = dict(self.row_style)
        if not margin_top:
            style.pop("marginTop", None)

        return dash.html.Div([dash.html.Div([label], style=self.label_style), control], style=style)