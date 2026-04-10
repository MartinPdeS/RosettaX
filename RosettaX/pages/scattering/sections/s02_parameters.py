from typing import Any, Optional, Sequence
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


class ParametersSection:
    """
    Render and manage the example calculation parameters section.

    Responsibilities
    ----------------
    - Render a card containing a particle type selector and a dynamic parameter block.
    - Swap parameter blocks when the particle type changes.
    - Apply refractive index presets by copying dropdown values into numeric inputs.
    - Preserve user entered values across page navigation within the session.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ParametersSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        logger.debug("Building parameters section layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("2. Set Example Calculation Parameters")

    def _build_collapse(self) -> dbc.Collapse:
        return dbc.Collapse(
            self._build_body(),
            id=self.page.ids.collapse_example,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        ids = self.page.ids

        return dbc.CardBody(
            dash.html.Div(
                [
                    self._build_particle_type_row(),
                    dash.html.Div(id=ids.Parameters.mie_model_parameters_container),
                    self._build_calibrate_button(),
                ]
            )
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering parameters section callbacks.")
        self.register_render_callbacks()
        self.register_refractive_index_callbacks()

    def register_render_callbacks(self) -> None:
        logger.debug("Registering parameter render callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Parameters.mie_model_parameters_container, "children"),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            prevent_initial_call=False,
        )
        def _render_mie_model_parameters(mie_model_value: Optional[str]):
            logger.debug(
                "_render_mie_model_parameters called with mie_model_value=%r",
                mie_model_value,
            )

            if mie_model_value == "Core/Shell Sphere":
                return self._build_core_shell_parameters_block()

            return self._build_solid_sphere_parameters_block()

    def register_refractive_index_callbacks(self) -> None:
        logger.debug("Registering refractive index preset callbacks.")

        def _apply_preset_value(preset_value: Any, current_value: Any):
            logger.debug(
                "_apply_preset_value called with preset_value=%r current_value=%r",
                preset_value,
                current_value,
            )

            if preset_value is None:
                return current_value

            return float(preset_value)

        @dash.callback(
            dash.Output(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.Input(self.page.ids.Parameters.medium_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _apply_medium_preset(preset_value: Any, current_value: Any):
            return _apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.Input(self.page.ids.Parameters.particle_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _apply_particle_preset(preset_value: Any, current_value: Any):
            return _apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.Input(self.page.ids.Parameters.core_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _apply_core_preset(preset_value: Any, current_value: Any):
            return _apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.Input(self.page.ids.Parameters.shell_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def _apply_shell_preset(preset_value: Any, current_value: Any):
            return _apply_preset_value(preset_value, current_value)

    def _build_particle_type_row(self) -> dash.html.Div:
        ids = self.page.ids

        return self._inline_row(
            "Particle Type:",
            dash.dcc.Dropdown(
                id=ids.Parameters.mie_model,
                options=self._get_mie_model_options(),
                value="Solid Sphere",
                clearable=False,
                searchable=False,
                persistence=True,
                persistence_type="session",
                style={"width": "220px"},
            ),
            margin_top=False,
        )

    def _build_calibrate_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Calibrate",
            id=self.page.ids.calibrate_example_btn,
            n_clicks=0,
            style={"marginTop": "8px"},
        )

    def _get_mie_model_options(self) -> list[dict]:
        return [
            {"label": "Solid Sphere", "value": "Solid Sphere"},
            {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
        ]

    def _build_common_medium_parameters_rows(self) -> list:
        runtime_config = RuntimeConfig()

        return [
            self._refractive_index_picker(
                label="Medium Refractive Index:",
                preset_id=self.page.ids.Parameters.medium_refractive_index_source,
                value_id=self.page.ids.Parameters.medium_refractive_index_custom,
                default_value=getattr(runtime_config.Default, "medium_refractive_index", 1.333),
                preset_options=self._get_medium_refractive_index_presets(),
            )
        ]

    def _get_medium_refractive_index_presets(self) -> list[dict]:
        return [
            {"label": "Water 1.333", "value": 1.333},
            {"label": "PBS 1.335", "value": 1.335},
        ]

    def _get_particle_refractive_index_presets(self) -> list[dict]:
        return [
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
            {"label": "PMMA 1.49", "value": 1.49},
            {"label": "Lipid 1.47", "value": 1.47},
        ]

    def _get_core_refractive_index_presets(self) -> list[dict]:
        return [
            {"label": "Soybean oil 1.47", "value": 1.47},
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
        ]

    def _get_shell_refractive_index_presets(self) -> list[dict]:
        return [
            {"label": "Phospholipid 1.46", "value": 1.46},
            {"label": "Waterlike 1.33", "value": 1.33},
        ]

    def _build_solid_sphere_parameters_block(self) -> dash.html.Div:
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                *self._build_common_medium_parameters_rows(),
                self._refractive_index_picker(
                    label="Particle Refractive Index:",
                    preset_id=self.page.ids.Parameters.particle_refractive_index_source,
                    value_id=self.page.ids.Parameters.particle_refractive_index_custom,
                    default_value=runtime_config.Default.particle_refractive_index,
                    preset_options=self._get_particle_refractive_index_presets(),
                ),
                self._build_numeric_input_row(
                    label="Particle Diameter (nm):",
                    component_id=self.page.ids.Parameters.particle_diameter,
                    placeholder="Particle Diameter (nm)",
                    value=runtime_config.Default.particle_diameter,
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
            ]
        )

    def _build_core_shell_parameters_block(self) -> dash.html.Div:
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                *self._build_common_medium_parameters_rows(),
                self._refractive_index_picker(
                    label="Particle Core Refractive Index:",
                    preset_id=self.page.ids.Parameters.core_refractive_index_source,
                    value_id=self.page.ids.Parameters.core_refractive_index_custom,
                    default_value=runtime_config.Default.core_refractive_index,
                    preset_options=self._get_core_refractive_index_presets(),
                ),
                self._refractive_index_picker(
                    label="Particle Shell Refractive Index:",
                    preset_id=self.page.ids.Parameters.shell_refractive_index_source,
                    value_id=self.page.ids.Parameters.shell_refractive_index_custom,
                    default_value=runtime_config.Default.shell_refractive_index,
                    preset_options=self._get_shell_refractive_index_presets(),
                ),
                self._build_numeric_input_row(
                    label="Particle Core Diameter (nm):",
                    component_id=self.page.ids.Parameters.core_diameter,
                    placeholder="Particle Core Diameter (nm)",
                    value=runtime_config.Default.core_diameter,
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Particle Shell Thickness (nm):",
                    component_id=self.page.ids.Parameters.shell_thickness,
                    placeholder="Particle Shell Thickness (nm)",
                    value=runtime_config.Default.shell_thickness,
                    min_value=0,
                    step=1,
                    width_px=220,
                ),
            ]
        )

    def _build_numeric_input_row(
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
        return self._inline_row(
            label,
            dash.dcc.Input(
                id=component_id,
                type="number",
                placeholder=placeholder,
                value=value,
                min=min_value,
                max=max_value,
                step=step,
                persistence=True,
                persistence_type="session",
                style={"width": f"{width_px}px"},
            ),
        )

    def _refractive_index_picker(
        self,
        *,
        label: str,
        preset_id: str,
        value_id: str,
        default_value: float,
        preset_options: Sequence[dict],
        preset_placeholder_label: str = "Select preset",
    ) -> dash.html.Div:
        preset_dropdown = dash.dcc.Dropdown(
            id=preset_id,
            options=list(preset_options),
            value=None,
            placeholder=preset_placeholder_label,
            clearable=True,
            searchable=False,
            persistence=True,
            persistence_type="session",
            style={"width": "220px", "marginRight": "10px"},
        )

        numeric_input = dash.dcc.Input(
            id=value_id,
            type="number",
            value=default_value,
            min=1.0,
            max=2.5,
            step=0.001,
            persistence=True,
            persistence_type="session",
            style={"width": "160px"},
        )

        return self._inline_row(
            label,
            dash.html.Div(
                [preset_dropdown, numeric_input],
                style={"display": "flex", "alignItems": "center"},
            ),
        )

    def _inline_row(self, label: str, control, *, margin_top: bool = True) -> dash.html.Div:
        row_style = {
            "display": "flex",
            "alignItems": "center",
            "width": "100%",
            "marginTop": "10px",
        }
        if not margin_top:
            row_style.pop("marginTop", None)

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
            style=row_style,
        )