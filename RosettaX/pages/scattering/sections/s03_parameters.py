# -*- coding: utf-8 -*-

from typing import Any, Optional, Sequence
import logging

import dash
import dash_bootstrap_components as dbc
import numpy as np

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import styling


logger = logging.getLogger(__name__)


class Parameters:
    """
    Scattering parameter section.

    Design
    ------
    The visible table is the single source of truth for:
    - particle geometry
    - optional measured peak positions
    - expected coupling values

    This section:
    - renders the optical and refractive index controls
    - switches the visible table schema when the particle type changes
    - lets the user add rows
    - keeps the table internally consistent
    - computes model coupling directly into the table

    Notes
    -----
    - Measured peak positions are optional for model computation.
    - Compute model only fills the expected coupling column.
    - The table remains editable and persistent across the session.
    """

    sphere_table_columns = [
        {"name": "Particle diameter [nm]", "id": "particle_diameter_nm", "editable": True},
        {"name": "Measured peak position [a.u.] (optional)", "id": "measured_peak_position", "editable": True},
        {"name": "Expected coupling", "id": "expected_coupling", "editable": False},
    ]

    core_shell_table_columns = [
        {"name": "Core diameter [nm]", "id": "core_diameter_nm", "editable": True},
        {"name": "Shell thickness [nm]", "id": "shell_thickness_nm", "editable": True},
        {"name": "Outer diameter [nm]", "id": "outer_diameter_nm", "editable": False},
        {"name": "Measured peak position [a.u.] (optional)", "id": "measured_peak_position", "editable": True},
        {"name": "Expected coupling", "id": "expected_coupling", "editable": False},
    ]

    def __init__(self, page) -> None:
        self.page = page
        self.runtime_config = RuntimeConfig()
        self.default = self.runtime_config.Default
        logger.debug("Initialized Parameters section with page=%r", page)

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
                self._build_compute_model_button(),
            ]
        )

    def _build_optical_configuration_section(self) -> dash.html.Div:
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
                        persistence=True,
                        persistence_type="session",
                        style={"width": "320px"},
                    ),
                    margin_top=False,
                ),
                self._build_numeric_input_row(
                    label="Wavelength (nm):",
                    component_id=self.page.ids.Parameters.wavelength_nm,
                    placeholder="Wavelength (nm)",
                    value=getattr(self.default, "wavelength_nm", 700.0),
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector NA:",
                    component_id=self.page.ids.Parameters.detector_numerical_aperture,
                    placeholder="Detector NA",
                    value=getattr(self.default, "detector_numerical_aperture", 0.2),
                    min_value=0.0,
                    max_value=1.5,
                    step=0.001,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector cache NA:",
                    component_id=self.page.ids.Parameters.detector_cache_numerical_aperture,
                    placeholder="Detector cache NA",
                    value=getattr(self.default, "detector_cache_numerical_aperture", 0.2),
                    min_value=0.0,
                    max_value=1.5,
                    step=0.001,
                    width_px=220,
                ),
                self._build_numeric_input_row(
                    label="Detector sampling:",
                    component_id=self.page.ids.Parameters.detector_sampling,
                    placeholder="Detector sampling",
                    value=getattr(self.default, "detector_sampling", 600),
                    min_value=1,
                    step=1,
                    width_px=220,
                ),
            ]
        )

    def _build_particle_configuration_section(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Particle configuration"),
                self._inline_row(
                    "Particle type:",
                    dash.dcc.Dropdown(
                        id=self.page.ids.Parameters.mie_model,
                        options=self._get_mie_model_options(),
                        value=getattr(self.default, "mie_model", "Solid Sphere"),
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
                    default_value=getattr(self.default, "medium_refractive_index", 1.333),
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
        return [
            self._refractive_index_picker(
                label="Particle refractive index:",
                preset_id=self.page.ids.Parameters.particle_refractive_index_source,
                value_id=self.page.ids.Parameters.particle_refractive_index_custom,
                default_value=getattr(self.default, "particle_refractive_index", 1.59),
                preset_options=self._get_particle_refractive_index_presets(),
            ),
        ]

    def _build_core_shell_parameters_block(self) -> list:
        return [
            self._refractive_index_picker(
                label="Core refractive index:",
                preset_id=self.page.ids.Parameters.core_refractive_index_source,
                value_id=self.page.ids.Parameters.core_refractive_index_custom,
                default_value=getattr(self.default, "core_refractive_index", 1.47),
                preset_options=self._get_core_refractive_index_presets(),
            ),
            self._refractive_index_picker(
                label="Shell refractive index:",
                preset_id=self.page.ids.Parameters.shell_refractive_index_source,
                value_id=self.page.ids.Parameters.shell_refractive_index_custom,
                default_value=getattr(self.default, "shell_refractive_index", 1.46),
                preset_options=self._get_shell_refractive_index_presets(),
            ),
        ]

    def _build_reference_table_section(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Calibration reference table"),
                dash.html.Div(
                    "The table is the source of truth. Edit the particle geometry directly here. "
                    "Measured peak positions are optional at this stage. "
                    "Click Compute model to fill only the expected coupling column.",
                    style={"marginBottom": "10px", "opacity": 0.8},
                ),
                dash.dash_table.DataTable(
                    id=self.page.ids.Calibration.bead_table,
                    columns=self.sphere_table_columns,
                    data=self._build_empty_rows_for_model("Solid Sphere", row_count=3),
                    **styling.DATATABLE
                ),
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Add row",
                            id=self.page.ids.Calibration.add_row_btn,
                            n_clicks=0,
                        )
                    ],
                    style={"marginTop": "10px"},
                ),
            ]
        )

    def _build_compute_model_button(self) -> dash.html.Button:
        return dash.html.Button(
            "Compute model",
            id=self.page.ids.Calibration.compute_model_btn,
            n_clicks=0,
            style={"marginTop": "12px"},
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering Parameters callbacks.")
        self._register_visibility_callbacks()
        self._register_refractive_index_callbacks()
        self._register_optical_configuration_callbacks()
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
            dash.Output(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.Output(self.page.ids.Parameters.detector_sampling, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_parameters_from_runtime_config(runtime_config_data: Any):
            logger.debug(
                "sync_parameters_from_runtime_config called with runtime_config_data=%r",
                runtime_config_data,
            )

            if not isinstance(runtime_config_data, dict):
                resolved_values = (
                    self.default.mie_model,
                    self.default.medium_refractive_index,
                    self.default.particle_refractive_index,
                    self.default.core_refractive_index,
                    self.default.shell_refractive_index,
                    self.default.wavelength_nm,
                    self.default.detector_numerical_aperture,
                    self.default.detector_cache_numerical_aperture,
                    self.default.detector_sampling,
                )
                logger.debug(
                    "runtime_config_data is not a dict. Returning Default values=%r",
                    resolved_values,
                )
                return resolved_values

            resolved_values = (
                runtime_config_data.get("mie_model", self.default.mie_model),
                runtime_config_data.get("medium_refractive_index", self.default.medium_refractive_index),
                runtime_config_data.get("particle_refractive_index", self.default.particle_refractive_index),
                runtime_config_data.get("core_refractive_index", self.default.core_refractive_index),
                runtime_config_data.get("shell_refractive_index", self.default.shell_refractive_index),
                runtime_config_data.get("wavelength_nm", self.default.wavelength_nm),
                runtime_config_data.get("detector_numerical_aperture", self.default.detector_numerical_aperture),
                runtime_config_data.get("detector_cache_numerical_aperture", self.default.detector_cache_numerical_aperture),
                runtime_config_data.get("detector_sampling", self.default.detector_sampling),
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
        def populate_table_from_runtime_defaults(
            runtime_config_data: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> Any:
            resolved_mie_model = self._resolve_mie_model(mie_model)
            normalized_current_rows = self._normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "populate_table_from_runtime_defaults called with resolved_mie_model=%r runtime_config_data=%r current_rows=%r",
                resolved_mie_model,
                runtime_config_data,
                normalized_current_rows,
            )

            if not self._table_is_effectively_empty(
                mie_model=resolved_mie_model,
                rows=normalized_current_rows,
            ):
                logger.debug("Table already contains user data. Leaving it unchanged.")
                return dash.no_update

            if not isinstance(runtime_config_data, dict):
                logger.debug("No runtime config data available.")
                return dash.no_update

            if resolved_mie_model == "Core/Shell Sphere":
                core_diameters_nm = self._as_float_list_from_runtime_value(
                    runtime_config_data.get("core_diameter_nm", runtime_config_data.get("core_diameter", "")),
                )
                shell_thicknesses_nm = self._as_float_list_from_runtime_value(
                    runtime_config_data.get("shell_thickness_nm", runtime_config_data.get("shell_thickness", "")),
                )

                row_count = max(3, len(core_diameters_nm), len(shell_thicknesses_nm))
                rows: list[dict[str, str]] = []

                for index in range(row_count):
                    core_value = (
                        f"{float(core_diameters_nm[index]):.6g}"
                        if index < len(core_diameters_nm)
                        else ""
                    )
                    shell_value = (
                        f"{float(shell_thicknesses_nm[index]):.6g}"
                        if index < len(shell_thicknesses_nm)
                        else ""
                    )

                    rows.append(
                        {
                            "core_diameter_nm": core_value,
                            "shell_thickness_nm": shell_value,
                            "outer_diameter_nm": self._compute_outer_diameter_string(
                                core_diameter_nm=core_value,
                                shell_thickness_nm=shell_value,
                            ),
                            "measured_peak_position": "",
                            "expected_coupling": "",
                        }
                    )

                logger.debug("Populated core shell table from runtime defaults rows=%r", rows)
                return rows

            particle_diameters_nm = self._as_float_list_from_runtime_value(
                runtime_config_data.get("particle_diameter_nm", runtime_config_data.get("particle_diameter", "")),
            )

            row_count = max(3, len(particle_diameters_nm))
            rows = []

            for index in range(row_count):
                particle_value = (
                    f"{float(particle_diameters_nm[index]):.6g}"
                    if index < len(particle_diameters_nm)
                    else ""
                )
                rows.append(
                    {
                        "particle_diameter_nm": particle_value,
                        "measured_peak_position": "",
                        "expected_coupling": "",
                    }
                )

            logger.debug("Populated solid sphere table from runtime defaults rows=%r", rows)
            return rows


    def _register_post_compute_cleanup_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "active_cell"),
            dash.Output(self.page.ids.Calibration.bead_table, "selected_cells"),
            dash.Input(self.page.ids.Calibration.compute_model_btn, "n_clicks"),
            prevent_initial_call=True,
        )
        def clear_table_selection_after_compute(_n_clicks: int) -> tuple[None, list]:
            logger.debug("Clearing bead table selection after Compute model.")
            return None, []

    def _register_visibility_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Parameters.solid_sphere_container, "style"),
            dash.Output(self.page.ids.Parameters.core_shell_container, "style"),
            dash.Input(self.page.ids.Parameters.mie_model, "value"),
            prevent_initial_call=False,
        )
        def toggle_parameter_blocks(mie_model_value: Optional[str]) -> tuple[dict[str, str], dict[str, str]]:
            resolved_mie_model = self._resolve_mie_model(mie_model_value)
            logger.debug("toggle_parameter_blocks called with resolved_mie_model=%r", resolved_mie_model)

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

    def _register_optical_configuration_callbacks(self) -> None:
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
        ) -> tuple[Any, Any, Any, Any]:
            logger.debug("apply_optical_configuration_preset called with preset_name=%r", preset_name)

            if preset_name is None:
                return (
                    current_wavelength_nm,
                    current_detector_numerical_aperture,
                    current_detector_cache_numerical_aperture,
                    current_detector_sampling,
                )

            preset = self._get_optical_configuration_presets().get(str(preset_name), {})

            resolved_values = (
                preset.get("wavelength_nm", current_wavelength_nm),
                preset.get("detector_numerical_aperture", current_detector_numerical_aperture),
                preset.get("detector_cache_numerical_aperture", current_detector_cache_numerical_aperture),
                preset.get("detector_sampling", current_detector_sampling),
            )

            logger.debug("apply_optical_configuration_preset returning values=%r", resolved_values)
            return resolved_values

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
            resolved_mie_model = self._resolve_mie_model(mie_model)
            next_columns = self._get_table_columns_for_model(resolved_mie_model)
            next_rows = self._remap_table_rows_to_model(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "sync_table_schema_from_model resolved_mie_model=%r row_count=%r rows=%r",
                resolved_mie_model,
                len(next_rows),
                next_rows,
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
            del n_clicks

            resolved_mie_model = self._resolve_mie_model(mie_model)
            next_rows = [dict(row) for row in (rows or [])]
            next_rows.append(self._build_empty_row_for_model(resolved_mie_model))

            logger.debug(
                "add_row resolved_mie_model=%r new_row_count=%r rows=%r",
                resolved_mie_model,
                len(next_rows),
                next_rows,
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
            _data_timestamp: Any,
            mie_model: Any,
            current_rows: Optional[list[dict[str, Any]]],
        ) -> list[dict[str, str]]:
            del _data_timestamp

            resolved_mie_model = self._resolve_mie_model(mie_model)
            normalized_rows = self._normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=current_rows,
            )

            logger.debug(
                "normalize_table_after_user_edit resolved_mie_model=%r row_count=%r rows=%r",
                resolved_mie_model,
                len(normalized_rows),
                normalized_rows,
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
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
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
            detector_cache_numerical_aperture: Any,
            detector_sampling: Any,
        ) -> list[dict[str, str]]:
            logger.debug(
                "compute_model called with n_clicks=%r mie_model=%r row_count=%r current_rows=%r",
                n_clicks,
                mie_model,
                None if current_rows is None else len(current_rows),
                current_rows,
            )

            resolved_rows = [dict(row) for row in (current_rows or [])]
            resolved_mie_model = self._resolve_mie_model(mie_model)

            if not resolved_rows:
                logger.debug("compute_model found no rows. Returning empty model-specific defaults.")
                return self._build_empty_rows_for_model(resolved_mie_model, row_count=3)

            try:
                resolved_medium_refractive_index = self._as_required_float(
                    medium_refractive_index,
                    "medium_refractive_index",
                )
                resolved_wavelength_nm = self._as_required_float(
                    wavelength_nm,
                    "wavelength_nm",
                )
                resolved_detector_numerical_aperture = self._as_required_float(
                    detector_numerical_aperture,
                    "detector_numerical_aperture",
                )
                resolved_detector_cache_numerical_aperture = self._as_required_float(
                    detector_cache_numerical_aperture,
                    "detector_cache_numerical_aperture",
                )
                resolved_detector_sampling = self._as_required_int(
                    detector_sampling,
                    "detector_sampling",
                )
            except Exception:
                logger.exception("compute_model aborted because optical parameters are invalid.")
                return self._normalize_table_rows(
                    mie_model=resolved_mie_model,
                    current_rows=resolved_rows,
                )

            logger.debug(
                "compute_model resolved optical parameters medium_refractive_index=%r wavelength_nm=%r detector_numerical_aperture=%r detector_cache_numerical_aperture=%r detector_sampling=%r",
                resolved_medium_refractive_index,
                resolved_wavelength_nm,
                resolved_detector_numerical_aperture,
                resolved_detector_cache_numerical_aperture,
                resolved_detector_sampling,
            )

            backend = BackEnd(
                fcs_file_path="",
                detector_column="",
            )

            if resolved_mie_model == "Core/Shell Sphere":
                logger.debug("compute_model running in Core/Shell Sphere mode.")
                try:
                    _resolved_core_refractive_index = self._as_required_float(
                        core_refractive_index,
                        "core_refractive_index",
                    )
                    resolved_shell_refractive_index = self._as_required_float(
                        shell_refractive_index,
                        "shell_refractive_index",
                    )
                except Exception:
                    logger.exception("compute_model aborted because core/shell refractive indices are invalid.")
                    return self._normalize_table_rows(
                        mie_model=resolved_mie_model,
                        current_rows=resolved_rows,
                    )

                valid_row_indices: list[int] = []
                outer_diameters_nm: list[float] = []

                updated_rows = self._normalize_table_rows(
                    mie_model=resolved_mie_model,
                    current_rows=resolved_rows,
                )

                for row_index, row in enumerate(updated_rows):
                    outer_diameter_nm = self._as_optional_float(row.get("outer_diameter_nm"))
                    if outer_diameter_nm is None or outer_diameter_nm <= 0.0:
                        updated_rows[row_index]["expected_coupling"] = ""
                        continue

                    valid_row_indices.append(row_index)
                    outer_diameters_nm.append(float(outer_diameter_nm))

                logger.debug(
                    "compute_model core-shell valid_row_indices=%r outer_diameters_nm=%r",
                    valid_row_indices,
                    outer_diameters_nm,
                )

                if not outer_diameters_nm:
                    logger.debug("compute_model found no valid core-shell rows.")
                    return updated_rows

                try:
                    modeled_coupling_result = backend.compute_modeled_coupling_from_diameters(
                        particle_diameters_nm=np.asarray(outer_diameters_nm, dtype=float),
                        wavelength_nm=resolved_wavelength_nm,
                        source_numerical_aperture=0.1,
                        optical_power_watt=1.0,
                        detector_numerical_aperture=resolved_detector_numerical_aperture,
                        medium_refractive_index=resolved_medium_refractive_index,
                        particle_refractive_index=resolved_shell_refractive_index,
                        detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
                        detector_phi_offset_degree=0.0,
                        detector_gamma_offset_degree=0.0,
                        polarization_angle_degree=0.0,
                        detector_sampling=resolved_detector_sampling,
                    )
                except Exception:
                    logger.exception("compute_model failed during core-shell outer-diameter approximation.")
                    return updated_rows

                for row_index, expected_coupling in zip(
                    valid_row_indices,
                    modeled_coupling_result.expected_coupling_values,
                    strict=False,
                ):
                    updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

                logger.debug("compute_model returning updated core-shell rows=%r", updated_rows)
                return updated_rows

            logger.debug("compute_model running in Solid Sphere mode.")

            try:
                resolved_particle_refractive_index = self._as_required_float(
                    particle_refractive_index,
                    "particle_refractive_index",
                )
            except Exception:
                logger.exception("compute_model aborted because particle refractive index is invalid.")
                return self._normalize_table_rows(
                    mie_model=resolved_mie_model,
                    current_rows=resolved_rows,
                )

            valid_row_indices = []
            particle_diameters_nm = []

            updated_rows = self._normalize_table_rows(
                mie_model=resolved_mie_model,
                current_rows=resolved_rows,
            )

            for row_index, row in enumerate(updated_rows):
                particle_diameter_nm = self._as_optional_float(row.get("particle_diameter_nm"))
                if particle_diameter_nm is None or particle_diameter_nm <= 0.0:
                    updated_rows[row_index]["expected_coupling"] = ""
                    continue

                valid_row_indices.append(row_index)
                particle_diameters_nm.append(float(particle_diameter_nm))

            logger.debug(
                "compute_model solid-sphere valid_row_indices=%r particle_diameters_nm=%r",
                valid_row_indices,
                particle_diameters_nm,
            )

            if not particle_diameters_nm:
                logger.debug("compute_model found no valid solid-sphere rows.")
                return updated_rows

            try:
                modeled_coupling_result = backend.compute_modeled_coupling_from_diameters(
                    particle_diameters_nm=np.asarray(particle_diameters_nm, dtype=float),
                    wavelength_nm=resolved_wavelength_nm,
                    source_numerical_aperture=0.1,
                    optical_power_watt=1.0,
                    detector_numerical_aperture=resolved_detector_numerical_aperture,
                    medium_refractive_index=resolved_medium_refractive_index,
                    particle_refractive_index=resolved_particle_refractive_index,
                    detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
                    detector_phi_offset_degree=0.0,
                    detector_gamma_offset_degree=0.0,
                    polarization_angle_degree=0.0,
                    detector_sampling=resolved_detector_sampling,
                )
            except Exception:
                logger.exception("compute_model failed during solid-sphere coupling computation.")
                return updated_rows

            for row_index, expected_coupling in zip(
                valid_row_indices,
                modeled_coupling_result.expected_coupling_values,
                strict=False,
            ):
                updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

            logger.debug("compute_model returning updated solid-sphere rows=%r", updated_rows)
            return updated_rows

    def _resolve_mie_model(self, mie_model: Any) -> str:
        mie_model_string = "" if mie_model is None else str(mie_model).strip()
        return "Core/Shell Sphere" if mie_model_string == "Core/Shell Sphere" else "Solid Sphere"

    def _get_table_columns_for_model(self, mie_model: str) -> list[dict[str, Any]]:
        return list(self.core_shell_table_columns) if mie_model == "Core/Shell Sphere" else list(self.sphere_table_columns)

    def _build_empty_row_for_model(self, mie_model: str) -> dict[str, str]:
        if mie_model == "Core/Shell Sphere":
            return {
                "core_diameter_nm": "",
                "shell_thickness_nm": "",
                "outer_diameter_nm": "",
                "measured_peak_position": "",
                "expected_coupling": "",
            }

        return {
            "particle_diameter_nm": "",
            "measured_peak_position": "",
            "expected_coupling": "",
        }

    def _build_empty_rows_for_model(self, mie_model: str, row_count: int) -> list[dict[str, str]]:
        return [self._build_empty_row_for_model(mie_model) for _ in range(int(row_count))]

    def _remap_table_rows_to_model(
        self,
        *,
        mie_model: str,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, str]]:
        resolved_current_rows = [dict(row) for row in (current_rows or [])]
        row_count = max(3, len(resolved_current_rows))
        remapped_rows: list[dict[str, str]] = []

        if mie_model == "Core/Shell Sphere":
            for row_index in range(row_count):
                source_row = resolved_current_rows[row_index] if row_index < len(resolved_current_rows) else {}

                particle_diameter_nm = self._normalize_editable_cell(source_row.get("particle_diameter_nm"))
                core_diameter_nm = self._normalize_editable_cell(source_row.get("core_diameter_nm"))
                shell_thickness_nm = self._normalize_editable_cell(source_row.get("shell_thickness_nm"))
                measured_peak_position = self._normalize_editable_cell(source_row.get("measured_peak_position"))
                expected_coupling = self._normalize_readonly_cell(source_row.get("expected_coupling"))

                if not core_diameter_nm and particle_diameter_nm:
                    core_diameter_nm = particle_diameter_nm

                outer_diameter_nm = self._compute_outer_diameter_string(
                    core_diameter_nm=core_diameter_nm,
                    shell_thickness_nm=shell_thickness_nm,
                )

                remapped_rows.append(
                    {
                        "core_diameter_nm": core_diameter_nm,
                        "shell_thickness_nm": shell_thickness_nm,
                        "outer_diameter_nm": outer_diameter_nm,
                        "measured_peak_position": measured_peak_position,
                        "expected_coupling": expected_coupling,
                    }
                )

            return remapped_rows

        for row_index in range(row_count):
            source_row = resolved_current_rows[row_index] if row_index < len(resolved_current_rows) else {}

            particle_diameter_nm = self._normalize_editable_cell(source_row.get("particle_diameter_nm"))
            core_diameter_nm = self._normalize_editable_cell(source_row.get("core_diameter_nm"))
            outer_diameter_nm = self._normalize_editable_cell(source_row.get("outer_diameter_nm"))
            measured_peak_position = self._normalize_editable_cell(source_row.get("measured_peak_position"))
            expected_coupling = self._normalize_readonly_cell(source_row.get("expected_coupling"))

            if not particle_diameter_nm:
                if outer_diameter_nm:
                    particle_diameter_nm = outer_diameter_nm
                elif core_diameter_nm:
                    particle_diameter_nm = core_diameter_nm

            remapped_rows.append(
                {
                    "particle_diameter_nm": particle_diameter_nm,
                    "measured_peak_position": measured_peak_position,
                    "expected_coupling": expected_coupling,
                }
            )

        return remapped_rows

    def _normalize_table_rows(
        self,
        *,
        mie_model: str,
        current_rows: Optional[list[dict[str, Any]]],
    ) -> list[dict[str, str]]:
        resolved_current_rows = [dict(row) for row in (current_rows or [])]

        if mie_model == "Core/Shell Sphere":
            normalized_rows: list[dict[str, str]] = []

            for source_row in resolved_current_rows:
                core_diameter_nm = self._normalize_editable_cell(source_row.get("core_diameter_nm"))
                shell_thickness_nm = self._normalize_editable_cell(source_row.get("shell_thickness_nm"))
                measured_peak_position = self._normalize_editable_cell(source_row.get("measured_peak_position"))
                expected_coupling = self._normalize_readonly_cell(source_row.get("expected_coupling"))

                outer_diameter_nm = self._compute_outer_diameter_string(
                    core_diameter_nm=core_diameter_nm,
                    shell_thickness_nm=shell_thickness_nm,
                )

                normalized_rows.append(
                    {
                        "core_diameter_nm": core_diameter_nm,
                        "shell_thickness_nm": shell_thickness_nm,
                        "outer_diameter_nm": outer_diameter_nm,
                        "measured_peak_position": measured_peak_position,
                        "expected_coupling": expected_coupling,
                    }
                )

            return normalized_rows

        normalized_rows: list[dict[str, str]] = []

        for source_row in resolved_current_rows:
            normalized_rows.append(
                {
                    "particle_diameter_nm": self._normalize_editable_cell(source_row.get("particle_diameter_nm")),
                    "measured_peak_position": self._normalize_editable_cell(source_row.get("measured_peak_position")),
                    "expected_coupling": self._normalize_readonly_cell(source_row.get("expected_coupling")),
                }
            )

        return normalized_rows

    def _normalize_editable_cell(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_readonly_cell(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _compute_outer_diameter_string(
        self,
        *,
        core_diameter_nm: Any,
        shell_thickness_nm: Any,
    ) -> str:
        try:
            resolved_core_diameter_nm = float(core_diameter_nm)
            resolved_shell_thickness_nm = float(shell_thickness_nm)
        except Exception:
            return ""

        if resolved_core_diameter_nm <= 0.0 or resolved_shell_thickness_nm < 0.0:
            return ""

        outer_diameter_nm = resolved_core_diameter_nm + 2.0 * resolved_shell_thickness_nm
        return f"{outer_diameter_nm:.6g}"

    def _as_required_float(self, value: Any, field_name: str) -> float:
        try:
            if value in (None, ""):
                raise ValueError
            return float(value)
        except Exception as exc:
            raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc

    def _as_optional_float(self, value: Any) -> Optional[float]:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except Exception:
            return None

    def _as_required_int(self, value: Any, field_name: str) -> int:
        try:
            if value in (None, ""):
                raise ValueError
            return int(value)
        except Exception as exc:
            raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc

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

    def _get_mie_model_options(self) -> list[dict[str, str]]:
        return [
            {"label": "Solid Sphere", "value": "Solid Sphere"},
            {"label": "Core/Shell Sphere", "value": "Core/Shell Sphere"},
        ]

    def _get_medium_refractive_index_presets(self) -> list[dict[str, float]]:
        return [
            {"label": "Water 1.333", "value": 1.333},
            {"label": "PBS 1.335", "value": 1.335},
        ]

    def _get_particle_refractive_index_presets(self) -> list[dict[str, float]]:
        return [
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
            {"label": "PMMA 1.49", "value": 1.49},
            {"label": "Lipid 1.47", "value": 1.47},
        ]

    def _get_core_refractive_index_presets(self) -> list[dict[str, float]]:
        return [
            {"label": "Soybean oil 1.47", "value": 1.47},
            {"label": "Polystyrene 1.59", "value": 1.59},
            {"label": "Silica 1.45", "value": 1.45},
        ]

    def _get_shell_refractive_index_presets(self) -> list[dict[str, float]]:
        return [
            {"label": "Phospholipid 1.46", "value": 1.46},
            {"label": "Waterlike 1.33", "value": 1.33},
        ]

    def _get_optical_configuration_presets(self) -> dict[str, dict[str, Any]]:
        return {
            "default_small_particle_setup": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.2,
                "detector_cache_numerical_aperture": 0.0,
                "detector_sampling": 600,
            },
            "higher_na_collection": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.4,
                "detector_cache_numerical_aperture": 0.1,
                "detector_sampling": 600,
            },
            "low_sampling_preview": {
                "wavelength_nm": 700.0,
                "detector_numerical_aperture": 0.2,
                "detector_cache_numerical_aperture": 0.1,
                "detector_sampling": 200,
            },
        }

    def _get_optical_configuration_preset_options(self) -> list[dict[str, str]]:
        return [
            {"label": "Default small particle setup", "value": "default_small_particle_setup"},
            {"label": "Higher NA collection", "value": "higher_na_collection"},
            {"label": "Low sampling preview", "value": "low_sampling_preview"},
        ]

    def _table_is_effectively_empty(
        self,
        *,
        mie_model: str,
        rows: Optional[list[dict[str, Any]]],
    ) -> bool:
        normalized_rows = self._normalize_table_rows(
            mie_model=mie_model,
            current_rows=rows,
        )

        if not normalized_rows:
            return True

        if mie_model == "Core/Shell Sphere":
            for row in normalized_rows:
                if (
                    str(row.get("core_diameter_nm", "")).strip()
                    or str(row.get("shell_thickness_nm", "")).strip()
                    or str(row.get("measured_peak_position", "")).strip()
                    or str(row.get("expected_coupling", "")).strip()
                ):
                    return False
            return True

        for row in normalized_rows:
            if (
                str(row.get("particle_diameter_nm", "")).strip()
                or str(row.get("measured_peak_position", "")).strip()
                or str(row.get("expected_coupling", "")).strip()
            ):
                return False

        return True

    def _as_float_list_from_runtime_value(self, value: Any) -> list[float]:
        if value in (None, ""):
            return []

        if isinstance(value, (list, tuple)):
            result: list[float] = []
            for item in value:
                try:
                    parsed_value = float(item)
                except Exception:
                    continue
                if np.isfinite(parsed_value):
                    result.append(float(parsed_value))
            return result

        text = str(value).replace(";", ",")
        result = []

        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                parsed_value = float(part)
            except Exception:
                continue
            if np.isfinite(parsed_value):
                result.append(float(parsed_value))

        return result