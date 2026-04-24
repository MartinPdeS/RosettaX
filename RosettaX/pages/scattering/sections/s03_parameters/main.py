# -*- coding: utf-8 -*-

from typing import Any, Optional, Sequence
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import styling

from . import services
from . import presets


logger = logging.getLogger(__name__)


class Parameters:
    """
    Scattering parameter section.

    Design
    ------
    The visible table is the source of truth for:
    - particle geometry
    - optional measured peak positions
    - expected coupling values

    This section:
    - renders source configuration
    - renders detector configuration
    - loads detector presets dynamically from JSON files
    - reloads detector presets manually with a button
    - keeps detector values editable when Custom detector is selected
    - hides manual detector values when a JSON backed detector preset is selected
    - keeps wavelength independent from detector presets
    - renders an interactive optical configuration preview
    - switches the visible table schema when the particle type changes
    - lets the user add rows
    - keeps the table internally consistent
    - computes expected coupling directly into the table
    """

    sphere_table_columns = services.sphere_table_columns
    core_shell_table_columns = services.core_shell_table_columns

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Parameters section with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_mie_model(self) -> str:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_str(
            "particle_model.mie_model",
            default="Solid Sphere",
        )

    def _get_default_wavelength_nm(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.wavelength_nm",
            default=700.0,
        )

    def _get_default_detector_numerical_aperture(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.detector_numerical_aperture",
            default=0.2,
        )

    def _get_default_blocker_bar_numerical_aperture(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.blocker_bar_numerical_aperture",
            default=0.0,
        )

    def _get_default_detector_sampling(self) -> int:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_int(
            "optics.detector_sampling",
            default=600,
        )

    def _get_default_detector_phi_angle_degree(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.detector_phi_angle_degree",
            default=0.0,
        )

    def _get_default_detector_gamma_angle_degree(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.detector_gamma_angle_degree",
            default=0.0,
        )

    def _get_default_medium_refractive_index(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "optics.medium_refractive_index",
            default=1.333,
        )

    def _get_default_particle_refractive_index(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "particle_model.particle_refractive_index",
            default=1.59,
        )

    def _get_default_core_refractive_index(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "particle_model.core_refractive_index",
            default=1.47,
        )

    def _get_default_shell_refractive_index(self) -> float:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_float(
            "particle_model.shell_refractive_index",
            default=1.46,
        )

    def get_layout(self) -> dbc.Card:
        logger.debug("Building Parameters layout.")
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
                dash.html.Hr(),
                self._build_reference_table_section(),
                dash.html.Div(style={"height": "12px"}),
                self._build_compute_model_block(),
            ]
        )

    def _build_detector_configuration_preset_refresh_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Reload detector presets",
            id=self.page.ids.Parameters.detector_configuration_preset_refresh_button,
            n_clicks=0,
            style={
                "marginLeft": "10px",
            },
        )

    def _build_optical_configuration_section(self) -> dash.html.Div:
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
        return dash.html.Div(
            [
                self._build_numeric_input_row(
                    label="Wavelength (nm):",
                    component_id=self.page.ids.Parameters.wavelength_nm,
                    placeholder="Wavelength (nm)",
                    value=self._get_default_wavelength_nm(),
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
                self._inline_row(
                    "Detector preset:",
                    dash.html.Div(
                        [
                            dash.dcc.Dropdown(
                                id=self.page.ids.Parameters.detector_configuration_preset,
                                options=services.build_detector_preset_options(),
                                value=services.CUSTOM_DETECTOR_PRESET_NAME,
                                placeholder="Select detector preset",
                                clearable=False,
                                searchable=False,
                                persistence=True,
                                persistence_type="session",
                                style={"width": "320px"},
                            ),
                            self._build_detector_configuration_preset_refresh_button(),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    margin_top=True,
                ),
                dash.html.Div(
                    [
                        self._build_numeric_input_row(
                            label="Detector NA:",
                            component_id=self.page.ids.Parameters.detector_numerical_aperture,
                            placeholder="Detector NA",
                            value=self._get_default_detector_numerical_aperture(),
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Blocker bar NA:",
                            component_id=self.page.ids.Parameters.blocker_bar_numerical_aperture,
                            placeholder="Blocker bar NA",
                            value=self._get_default_blocker_bar_numerical_aperture(),
                            min_value=0.0,
                            max_value=1.5,
                            step=0.001,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector sampling:",
                            component_id=self.page.ids.Parameters.detector_sampling,
                            placeholder="Detector sampling",
                            value=self._get_default_detector_sampling(),
                            min_value=1,
                            step=1,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector phi angle (deg):",
                            component_id=self.page.ids.Parameters.detector_phi_angle_degree,
                            placeholder="Detector phi angle",
                            value=self._get_default_detector_phi_angle_degree(),
                            min_value=-360.0,
                            max_value=360.0,
                            step=0.1,
                            width_px=220,
                        ),
                        self._build_numeric_input_row(
                            label="Detector gamma angle (deg):",
                            component_id=self.page.ids.Parameters.detector_gamma_angle_degree,
                            placeholder="Detector gamma angle",
                            value=self._get_default_detector_gamma_angle_degree(),
                            min_value=-360.0,
                            max_value=360.0,
                            step=0.1,
                            width_px=220,
                        ),
                    ],
                    id=self.page.ids.Parameters.detector_configuration_custom_values_container,
                    style={"display": "block"},
                ),
            ],
            style={
                "flex": "1 1 520px",
                "minWidth": "480px",
            },
        )

    def _build_optical_configuration_visualization(self) -> dbc.Card:
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.dcc.Graph(
                        id=self.page.ids.Parameters.optical_configuration_preview,
                        figure=services.build_optical_configuration_preview_figure(
                            detector_numerical_aperture=self._get_default_detector_numerical_aperture(),
                            blocker_bar_numerical_aperture=self._get_default_blocker_bar_numerical_aperture(),
                            medium_refractive_index=self._get_default_medium_refractive_index(),
                            detector_phi_angle_degree=self._get_default_detector_phi_angle_degree(),
                            detector_gamma_angle_degree=self._get_default_detector_gamma_angle_degree(),
                        ),
                        config={
                            "displayModeBar": False,
                            "scrollZoom": True,
                            "doubleClick": "reset",
                            "responsive": True,
                        },
                        className="optical-configuration-preview-graph",
                        style={
                            "height": "380px",
                            "width": "100%",
                            "touchAction": "auto",
                        },
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
        return dash.html.Div(
            [
                dash.html.H5("Particle configuration"),
                self._inline_row(
                    "Particle type:",
                    dash.dcc.Dropdown(
                        id=self.page.ids.Parameters.mie_model,
                        options=presets.MIE_MODEL_OPTIONS,
                        value=self._get_default_mie_model(),
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
                    default_value=self._get_default_medium_refractive_index(),
                    preset_options=presets.MEDIUM_REFRACTIVE_INDEX_PRESETS,
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
        return [
            self._refractive_index_picker(
                label="Particle refractive index:",
                preset_id=self.page.ids.Parameters.particle_refractive_index_source,
                value_id=self.page.ids.Parameters.particle_refractive_index_custom,
                default_value=self._get_default_particle_refractive_index(),
                preset_options=presets.PARTICLE_REFRACTIVE_INDEX_PRESETS,
            ),
        ]

    def _build_core_shell_parameters_block(self) -> list:
        return [
            self._refractive_index_picker(
                label="Core refractive index:",
                preset_id=self.page.ids.Parameters.core_refractive_index_source,
                value_id=self.page.ids.Parameters.core_refractive_index_custom,
                default_value=self._get_default_core_refractive_index(),
                preset_options=presets.CORE_REFRACTIVE_INDEX_PRESETS,
            ),
            self._refractive_index_picker(
                label="Shell refractive index:",
                preset_id=self.page.ids.Parameters.shell_refractive_index_source,
                value_id=self.page.ids.Parameters.shell_refractive_index_custom,
                default_value=self._get_default_shell_refractive_index(),
                preset_options=presets.SHELL_REFRACTIVE_INDEX_PRESETS,
            ),
        ]

    def _build_reference_table_section(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Calibration reference table"),
                dash.html.Div(
                    "The table is the source of truth. Edit the particle geometry directly here. "
                    "Measured peak positions are optional at this stage. "
                    "First click Compute Expected Coupling to fill the model column. "
                    "Then click Fit Calibration in the next section to generate the graphs and calibration.",
                    style={
                        "marginBottom": "10px",
                        "opacity": 0.8,
                    },
                ),
                dash.dash_table.DataTable(
                    id=self.page.ids.Calibration.bead_table,
                    columns=self.sphere_table_columns,
                    data=services.build_empty_rows_for_model(
                        "Solid Sphere",
                        row_count=3,
                    ),
                    **styling.DATATABLE,
                ),
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Add row",
                            id=self.page.ids.Calibration.add_row_btn,
                            n_clicks=0,
                        )
                    ],
                    style={
                        "marginTop": "10px",
                    },
                ),
            ]
        )

    def _build_compute_model_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_compute_model_button(),
                dash.html.Div(
                    "This step only fills the expected coupling column in the table.",
                    style={
                        "marginTop": "8px",
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_compute_model_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Compute Expected Coupling",
            id=self.page.ids.Calibration.compute_model_btn,
            n_clicks=0,
            style={
                "marginTop": "12px",
            },
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering Parameters callbacks.")
        self._register_visibility_callbacks()
        self._register_refractive_index_callbacks()
        self._register_detector_configuration_options_callback()
        self._register_detector_configuration_callbacks()
        self._register_optical_configuration_preview_callback()
        self._register_table_callbacks()
        self._register_compute_model_callback()
        self._register_post_compute_cleanup_callbacks()
        self._register_table_default_population_callback()
        self._register_runtime_sync_callbacks()

    def _register_runtime_sync_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Parameters.mie_model, "value"),
            dash.Output(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.Output(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.Output(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.Output(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.Output(self.page.ids.Parameters.detector_sampling, "value"),
            dash.Output(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.Output(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_parameters_from_runtime_config(runtime_config_data: Any):
            logger.debug(
                "sync_parameters_from_runtime_config called with runtime_config_data=%r",
                runtime_config_data,
            )

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            resolved_values = (
                runtime_config.get_str(
                    "particle_model.mie_model",
                    default="Solid Sphere",
                ),
                runtime_config.get_float(
                    "optics.medium_refractive_index",
                    default=1.333,
                ),
                runtime_config.get_float(
                    "particle_model.particle_refractive_index",
                    default=1.59,
                ),
                runtime_config.get_float(
                    "particle_model.core_refractive_index",
                    default=1.47,
                ),
                runtime_config.get_float(
                    "particle_model.shell_refractive_index",
                    default=1.46,
                ),
                runtime_config.get_float(
                    "optics.wavelength_nm",
                    default=700.0,
                ),
                runtime_config.get_float(
                    "optics.detector_numerical_aperture",
                    default=0.2,
                ),
                runtime_config.get_float(
                    "optics.blocker_bar_numerical_aperture",
                    default=0.0,
                ),
                runtime_config.get_int(
                    "optics.detector_sampling",
                    default=600,
                ),
                runtime_config.get_float(
                    "optics.detector_phi_angle_degree",
                    default=0.0,
                ),
                runtime_config.get_float(
                    "optics.detector_gamma_angle_degree",
                    default=0.0,
                ),
            )

            logger.debug(
                "sync_parameters_from_runtime_config returning resolved_values=%r",
                resolved_values,
            )

            return resolved_values

    def _register_table_default_population_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input("runtime-config-store", "data"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def populate_table_from_runtime_defaults_callback(
            runtime_config_data: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> Any:
            resolved_mie_model = services.resolve_mie_model(mie_model)
            normalized_current_rows = services.normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "populate_table_from_runtime_defaults called with resolved_mie_model=%r "
                "runtime_config_data=%r current_rows=%r",
                resolved_mie_model,
                runtime_config_data,
                normalized_current_rows,
            )

            if not services.table_is_effectively_empty(
                mie_model=resolved_mie_model,
                rows=normalized_current_rows,
            ):
                logger.debug("Table already contains user data. Leaving it unchanged.")
                return dash.no_update

            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            rows = services.populate_table_from_runtime_defaults(
                mie_model=resolved_mie_model,
                runtime_particle_diameters_nm=runtime_config.get_path(
                    "particle_model.particle_diameter_nm",
                    default=[],
                ),
                runtime_core_diameters_nm=runtime_config.get_path(
                    "particle_model.core_diameter_nm",
                    default=[],
                ),
                runtime_shell_thicknesses_nm=runtime_config.get_path(
                    "particle_model.shell_thickness_nm",
                    default=[],
                ),
            )

            logger.debug("Populated table from runtime defaults rows=%r", rows)

            return rows

    def _register_post_compute_cleanup_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "active_cell"),
            dash.Output(self.page.ids.Calibration.bead_table, "selected_cells"),
            dash.Input(self.page.ids.Calibration.compute_model_btn, "n_clicks"),
            prevent_initial_call=True,
        )
        def clear_table_selection_after_compute(_n_clicks: int) -> tuple[None, list]:
            logger.debug("Clearing bead table selection after Compute Expected Coupling.")
            return None, []

    def _register_visibility_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Parameters.solid_sphere_container, "style"),
            dash.Output(self.page.ids.Parameters.core_shell_container, "style"),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            prevent_initial_call=False,
        )
        def toggle_parameter_blocks(
            mie_model_value: Optional[str],
        ) -> tuple[dict[str, str], dict[str, str]]:
            resolved_mie_model = services.resolve_mie_model(mie_model_value)

            logger.debug(
                "toggle_parameter_blocks called with mie_model_value=%r resolved_mie_model=%r",
                mie_model_value,
                resolved_mie_model,
            )

            if resolved_mie_model == "Core/Shell Sphere":
                return {"display": "none"}, {"display": "block"}

            return {"display": "block"}, {"display": "none"}

    def _register_refractive_index_callbacks(self) -> None:
        def apply_preset_value(preset_value: Any, current_value: Any) -> Any:
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
        def apply_medium_preset(preset_value: Any, current_value: Any) -> Any:
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
        def apply_particle_preset(preset_value: Any, current_value: Any) -> Any:
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
        def apply_core_preset(preset_value: Any, current_value: Any) -> Any:
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
        def apply_shell_preset(preset_value: Any, current_value: Any) -> Any:
            return apply_preset_value(preset_value, current_value)

    def _register_detector_configuration_options_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.detector_configuration_preset,
                "options",
            ),
            dash.Input(
                self.page.ids.Parameters.detector_configuration_preset_refresh_button,
                "n_clicks",
            ),
            prevent_initial_call=False,
        )
        def refresh_detector_configuration_preset_options(
            n_clicks: int,
        ) -> list[dict[str, str]]:
            logger.debug(
                "refresh_detector_configuration_preset_options called with n_clicks=%r",
                n_clicks,
            )

            options = services.build_detector_preset_options()

            logger.debug(
                "refresh_detector_configuration_preset_options returning option_count=%d options=%r",
                len(options),
                options,
            )

            return options

    def _register_detector_configuration_callbacks(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.detector_configuration_custom_values_container,
                "style",
            ),
            dash.Input(self.page.ids.Parameters.detector_configuration_preset, "value"),
            prevent_initial_call=False,
        )
        def toggle_detector_configuration_custom_values(
            preset_name: Any,
        ) -> dict[str, str]:
            logger.debug(
                "toggle_detector_configuration_custom_values called with preset_name=%r",
                preset_name,
            )

            return services.resolve_detector_configuration_visibility_style(
                preset_name=preset_name,
            )

        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.detector_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Parameters.blocker_bar_numerical_aperture,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Parameters.detector_sampling,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Parameters.detector_phi_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Parameters.detector_gamma_angle_degree,
                "value",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.detector_configuration_preset, "value"),
            dash.Input(
                self.page.ids.Parameters.detector_configuration_preset_refresh_button,
                "n_clicks",
            ),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            dash.State(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.State(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
            prevent_initial_call=True,
        )
        def apply_detector_configuration_preset(
            preset_name: Any,
            n_clicks: int,
            current_detector_numerical_aperture: Any,
            current_blocker_bar_numerical_aperture: Any,
            current_detector_sampling: Any,
            current_detector_phi_angle_degree: Any,
            current_detector_gamma_angle_degree: Any,
        ) -> tuple[Any, Any, Any, Any, Any]:
            logger.debug(
                "apply_detector_configuration_preset called with preset_name=%r "
                "n_clicks=%r current_values=%r",
                preset_name,
                n_clicks,
                (
                    current_detector_numerical_aperture,
                    current_blocker_bar_numerical_aperture,
                    current_detector_sampling,
                    current_detector_phi_angle_degree,
                    current_detector_gamma_angle_degree,
                ),
            )

            resolved_values = services.resolve_detector_configuration_values(
                preset_name=preset_name,
                current_detector_numerical_aperture=current_detector_numerical_aperture,
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
        @dash.callback(
            dash.Output(
                self.page.ids.Parameters.optical_configuration_preview,
                "figure",
            ),
            dash.Input(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.Input(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.Input(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.Input(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.Input(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
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

            return services.build_optical_configuration_preview_figure(
                detector_numerical_aperture=detector_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                medium_refractive_index=medium_refractive_index,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
            )

    def _register_table_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "columns"),
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def sync_table_schema_from_model(
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
            resolved_mie_model = services.resolve_mie_model(mie_model)
            next_columns = services.get_table_columns_for_model(resolved_mie_model)
            next_rows = services.remap_table_rows_to_model(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "sync_table_schema_from_model returning resolved_mie_model=%r "
                "column_count=%d row_count=%d",
                resolved_mie_model,
                len(next_columns),
                len(next_rows),
            )

            return next_columns, next_rows

        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def add_row(
            n_clicks: int,
            mie_model: Any,
            rows: Optional[list[dict[str, Any]]],
        ) -> list[dict[str, str]]:
            logger.debug(
                "add_row called with n_clicks=%r mie_model=%r row_count=%r",
                n_clicks,
                mie_model,
                None if rows is None else len(rows),
            )

            resolved_mie_model = services.resolve_mie_model(mie_model)
            next_rows = [dict(row) for row in (rows or [])]
            next_rows.append(services.build_empty_row_for_model(resolved_mie_model))

            logger.debug(
                "add_row returning resolved_mie_model=%r new_row_count=%d",
                resolved_mie_model,
                len(next_rows),
            )

            return next_rows

        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Calibration.bead_table, "data_timestamp"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            prevent_initial_call=True,
        )
        def normalize_table_after_user_edit(
            data_timestamp: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> list[dict[str, str]]:
            logger.debug(
                "normalize_table_after_user_edit called with data_timestamp=%r "
                "mie_model=%r row_count=%r",
                data_timestamp,
                mie_model,
                None if current_rows is None else len(current_rows),
            )

            resolved_mie_model = services.resolve_mie_model(mie_model)

            normalized_rows = services.normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "normalize_table_after_user_edit returning resolved_mie_model=%r row_count=%d",
                resolved_mie_model,
                len(normalized_rows),
            )

            return normalized_rows

    def _register_compute_model_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Calibration.compute_model_btn, "n_clicks"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            dash.State(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.State(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
            prevent_initial_call=True,
        )
        def compute_model(
            n_clicks: int,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
            medium_refractive_index: Any,
            particle_refractive_index: Any,
            core_refractive_index: Any,
            shell_refractive_index: Any,
            wavelength_nm: Any,
            detector_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            detector_sampling: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
        ) -> list[dict[str, str]]:
            logger.debug(
                "compute_model called with n_clicks=%r mie_model=%r row_count=%r "
                "medium_refractive_index=%r particle_refractive_index=%r "
                "core_refractive_index=%r shell_refractive_index=%r wavelength_nm=%r "
                "detector_numerical_aperture=%r blocker_bar_numerical_aperture=%r "
                "detector_sampling=%r detector_phi_angle_degree=%r "
                "detector_gamma_angle_degree=%r",
                n_clicks,
                mie_model,
                None if current_rows is None else len(current_rows),
                medium_refractive_index,
                particle_refractive_index,
                core_refractive_index,
                shell_refractive_index,
                wavelength_nm,
                detector_numerical_aperture,
                blocker_bar_numerical_aperture,
                detector_sampling,
                detector_phi_angle_degree,
                detector_gamma_angle_degree,
            )

            resolved_mie_model = services.resolve_mie_model(mie_model)

            if not current_rows:
                logger.debug(
                    "compute_model found no rows. Returning empty rows for model=%r",
                    resolved_mie_model,
                )
                return services.build_empty_rows_for_model(
                    resolved_mie_model,
                    row_count=3,
                )

            return services.compute_model_for_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
                medium_refractive_index=medium_refractive_index,
                particle_refractive_index=particle_refractive_index,
                core_refractive_index=core_refractive_index,
                shell_refractive_index=shell_refractive_index,
                wavelength_nm=wavelength_nm,
                detector_numerical_aperture=detector_numerical_aperture,
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                detector_sampling=detector_sampling,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
                logger=logger,
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
                debounce=True,
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