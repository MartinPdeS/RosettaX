# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional, Sequence

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.workflow.model.scattering import ScatteringModelConfiguration


logger = logging.getLogger(__name__)


class Model:
    """
    Scattering parameter section.

    Responsibilities
    ----------------
    - Render optical configuration controls.
    - Render particle configuration controls.
    - Render detector preset controls.
    - Render the optical configuration preview.
    - Synchronize parameter controls from the runtime configuration store.

    Ownership
    ---------
    This section owns only the visual parameter inputs.

    The reusable scattering model logic lives in
    RosettaX.workflow.model.scattering.
    """

    model_configuration = ScatteringModelConfiguration

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Parameters
        self.default_values = self.model_configuration.build_default_profile_defaults()

        logger.debug(
            "Initialized Parameters section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering parameter layout.
        """
        logger.debug("Building Parameters layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        """
        Compatibility alias for older section loading code.
        """
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        """
        Build section header.
        """
        return dbc.CardHeader("3. Set calculation parameters")

    def _build_collapse(self) -> dbc.Collapse:
        """
        Build collapsible parameter body.
        """
        return dbc.Collapse(
            self._build_body(),
            id=self.ids.collapse_example,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build parameter body.
        """
        return dbc.CardBody(
            [
                self._build_optical_configuration_section(),
                dash.html.Hr(),
                self._build_particle_configuration_section(),
            ]
        )

    def _build_optical_configuration_section(self) -> dash.html.Div:
        """
        Build optical configuration section.
        """
        return dash.html.Div(
            [
                dash.html.H5("Optical configuration"),
                dash.html.Div(
                    [
                        self._build_optical_configuration_controls(),
                        self._build_optical_configuration_visualization(),
                    ],
                    style={
                        "display": "flex",
                        "gap": "24px",
                        "alignItems": "flex-start",
                        "width": "100%",
                        "flexWrap": "wrap",
                    },
                ),
            ]
        )

    def _build_optical_configuration_controls(self) -> dash.html.Div:
        """
        Build optical configuration controls.
        """
        return dash.html.Div(
            [
                self._build_numeric_input_row(
                    label="Wavelength (nm):",
                    component_id=self.ids.wavelength_nm,
                    placeholder="Wavelength (nm)",
                    value=self.default_values.wavelength_nm,
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
                self._inline_row(
                    "Detector preset:",
                    dash.dcc.Dropdown(
                        id=self.ids.detector_configuration_preset,
                        options=self.model_configuration.build_detector_preset_options(),
                        value=self.model_configuration.custom_detector_preset_name,
                        placeholder="Select detector preset",
                        clearable=False,
                        searchable=False,
                        persistence=True,
                        persistence_type="session",
                        style={
                            "width": "320px",
                        },
                    ),
                    margin_top=True,
                ),
                dash.html.Div(
                    [
                        self._build_numeric_input_row(
                            label="Detector NA:",
                            component_id=self.ids.detector_numerical_aperture,
                            placeholder="Detector NA",
                            value=self.default_values.detector_numerical_aperture,
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector cache NA:",
                            component_id=self.ids.detector_cache_numerical_aperture,
                            placeholder="Detector cache NA",
                            value=self.default_values.detector_cache_numerical_aperture,
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Blocker bar NA:",
                            component_id=self.ids.blocker_bar_numerical_aperture,
                            placeholder="Blocker bar NA",
                            value=self.default_values.blocker_bar_numerical_aperture,
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector sampling:",
                            component_id=self.ids.detector_sampling,
                            placeholder="Detector sampling",
                            value=self.default_values.detector_sampling,
                            min_value=1,
                            step=1,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector phi angle (deg):",
                            component_id=self.ids.detector_phi_angle_degree,
                            placeholder="Detector phi angle",
                            value=self.default_values.detector_phi_angle_degree,
                            min_value=-360.0,
                            max_value=360.0,
                            step=0.1,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector gamma angle (deg):",
                            component_id=self.ids.detector_gamma_angle_degree,
                            placeholder="Detector gamma angle",
                            value=self.default_values.detector_gamma_angle_degree,
                            min_value=-360.0,
                            max_value=360.0,
                            step=0.1,
                            width_px=220,
                        ),
                    ],
                    id=self.ids.detector_configuration_custom_values_container,
                    style={
                        "display": "block",
                    },
                ),
            ],
            style={
                "flex": "1 1 520px",
                "minWidth": "480px",
            },
        )

    def _build_optical_configuration_visualization(self) -> dbc.Card:
        """
        Build optical configuration preview graph.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.dcc.Graph(
                        id=self.ids.optical_configuration_preview,
                        figure=self.model_configuration.build_optical_configuration_preview_figure(
                            detector_numerical_aperture=self.default_values.detector_numerical_aperture,
                            blocker_bar_numerical_aperture=self.default_values.blocker_bar_numerical_aperture,
                            medium_refractive_index=self.default_values.medium_refractive_index,
                            detector_phi_angle_degree=self.default_values.detector_phi_angle_degree,
                            detector_gamma_angle_degree=self.default_values.detector_gamma_angle_degree,
                        ),
                        style={
                            **styling.PLOTLY_GRAPH_STYLE,
                            "height": "30vh",
                        },
                        config=styling.PLOTLY_GRAPH_CONFIG,
                        className="optical-configuration-preview-graph",
                    ),
                ],
                style={
                    "padding": "0px",
                },
            ),
            style={
                "flex": "0 1 430px",
                "minWidth": "340px",
                "overflow": "hidden",
            },
        )

    def _build_particle_configuration_section(self) -> dash.html.Div:
        """
        Build particle configuration section.
        """
        return dash.html.Div(
            [
                dash.html.H5("Particle configuration"),
                self._inline_row(
                    "Particle type:",
                    dash.dcc.Dropdown(
                        id=self.ids.mie_model,
                        options=self.model_configuration.mie_model_options,
                        value=self.default_values.mie_model,
                        clearable=False,
                        searchable=False,
                        persistence=True,
                        persistence_type="session",
                        style={
                            "width": "220px",
                        },
                    ),
                    margin_top=False,
                ),
                self._refractive_index_picker(
                    label="Medium refractive index:",
                    preset_id=self.ids.medium_refractive_index_source,
                    value_id=self.ids.medium_refractive_index_custom,
                    default_value=self.default_values.medium_refractive_index,
                    preset_options=self.model_configuration.medium_refractive_index_presets,
                ),
                dash.html.Div(
                    self._build_solid_sphere_parameters_block(),
                    id=self.ids.solid_sphere_container,
                    style={
                        "display": "block",
                    },
                ),
                dash.html.Div(
                    self._build_core_shell_parameters_block(),
                    id=self.ids.core_shell_container,
                    style={
                        "display": "none",
                    },
                ),
            ]
        )

    def _build_solid_sphere_parameters_block(self) -> list[Any]:
        """
        Build solid sphere parameter controls.
        """
        return [
            self._refractive_index_picker(
                label="Particle refractive index:",
                preset_id=self.ids.particle_refractive_index_source,
                value_id=self.ids.particle_refractive_index_custom,
                default_value=self.default_values.particle_refractive_index,
                preset_options=self.model_configuration.particle_refractive_index_presets,
            ),
        ]

    def _build_core_shell_parameters_block(self) -> list[Any]:
        """
        Build core shell parameter controls.
        """
        return [
            self._refractive_index_picker(
                label="Core refractive index:",
                preset_id=self.ids.core_refractive_index_source,
                value_id=self.ids.core_refractive_index_custom,
                default_value=self.default_values.core_refractive_index,
                preset_options=self.model_configuration.core_refractive_index_presets,
            ),
            self._refractive_index_picker(
                label="Shell refractive index:",
                preset_id=self.ids.shell_refractive_index_source,
                value_id=self.ids.shell_refractive_index_custom,
                default_value=self.default_values.shell_refractive_index,
                preset_options=self.model_configuration.shell_refractive_index_presets,
            ),
        ]

    def register_callbacks(self) -> None:
        """
        Register parameter callbacks.
        """
        logger.debug("Registering Parameters callbacks.")

        self._register_visibility_callbacks()
        self._register_refractive_index_callbacks()
        self._register_detector_configuration_callbacks()
        self._register_optical_configuration_preview_callback()
        self._register_runtime_sync_callbacks()

    def _register_runtime_sync_callbacks(self) -> None:
        """
        Register runtime configuration synchronization callback.
        """

        @dash.callback(
            dash.Output(self.ids.mie_model, "value"),
            dash.Output(self.ids.medium_refractive_index_custom, "value"),
            dash.Output(self.ids.particle_refractive_index_custom, "value"),
            dash.Output(self.ids.core_refractive_index_custom, "value"),
            dash.Output(self.ids.shell_refractive_index_custom, "value"),
            dash.Output(self.ids.wavelength_nm, "value"),
            dash.Output(self.ids.detector_numerical_aperture, "value"),
            dash.Output(self.ids.detector_cache_numerical_aperture, "value"),
            dash.Output(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.Output(self.ids.detector_sampling, "value"),
            dash.Output(self.ids.detector_phi_angle_degree, "value"),
            dash.Output(self.ids.detector_gamma_angle_degree, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_parameters_from_runtime_config(
            runtime_config_data: Any,
        ) -> tuple[Any, ...]:
            logger.debug(
                "sync_parameters_from_runtime_config called with runtime_config_data=%r",
                runtime_config_data,
            )

            resolved_values = self.model_configuration.build_defaults_from_runtime_config(
                runtime_config_data,
            ).to_callback_values()

            logger.debug(
                "sync_parameters_from_runtime_config returning resolved_values=%r",
                resolved_values,
            )

            return resolved_values

    def _register_visibility_callbacks(self) -> None:
        """
        Register particle model visibility callbacks.
        """

        @dash.callback(
            dash.Output(self.ids.solid_sphere_container, "style"),
            dash.Output(self.ids.core_shell_container, "style"),
            dash.Input(self.ids.mie_model, "value"),
            prevent_initial_call=False,
        )
        def toggle_parameter_blocks(
            mie_model_value: Optional[str],
        ) -> tuple[dict[str, str], dict[str, str]]:
            resolved_styles = self.model_configuration.build_visibility_styles_for_mie_model(
                mie_model=mie_model_value,
            )

            logger.debug(
                "toggle_parameter_blocks called with mie_model_value=%r styles=%r",
                mie_model_value,
                resolved_styles,
            )

            return resolved_styles

    def _register_refractive_index_callbacks(self) -> None:
        """
        Register refractive index preset callbacks.
        """

        @dash.callback(
            dash.Output(
                self.ids.medium_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.medium_refractive_index_source, "value"),
            dash.State(self.ids.medium_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_medium_preset(
            preset_value: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.particle_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.particle_refractive_index_source, "value"),
            dash.State(self.ids.particle_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_particle_preset(
            preset_value: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.core_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.core_refractive_index_source, "value"),
            dash.State(self.ids.core_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_core_preset(
            preset_value: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                current_value=current_value,
            )

        @dash.callback(
            dash.Output(
                self.ids.shell_refractive_index_custom,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.shell_refractive_index_source, "value"),
            dash.State(self.ids.shell_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_shell_preset(
            preset_value: Any,
            current_value: Any,
        ) -> Any:
            return self.model_configuration.apply_refractive_index_preset(
                preset_value=preset_value,
                current_value=current_value,
            )

    def _register_detector_configuration_callbacks(self) -> None:
        """
        Register detector configuration callbacks.
        """

        @dash.callback(
            dash.Output(
                self.ids.detector_configuration_custom_values_container,
                "style",
            ),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            prevent_initial_call=False,
        )
        def toggle_detector_configuration_custom_values(
            preset_name: Any,
        ) -> dict[str, str]:
            logger.debug(
                "toggle_detector_configuration_custom_values called with preset_name=%r",
                preset_name,
            )

            return self.model_configuration.resolve_detector_configuration_visibility_style(
                preset_name=preset_name,
            )

        @dash.callback(
            dash.Output(
                self.ids.detector_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.blocker_bar_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_sampling,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_phi_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.detector_gamma_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.detector_configuration_preset, "value"),
            dash.State(self.ids.detector_numerical_aperture, "value"),
            dash.State(self.ids.detector_cache_numerical_aperture, "value"),
            dash.State(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.State(self.ids.detector_sampling, "value"),
            dash.State(self.ids.detector_phi_angle_degree, "value"),
            dash.State(self.ids.detector_gamma_angle_degree, "value"),
            prevent_initial_call=True,
        )
        def apply_detector_configuration_preset(
            preset_name: Any,
            current_detector_numerical_aperture: Any,
            current_detector_cache_numerical_aperture: Any,
            current_blocker_bar_numerical_aperture: Any,
            current_detector_sampling: Any,
            current_detector_phi_angle_degree: Any,
            current_detector_gamma_angle_degree: Any,
        ) -> tuple[Any, Any, Any, Any, Any, Any]:
            logger.debug(
                "apply_detector_configuration_preset called with preset_name=%r",
                preset_name,
            )

            resolved_values = self.model_configuration.resolve_detector_configuration_values(
                preset_name=preset_name,
                current_detector_numerical_aperture=current_detector_numerical_aperture,
                current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
                current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
                current_detector_sampling=current_detector_sampling,
                current_detector_phi_angle_degree=current_detector_phi_angle_degree,
                current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
            )

            logger.debug(
                "apply_detector_configuration_preset returning resolved_values=%r",
                resolved_values,
            )

            return resolved_values

    def _register_optical_configuration_preview_callback(self) -> None:
        """
        Register optical configuration preview callback.
        """

        @dash.callback(
            dash.Output(
                self.ids.optical_configuration_preview,
                "figure",
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.Input(self.ids.blocker_bar_numerical_aperture, "value"),
            dash.Input(self.ids.medium_refractive_index_custom, "value"),
            dash.Input(self.ids.detector_phi_angle_degree, "value"),
            dash.Input(self.ids.detector_gamma_angle_degree, "value"),
            prevent_initial_call=False,
        )
        def update_optical_configuration_preview(
            detector_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            medium_refractive_index: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
        ):
            logger.debug(
                "update_optical_configuration_preview called with "
                "detector_numerical_aperture=%r blocker_bar_numerical_aperture=%r "
                "medium_refractive_index=%r detector_phi_angle_degree=%r "
                "detector_gamma_angle_degree=%r",
                detector_numerical_aperture,
                blocker_bar_numerical_aperture,
                medium_refractive_index,
                detector_phi_angle_degree,
                detector_gamma_angle_degree,
            )

            return self.model_configuration.build_optical_configuration_preview_figure(
                detector_numerical_aperture=detector_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                medium_refractive_index=medium_refractive_index,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
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
        """
        Build a labeled numeric input row.
        """
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
                debounce=True,
                persistence=True,
                persistence_type="session",
                style={
                    "width": f"{width_px}px",
                },
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
        """
        Build refractive index preset and custom value controls.
        """
        preset_dropdown = dash.dcc.Dropdown(
            id=preset_id,
            options=list(preset_options),
            value=None,
            placeholder=preset_placeholder_label,
            clearable=True,
            searchable=False,
            persistence=True,
            persistence_type="session",
            style={
                "width": "220px",
                "marginRight": "10px",
            },
        )

        numeric_input = dash.dcc.Input(
            id=value_id,
            type="number",
            value=default_value,
            min=1.0,
            max=2.5,
            step=0.001,
            debounce=True,
            persistence=True,
            persistence_type="session",
            style={
                "width": "160px",
            },
        )

        return self._inline_row(
            label,
            dash.html.Div(
                [
                    preset_dropdown,
                    numeric_input,
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                },
            ),
        )

    def _inline_row(
        self,
        label: str,
        control: Any,
        *,
        margin_top: bool = True,
    ) -> dash.html.Div:
        """
        Build one aligned label control row.
        """
        row_style = {
            "display": "flex",
            "alignItems": "center",
            "width": "100%",
            "marginTop": "10px",
        }

        if not margin_top:
            row_style.pop(
                "marginTop",
                None,
            )

        return dash.html.Div(
            [
                dash.html.Div(
                    label,
                    style={
                        "width": "260px",
                        "minWidth": "260px",
                        "fontWeight": 500,
                    },
                ),
                dash.html.Div(
                    control,
                    style={
                        "flex": "1",
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
            ],
            style=row_style,
        )