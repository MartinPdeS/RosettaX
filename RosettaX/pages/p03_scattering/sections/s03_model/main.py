# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional, Sequence

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling, ui_forms, RuntimeConfig, casting
from RosettaX.workflow.scattering.model import ScatteringModelConfiguration


logger = logging.getLogger(__name__)


DETECTOR_NUMERICAL_APERTURE_EPSILON = 1e-6


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
    RosettaX.workflow.scattering.model.
    """

    model_configuration = ScatteringModelConfiguration

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.ids = page.ids.Parameters
        self.section_number = section_number
        self.card_color = card_color
        self.default_values = self.model_configuration.build_default_profile_defaults()

        self.section_tooltip_target_id = f"{self.ids.mie_model}-section-info-target"
        self.section_tooltip_id = f"{self.ids.mie_model}-section-info-tooltip"

        self.optical_configuration_tooltip_target_id = f"{self.ids.wavelength_nm}-optical-info-target"
        self.optical_configuration_tooltip_id = f"{self.ids.wavelength_nm}-optical-info-tooltip"

        self.particle_configuration_tooltip_target_id = f"{self.ids.mie_model}-particle-info-target"
        self.particle_configuration_tooltip_id = f"{self.ids.mie_model}-particle-info-tooltip"

        self.scatterer_preset_tooltip_target_id = f"{self.ids.scatterer_preset}-info-target"
        self.scatterer_preset_tooltip_id = f"{self.ids.scatterer_preset}-info-tooltip"

        self.detector_preset_tooltip_target_id = f"{self.ids.detector_configuration_preset}-info-target"
        self.detector_preset_tooltip_id = f"{self.ids.detector_configuration_preset}-info-tooltip"

        self.optical_preview_tooltip_target_id = f"{self.ids.optical_configuration_preview}-info-target"
        self.optical_preview_tooltip_id = f"{self.ids.optical_configuration_preview}-info-tooltip"

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
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Set calculation parameters",
            tooltip_target_id=self.section_tooltip_target_id,
            tooltip_id=self.section_tooltip_id,
            tooltip_text=(
                "These parameters define the optical, detector, and particle "
                "model used to compute the calibration standard coupling values."
            ),
            subtitle="Configure the physical model used for scattering calibration.",
            color_name=self.card_color,
        )

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
                self._build_optical_configuration_panel(),
                dash.html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._build_particle_configuration_panel(),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_optical_configuration_panel(self) -> dbc.Card:
        """
        Build the optical configuration subpanel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Optical configuration",
                            tooltip_target_id=self.optical_configuration_tooltip_target_id,
                            tooltip_id=self.optical_configuration_tooltip_id,
                            tooltip_text=(
                                "These controls define the illumination wavelength, detector "
                                "acceptance geometry, collection numerical aperture, blocker "
                                "bar numerical aperture, and angular sampling used by the "
                                "scattering model."
                            ),
                            title_style_overrides={
                                "fontSize": "1rem",
                            },
                        ),
                        dash.html.Div(
                            "Illumination, detector geometry, and angular sampling.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.card_color,
                    ),
                ),
                dbc.CardBody(
                    [
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
                                "overflow": "visible",
                            },
                        ),
                    ],
                    style=ui_forms.build_workflow_panel_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
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
                ui_forms.build_inline_row(
                    label="Detector preset:",
                    control=dash.html.Div(
                        [
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
                            ui_forms.build_info_badge(
                                tooltip_target_id=self.detector_preset_tooltip_target_id,
                            ),
                            dbc.Tooltip(
                                (
                                    "Use a detector preset to load a predefined "
                                    "collection geometry. Select the custom preset "
                                    "when you want to edit each detector parameter "
                                    "manually."
                                ),
                                id=self.detector_preset_tooltip_id,
                                target=self.detector_preset_tooltip_target_id,
                                placement="right",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "overflow": "visible",
                        },
                    ),
                    margin_top=True,
                    row_style_overrides={
                        "overflow": "visible",
                    },
                    control_wrapper_style_overrides={
                        "overflow": "visible",
                    },
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
                            max_value=self.default_values.detector_numerical_aperture,
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
                        "overflow": "visible",
                    },
                ),
            ],
            style={
                "flex": "1 1 520px",
                "minWidth": "480px",
                "overflow": "visible",
            },
        )

    def _build_optical_configuration_visualization(self) -> dbc.Card:
        """
        Build optical configuration preview graph.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    ui_forms.build_title_with_info(
                        title="Optical preview",
                        tooltip_target_id=self.optical_preview_tooltip_target_id,
                        tooltip_id=self.optical_preview_tooltip_id,
                        tooltip_text=(
                            "This preview visualizes the detector collection region "
                            "and blocker bar geometry from the current optical "
                            "configuration. It is only a geometric preview, not the "
                            "final Mie coupling curve."
                        ),
                        title_style_overrides={
                            "fontSize": "0.95rem",
                        },
                    ),
                    style={
                        "background": "rgba(128, 128, 128, 0.08)",
                        "borderBottom": "1px solid rgba(128, 128, 128, 0.18)",
                        "padding": "10px 14px",
                        "borderTopLeftRadius": "10px",
                        "borderTopRightRadius": "10px",
                    },
                ),
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
            ],
            style={
                "flex": "0 1 430px",
                "minWidth": "340px",
                "borderRadius": "10px",
                "overflow": "visible",
            },
        )

    def _build_particle_configuration_panel(self) -> dbc.Card:
        """
        Build the particle configuration subpanel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Particle configuration",
                            tooltip_target_id=self.particle_configuration_tooltip_target_id,
                            tooltip_id=self.particle_configuration_tooltip_id,
                            tooltip_text=(
                                "These controls define the particle model and refractive "
                                "indices used to compute the modeled optical coupling of "
                                "the calibration standard."
                            ),
                            title_style_overrides={
                                "fontSize": "1rem",
                            },
                        ),
                        dash.html.Div(
                            "Particle model and refractive index parameters.",
                            style=ui_forms.build_workflow_section_subtitle_style(),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.card_color,
                    ),
                ),
                dbc.CardBody(
                    self._build_particle_configuration_section(),
                    style=ui_forms.build_workflow_panel_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_particle_configuration_section(self) -> dash.html.Div:
        """
        Build particle configuration section.
        """
        return dash.html.Div(
            [
                ui_forms.build_inline_row(
                    label="Scatterer preset:",
                    control=dash.html.Div(
                        [
                            dash.dcc.Dropdown(
                                id=self.ids.scatterer_preset,
                                options=self.model_configuration.build_scatterer_preset_options(),
                                value=self.model_configuration.custom_scatterer_preset_name,
                                clearable=False,
                                searchable=False,
                                persistence=True,
                                persistence_type="session",
                                style={
                                    "width": "320px",
                                },
                            ),
                            ui_forms.build_info_badge(
                                tooltip_target_id=self.scatterer_preset_tooltip_target_id,
                            ),
                            dbc.Tooltip(
                                (
                                        "Use a scatterer preset to load a predefined bead set and "
                                        "matching refractive index defaults for calibration setup."
                                ),
                                id=self.scatterer_preset_tooltip_id,
                                target=self.scatterer_preset_tooltip_target_id,
                                placement="right",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "overflow": "visible",
                        },
                    ),
                    margin_top=False,
                    row_style_overrides={
                        "overflow": "visible",
                    },
                    control_wrapper_style_overrides={
                        "overflow": "visible",
                    },
                ),
                ui_forms.build_inline_row(
                    label="Particle type:",
                    control=dash.dcc.Dropdown(
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
                    row_style_overrides={
                        "overflow": "visible",
                    },
                    control_wrapper_style_overrides={
                        "overflow": "visible",
                    },
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
                    style=self._build_parameter_group_style(
                        is_visible=True,
                    ),
                ),
                dash.html.Div(
                    self._build_core_shell_parameters_block(),
                    id=self.ids.core_shell_container,
                    style=self._build_parameter_group_style(
                        is_visible=False,
                    ),
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "12px",
                "overflow": "visible",
            },
        )

    def _build_parameter_group_style(
        self,
        *,
        is_visible: bool,
    ) -> dict[str, str]:
        """
        Build a consistent layout style for model-specific parameter groups.
        """
        return {
            "display": "flex" if is_visible else "none",
            "flexDirection": "column",
            "gap": "12px",
            "overflow": "visible",
        }

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
        return ui_forms.build_inline_row(
            label=label,
            control=dash.dcc.Input(
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
            row_style_overrides={
                "overflow": "visible",
            },
            control_wrapper_style_overrides={
                "overflow": "visible",
            },
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

        return ui_forms.build_inline_row(
            label=label,
            control=dash.html.Div(
                [
                    preset_dropdown,
                    numeric_input,
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "overflow": "visible",
                },
            ),
            row_style_overrides={
                "overflow": "visible",
            },
            control_wrapper_style_overrides={
                "overflow": "visible",
            },
        )

    @staticmethod
    def _clamp_detector_cache_numerical_aperture(
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
    ) -> Any:
        """
        Keep detector cache numerical aperture within the detector aperture.
        """
        resolved_detector_numerical_aperture = casting.as_optional_float(
            detector_numerical_aperture
        )
        resolved_detector_cache_numerical_aperture = casting.as_optional_float(
            detector_cache_numerical_aperture
        )

        if resolved_detector_numerical_aperture is None:
            return detector_cache_numerical_aperture

        if resolved_detector_cache_numerical_aperture is None:
            return detector_cache_numerical_aperture

        strict_upper_bound = max(
            0.0,
            resolved_detector_numerical_aperture - DETECTOR_NUMERICAL_APERTURE_EPSILON,
        )

        if resolved_detector_cache_numerical_aperture < resolved_detector_numerical_aperture:
            return detector_cache_numerical_aperture

        logger.debug(
            "Clamping detector cache numerical aperture from %r to strict upper bound %r below detector numerical aperture %r.",
            detector_cache_numerical_aperture,
            strict_upper_bound,
            detector_numerical_aperture,
        )

        return strict_upper_bound

    def register_callbacks(self) -> None:
        """
        Register parameter callbacks.
        """
        logger.debug("Registering Parameters callbacks.")

        self._register_visibility_callbacks()
        self._register_scatterer_preset_callbacks()
        self._register_refractive_index_callbacks()
        self._register_detector_configuration_callbacks()
        self._register_optical_configuration_preview_callback()
        self._register_runtime_sync_callbacks()

    def _register_runtime_sync_callbacks(self) -> None:
        """
        Register runtime configuration synchronization callback.
        """

        @dash.callback(
            dash.Output(self.ids.scatterer_preset, "value"),
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

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            resolved_values = self.model_configuration.build_defaults_from_runtime_config(
                runtime_config_data,
            ).to_callback_values()

            resolved_detector_values = (
                self.model_configuration.resolve_detector_configuration_values(
                    preset_name=self.model_configuration.custom_detector_preset_name,
                    current_detector_numerical_aperture=resolved_values[6],
                    current_detector_cache_numerical_aperture=resolved_values[7],
                    current_blocker_bar_numerical_aperture=resolved_values[8],
                    current_detector_sampling=resolved_values[9],
                    current_detector_phi_angle_degree=resolved_values[10],
                    current_detector_gamma_angle_degree=resolved_values[11],
                )
            )

            resolved_values = (
                *resolved_values[:6],
                *resolved_detector_values,
            )

            scatterer_preset = self.model_configuration.resolve_runtime_scatterer_preset(
                runtime_config.get_str(
                    "particle_model.scatterer_preset",
                    default=self.model_configuration.custom_scatterer_preset_name,
                )
            )

            if scatterer_preset != self.model_configuration.custom_scatterer_preset_name:
                (
                    resolved_mie_model,
                    resolved_medium_refractive_index,
                    resolved_particle_refractive_index,
                    resolved_core_refractive_index,
                    resolved_shell_refractive_index,
                ) = self.model_configuration.resolve_scatterer_preset_values(
                    preset_name=scatterer_preset,
                    current_mie_model=resolved_values[0],
                    current_medium_refractive_index=resolved_values[1],
                    current_particle_refractive_index=resolved_values[2],
                    current_core_refractive_index=resolved_values[3],
                    current_shell_refractive_index=resolved_values[4],
                )

                resolved_values = (
                    resolved_mie_model,
                    resolved_medium_refractive_index,
                    resolved_particle_refractive_index,
                    resolved_core_refractive_index,
                    resolved_shell_refractive_index,
                    *resolved_values[5:],
                )

            resolved_values = (
                *resolved_values[:7],
                self._clamp_detector_cache_numerical_aperture(
                    resolved_values[6],
                    resolved_values[7],
                ),
                *resolved_values[8:],
            )

            logger.debug(
                "sync_parameters_from_runtime_config returning resolved_values=%r",
                resolved_values,
            )

            return (
                scatterer_preset,
                *resolved_values,
            )

    def _register_scatterer_preset_callbacks(self) -> None:
        """
        Register scatterer preset callbacks.
        """

        @dash.callback(
            dash.Output(self.ids.mie_model, "value", allow_duplicate=True),
            dash.Output(self.ids.medium_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.medium_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.particle_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.particle_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.core_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.core_refractive_index_custom, "value", allow_duplicate=True),
            dash.Output(self.ids.shell_refractive_index_source, "value", allow_duplicate=True),
            dash.Output(self.ids.shell_refractive_index_custom, "value", allow_duplicate=True),
            dash.Input(self.ids.scatterer_preset, "value"),
            dash.State(self.ids.mie_model, "value"),
            dash.State(self.ids.medium_refractive_index_custom, "value"),
            dash.State(self.ids.particle_refractive_index_custom, "value"),
            dash.State(self.ids.core_refractive_index_custom, "value"),
            dash.State(self.ids.shell_refractive_index_custom, "value"),
            prevent_initial_call=True,
        )
        def apply_scatterer_preset(
            preset_name: Any,
            current_mie_model: Any,
            current_medium_refractive_index: Any,
            current_particle_refractive_index: Any,
            current_core_refractive_index: Any,
            current_shell_refractive_index: Any,
        ) -> tuple[Any, ...]:
            logger.debug(
                "apply_scatterer_preset called with preset_name=%r",
                preset_name,
            )

            (
                resolved_mie_model,
                resolved_medium_refractive_index,
                resolved_particle_refractive_index,
                resolved_core_refractive_index,
                resolved_shell_refractive_index,
            ) = self.model_configuration.resolve_scatterer_preset_values(
                preset_name=preset_name,
                current_mie_model=current_mie_model,
                current_medium_refractive_index=current_medium_refractive_index,
                current_particle_refractive_index=current_particle_refractive_index,
                current_core_refractive_index=current_core_refractive_index,
                current_shell_refractive_index=current_shell_refractive_index,
            )

            return (
                resolved_mie_model,
                None,
                resolved_medium_refractive_index,
                None,
                resolved_particle_refractive_index,
                None,
                resolved_core_refractive_index,
                None,
                resolved_shell_refractive_index,
            )

        @dash.callback(
            dash.Output(self.ids.mie_model, "disabled"),
            dash.Output(self.ids.medium_refractive_index_source, "disabled"),
            dash.Output(self.ids.medium_refractive_index_custom, "disabled"),
            dash.Output(self.ids.particle_refractive_index_source, "disabled"),
            dash.Output(self.ids.particle_refractive_index_custom, "disabled"),
            dash.Output(self.ids.core_refractive_index_source, "disabled"),
            dash.Output(self.ids.core_refractive_index_custom, "disabled"),
            dash.Output(self.ids.shell_refractive_index_source, "disabled"),
            dash.Output(self.ids.shell_refractive_index_custom, "disabled"),
            dash.Input(self.ids.scatterer_preset, "value"),
            prevent_initial_call=False,
        )
        def sync_scatterer_preset_disabled_state(
            preset_name: Any,
        ) -> tuple[bool, ...]:
            is_locked = self.model_configuration.scatterer_preset_disables_manual_controls(
                preset_name=preset_name,
            )

            return (
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
                is_locked,
            )

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
            resolved_mie_model = self.model_configuration.resolve_mie_model(
                mie_model_value,
            )

            resolved_styles = (
                self._build_parameter_group_style(
                    is_visible=resolved_mie_model != "Core/Shell Sphere",
                ),
                self._build_parameter_group_style(
                    is_visible=resolved_mie_model == "Core/Shell Sphere",
                ),
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

            resolved_values = (
                resolved_values[0],
                self._clamp_detector_cache_numerical_aperture(
                    resolved_values[0],
                    resolved_values[1],
                ),
                *resolved_values[2:],
            )

            return resolved_values

        @dash.callback(
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "max",
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            prevent_initial_call=False,
        )
        def sync_detector_cache_numerical_aperture_max(
            detector_numerical_aperture: Any,
        ) -> Any:
            resolved_detector_numerical_aperture = casting.as_optional_float(
                detector_numerical_aperture
            )

            resolved_cache_max = None

            if resolved_detector_numerical_aperture is not None:
                resolved_cache_max = max(
                    0.0,
                    resolved_detector_numerical_aperture
                    - DETECTOR_NUMERICAL_APERTURE_EPSILON,
                )

            logger.debug(
                "sync_detector_cache_numerical_aperture_max called with detector_numerical_aperture=%r resolved_max=%r",
                detector_numerical_aperture,
                resolved_cache_max,
            )

            return resolved_cache_max

        @dash.callback(
            dash.Output(
                self.ids.detector_cache_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.detector_numerical_aperture, "value"),
            dash.State(self.ids.detector_cache_numerical_aperture, "value"),
            prevent_initial_call=True,
        )
        def clamp_detector_cache_numerical_aperture_after_detector_change(
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
        ) -> Any:
            resolved_detector_cache_numerical_aperture = (
                self._clamp_detector_cache_numerical_aperture(
                    detector_numerical_aperture,
                    detector_cache_numerical_aperture,
                )
            )

            if resolved_detector_cache_numerical_aperture == detector_cache_numerical_aperture:
                return dash.no_update

            return resolved_detector_cache_numerical_aperture

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