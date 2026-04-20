from typing import Any, Optional, Sequence
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


class Parameters:
    """
    Render and manage the scattering calculation parameter section.

    Responsibilities
    ----------------
    - Render optical and particle configuration inputs.
    - Show the solid sphere or core shell block depending on the selected model.
    - Synchronize values from the runtime config store.
    - Apply refractive index presets into numeric inputs.
    - Apply optical configuration presets into numeric inputs.
    - Provide a consistent parameter schema for downstream calibration logic.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized ParametersSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        logger.debug("Building ParametersSection layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("3. Set calculation parameters")

    def _build_collapse(self) -> dbc.Collapse:
        return dbc.Collapse(
            self._build_body(),
            id=self.page.ids.Parameters.collapse_example,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_optical_configuration_section(),
                dash.html.Hr(),
                self._build_particle_configuration_section(),
                self._build_calibrate_button(),
            ]
        )

    def _build_optical_configuration_section(self) -> dash.html.Div:
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.H5("Optical configuration"),
                self._inline_row(
                    "Configuration preset:",
                    dash.dcc.Dropdown(
                        id=self.page.ids.Parameters.optical_configuration_preset,
                        options=self._get_optical_configuration_preset_options(),
                        value=None,
                        placeholder="Select optical configuration preset",
                        clearable=True,
                        searchable=False,
                        persistence=False,
                        style={"width": "320px"},
                    ),
                    margin_top=False,
                ),
                self._build_numeric_input_row(
                    label="Wavelength (nm):",
                    component_id=self.page.ids.Parameters.wavelength_nm,
                    placeholder="Wavelength (nm)",
                    value=getattr(runtime_config.Default, "wavelength_nm", 700.0),
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector numerical aperture:",
                    component_id=self.page.ids.Parameters.detector_numerical_aperture,
                    placeholder="Detector numerical aperture",
                    value=getattr(runtime_config.Default, "detector_numerical_aperture", 0.2),
                    min_value=0.0,
                    max_value=1.5,
                    step=0.001,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector cache numerical aperture:",
                    component_id=self.page.ids.Parameters.detector_cache_numerical_aperture,
                    placeholder="Detector cache numerical aperture",
                    value=getattr(runtime_config.Default, "detector_cache_numerical_aperture", 0.2),
                    min_value=0.0,
                    max_value=1.5,
                    step=0.001,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector sampling:",
                    component_id=self.page.ids.Parameters.detector_sampling,
                    placeholder="Detector sampling",
                    value=getattr(runtime_config.Default, "detector_sampling", 600),
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
            ]
        )

    def _build_particle_configuration_section(self) -> dash.html.Div:
        runtime_config = RuntimeConfig()

        return dash.html.Div(
            [
                dash.html.H5("Particle configuration"),
                self._inline_row(
                    "Particle type:",
                    dash.dcc.Dropdown(
                        id=self.page.ids.Parameters.mie_model,
                        options=self._get_mie_model_options(),
                        value="Solid Sphere",
                        clearable=False,
                        searchable=False,
                        persistence=True,
                        persistence_type="session",
                        style={"width": "220px"},
                    ),
                    margin_top=False,
                ),
                self._refractive_index_picker(
                    label="Medium refractive index:",
                    preset_id=self.page.ids.Parameters.medium_refractive_index_source,
                    value_id=self.page.ids.Parameters.medium_refractive_index_custom,
                    default_value=getattr(runtime_config.Default, "medium_refractive_index", 1.333),
                    preset_options=self._get_medium_refractive_index_presets(),
                ),
                dash.html.Div(
                    self._build_solid_sphere_parameters_block(),
                    id=self.page.ids.Parameters.solid_sphere_container,
                    style={"display": "block"},
                ),
                dash.html.Div(
                    self._build_core_shell_parameters_block(),
                    id=self.page.ids.Parameters.core_shell_container,
                    style={"display": "none"},
                ),
            ]
        )

    def _build_solid_sphere_parameters_block(self) -> list:
        runtime_config = RuntimeConfig()

        return [
            self._refractive_index_picker(
                label="Particle refractive index:",
                preset_id=self.page.ids.Parameters.particle_refractive_index_source,
                value_id=self.page.ids.Parameters.particle_refractive_index_custom,
                default_value=getattr(runtime_config.Default, "particle_refractive_index", 1.59),
                preset_options=self._get_particle_refractive_index_presets(),
            ),
            self._build_numeric_input_row(
                label="Particle diameter (nm):",
                component_id=self.page.ids.Parameters.particle_diameter,
                placeholder="Particle diameter (nm)",
                value=getattr(runtime_config.Default, "particle_diameter", 100.0),
                min_value=1,
                step=1,
                width_px=220,
            ),
        ]

    def _build_core_shell_parameters_block(self) -> list:
        runtime_config = RuntimeConfig()

        return [
            self._refractive_index_picker(
                label="Core refractive index:",
                preset_id=self.page.ids.Parameters.core_refractive_index_source,
                value_id=self.page.ids.Parameters.core_refractive_index_custom,
                default_value=getattr(runtime_config.Default, "core_refractive_index", 1.47),
                preset_options=self._get_core_refractive_index_presets(),
            ),
            self._refractive_index_picker(
                label="Shell refractive index:",
                preset_id=self.page.ids.Parameters.shell_refractive_index_source,
                value_id=self.page.ids.Parameters.shell_refractive_index_custom,
                default_value=getattr(runtime_config.Default, "shell_refractive_index", 1.46),
                preset_options=self._get_shell_refractive_index_presets(),
            ),
            self._build_numeric_input_row(
                label="Core diameter (nm):",
                component_id=self.page.ids.Parameters.core_diameter,
                placeholder="Core diameter (nm)",
                value=getattr(runtime_config.Default, "core_diameter", 80.0),
                min_value=1,
                step=1,
                width_px=220,
            ),
            self._build_numeric_input_row(
                label="Shell thickness (nm):",
                component_id=self.page.ids.Parameters.shell_thickness,
                placeholder="Shell thickness (nm)",
                value=getattr(runtime_config.Default, "shell_thickness", 5.0),
                min_value=0,
                step=1,
                width_px=220,
            ),
        ]

    def _build_calibrate_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Calibrate",
            id=self.page.ids.Calibration.calibrate_btn,
            n_clicks=0,
            style={"marginTop": "12px"},
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering ParametersSection callbacks.")
        self._register_visibility_callbacks()
        self._register_runtime_sync_callbacks()
        self._register_refractive_index_callbacks()
        self._register_optical_configuration_callbacks()

    def _register_visibility_callbacks(self) -> None:
        logger.debug("Registering parameter visibility callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Parameters.solid_sphere_container, "style"),
            dash.Output(self.page.ids.Parameters.core_shell_container, "style"),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            prevent_initial_call=False,
        )
        def toggle_parameter_blocks(mie_model_value: Optional[str]):
            logger.debug(
                "toggle_parameter_blocks called with mie_model_value=%r",
                mie_model_value,
            )

            if mie_model_value == "Core/Shell Sphere":
                return {"display": "none"}, {"display": "block"}

            return {"display": "block"}, {"display": "none"}

    def _register_runtime_sync_callbacks(self) -> None:
        logger.debug("Registering runtime sync callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Parameters.mie_model, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_mie_model(runtime_config_data: Any):
            runtime_config = RuntimeConfig()

            if not isinstance(runtime_config_data, dict):
                return getattr(runtime_config.Default, "mie_model", "Solid Sphere")

            return runtime_config_data.get(
                "mie_model",
                getattr(runtime_config.Default, "mie_model", "Solid Sphere"),
            )

        @dash.callback(
            dash.Output(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.particle_diameter, "value"),
            dash.Output(self.page.ids.Parameters.core_diameter, "value"),
            dash.Output(self.page.ids.Parameters.shell_thickness, "value"),
            dash.Output(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.Output(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.Output(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.Output(self.page.ids.Parameters.detector_sampling, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_parameter_values(runtime_config_data: Any):
            logger.debug(
                "sync_parameter_values called with runtime_config_data=%r",
                runtime_config_data,
            )

            defaults = self._resolve_parameter_defaults(runtime_config_data)

            return (
                defaults["medium_refractive_index"],
                defaults["particle_refractive_index"],
                defaults["core_refractive_index"],
                defaults["shell_refractive_index"],
                defaults["particle_diameter"],
                defaults["core_diameter"],
                defaults["shell_thickness"],
                defaults["wavelength_nm"],
                defaults["detector_numerical_aperture"],
                defaults["detector_cache_numerical_aperture"],
                defaults["detector_sampling"],
            )

    def _register_refractive_index_callbacks(self) -> None:
        logger.debug("Registering refractive index preset callbacks.")

        def apply_preset_value(preset_value: Any, current_value: Any):
            logger.debug(
                "apply_preset_value called with preset_value=%r current_value=%r",
                preset_value,
                current_value,
            )

            if preset_value is None:
                return current_value

            return float(preset_value)

        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.medium_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.medium_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_medium_preset(preset_value: Any, current_value: Any):
            return apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.particle_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.particle_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_particle_preset(preset_value: Any, current_value: Any):
            return apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.core_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.core_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_core_preset(preset_value: Any, current_value: Any):
            return apply_preset_value(preset_value, current_value)

        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.shell_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.shell_refractive_index_source, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_shell_preset(preset_value: Any, current_value: Any):
            return apply_preset_value(preset_value, current_value)

    def _register_optical_configuration_callbacks(self) -> None:
        logger.debug("Registering optical configuration preset callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Parameters.wavelength_nm, "value", allow_duplicate=True),
            dash.Output(self.page.ids.Parameters.detector_numerical_aperture, "value", allow_duplicate=True),
            dash.Output(self.page.ids.Parameters.detector_cache_numerical_aperture, "value", allow_duplicate=True),
            dash.Output(self.page.ids.Parameters.detector_sampling, "value", allow_duplicate=True),
            dash.Input(self.page.ids.Parameters.optical_configuration_preset, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            prevent_initial_call=True,
        )
        def apply_optical_configuration_preset(
            preset_name: Any,
            current_wavelength_nm: Any,
            current_detector_numerical_aperture: Any,
            current_detector_cache_numerical_aperture: Any,
            current_detector_sampling: Any,
        ):
            if preset_name is None:
                return (
                    current_wavelength_nm,
                    current_detector_numerical_aperture,
                    current_detector_cache_numerical_aperture,
                    current_detector_sampling,
                )

            preset = self._get_optical_configuration_presets().get(str(preset_name), {})

            return (
                preset.get("wavelength_nm", current_wavelength_nm),
                preset.get("detector_numerical_aperture", current_detector_numerical_aperture),
                preset.get("detector_cache_numerical_aperture", current_detector_cache_numerical_aperture),
                preset.get("detector_sampling", current_detector_sampling),
            )

    def build_parameter_dict(
        self,
        *,
        mie_model: Any,
        medium_refractive_index: Any,
        particle_refractive_index: Any,
        core_refractive_index: Any,
        shell_refractive_index: Any,
        particle_diameter: Any,
        core_diameter: Any,
        shell_thickness: Any,
        wavelength_nm: Any,
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
        detector_sampling: Any,
    ) -> dict[str, Any]:
        parameter_dict = {
            "mie_model": None if mie_model is None else str(mie_model),
            "medium_refractive_index": medium_refractive_index,
            "particle_refractive_index": particle_refractive_index,
            "core_refractive_index": core_refractive_index,
            "shell_refractive_index": shell_refractive_index,
            "particle_diameter_nm": particle_diameter,
            "core_diameter_nm": core_diameter,
            "shell_thickness_nm": shell_thickness,
            "wavelength_nm": wavelength_nm,
            "optical_power_watt": 1.0,
            "source_numerical_aperture": 0.1,
            "detector_numerical_aperture": detector_numerical_aperture,
            "detector_cache_numerical_aperture": detector_cache_numerical_aperture,
            "detector_sampling": detector_sampling,
        }

        logger.debug("build_parameter_dict returning parameter_dict=%r", parameter_dict)
        return parameter_dict

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
                persistence=False,
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
            persistence=False,
            style={"width": "220px", "marginRight": "10px"},
        )

        numeric_input = dash.dcc.Input(
            id=value_id,
            type="number",
            value=default_value,
            min=1.0,
            max=2.5,
            step=0.001,
            persistence=False,
            style={"width": "160px"},
        )

        return self._inline_row(
            label,
            dash.html.Div(
                [preset_dropdown, numeric_input],
                style={"display": "flex", "alignItems": "center"},
            ),
        )

    def _inline_row(
        self,
        label: str,
        control,
        *,
        margin_top: bool = True,
    ) -> dash.html.Div:
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

    def _resolve_parameter_defaults(self, runtime_config_data: Any) -> dict[str, Any]:
        runtime_config = RuntimeConfig()

        if not isinstance(runtime_config_data, dict):
            return {
                "medium_refractive_index": getattr(runtime_config.Default, "medium_refractive_index", 1.333),
                "particle_refractive_index": getattr(runtime_config.Default, "particle_refractive_index", 1.59),
                "core_refractive_index": getattr(runtime_config.Default, "core_refractive_index", 1.47),
                "shell_refractive_index": getattr(runtime_config.Default, "shell_refractive_index", 1.46),
                "particle_diameter": getattr(runtime_config.Default, "particle_diameter", 100.0),
                "core_diameter": getattr(runtime_config.Default, "core_diameter", 80.0),
                "shell_thickness": getattr(runtime_config.Default, "shell_thickness", 5.0),
                "wavelength_nm": getattr(runtime_config.Default, "wavelength_nm", 700.0),
                "detector_numerical_aperture": getattr(runtime_config.Default, "detector_numerical_aperture", 0.2),
                "detector_cache_numerical_aperture": getattr(runtime_config.Default, "detector_cache_numerical_aperture", 0.2),
                "detector_sampling": getattr(runtime_config.Default, "detector_sampling", 600),
            }

        return {
            "medium_refractive_index": runtime_config_data.get("medium_refractive_index", getattr(runtime_config.Default, "medium_refractive_index", 1.333)),
            "particle_refractive_index": runtime_config_data.get("particle_refractive_index", getattr(runtime_config.Default, "particle_refractive_index", 1.59)),
            "core_refractive_index": runtime_config_data.get("core_refractive_index", getattr(runtime_config.Default, "core_refractive_index", 1.47)),
            "shell_refractive_index": runtime_config_data.get("shell_refractive_index", getattr(runtime_config.Default, "shell_refractive_index", 1.46)),
            "particle_diameter": runtime_config_data.get("particle_diameter_nm", getattr(runtime_config.Default, "particle_diameter", 100.0)),
            "core_diameter": runtime_config_data.get("core_diameter_nm", getattr(runtime_config.Default, "core_diameter", 80.0)),
            "shell_thickness": runtime_config_data.get("shell_thickness_nm", getattr(runtime_config.Default, "shell_thickness", 5.0)),
            "wavelength_nm": runtime_config_data.get("wavelength_nm", getattr(runtime_config.Default, "wavelength_nm", 700.0)),
            "detector_numerical_aperture": runtime_config_data.get("detector_numerical_aperture", getattr(runtime_config.Default, "detector_numerical_aperture", 0.2)),
            "detector_cache_numerical_aperture": runtime_config_data.get("detector_cache_numerical_aperture", getattr(runtime_config.Default, "detector_cache_numerical_aperture", 0.2)),
            "detector_sampling": runtime_config_data.get("detector_sampling", getattr(runtime_config.Default, "detector_sampling", 600)),
        }

    def _get_mie_model_options(self) -> list[dict]:
        return [
            {"label": "Solid Sphere", "value": "Solid Sphere"},
            {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
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

    def _get_optical_configuration_presets(self) -> dict[str, dict[str, Any]]:
        return {
            "default_small_particle_setup": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.2,
                "detector_cache_numerical_aperture": 0.2,
                "detector_sampling": 600,
            },
            "higher_na_collection": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.4,
                "detector_cache_numerical_aperture": 0.4,
                "detector_sampling": 600,
            },
            "low_sampling_preview": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.2,
                "detector_cache_numerical_aperture": 0.2,
                "detector_sampling": 200,
            },
        }

    def _get_optical_configuration_preset_options(self) -> list[dict]:
        return [
            {"label": "Default small particle setup", "value": "default_small_particle_setup"},
            {"label": "Higher NA collection", "value": "higher_na_collection"},
            {"label": "Low sampling preview", "value": "low_sampling_preview"},
        ]