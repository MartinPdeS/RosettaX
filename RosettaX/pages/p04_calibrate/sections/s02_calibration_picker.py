# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import directories
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.model.scattering import ScatteringModelConfiguration
from RosettaX.workflow.plotting import scatter2d

logger = logging.getLogger(__name__)


class CalibrationPicker:
    """
    Calibration file picker section.

    Responsibilities
    ----------------
    - List fluorescence and scattering calibration JSON files.
    - Resolve URL selected calibration values.
    - Store the selected calibration path.
    - Store a lightweight summary of the selected calibration payload.
    - Show target scattering model controls when a scattering calibration is selected.
    - Preview the target Mie relation.
    - Preview the automatically selected largest monotonic branch when the full
      target relation is not monotonic.
    """

    model_configuration = ScatteringModelConfiguration

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page

        self._folder_definitions: list[tuple[str, str, Path]] = [
            (
                "fluorescence",
                "Fluorescence",
                directories.fluorescence_calibration,
            ),
            (
                "scattering",
                "Scattering",
                directories.scattering_calibration,
            ),
        ]

        logger.debug(
            "Initialized CalibrationPicker section for page=%s",
            self.page.__class__.__name__,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the calibration picker layout.
        """
        logger.debug("Building CalibrationPicker layout.")

        return dbc.Card(
            [
                dbc.CardHeader("1. Select calibration"),
                dbc.CardBody(
                    [
                        self._build_picker_row(),
                        dash.html.Div(
                            style={
                                "height": "12px",
                            },
                        ),
                        self._build_scattering_target_model_section(),
                    ]
                ),
            ]
        )

    def _build_picker_row(self) -> dbc.Row:
        """
        Build the calibration dropdown and refresh row.
        """
        return dbc.Row(
            [
                dbc.Col(
                    dbc.Select(
                        id=self.page.ids.CalibrationPicker.dropdown,
                        options=[],
                        value=None,
                    ),
                    width=True,
                ),
                dbc.Col(
                    dbc.Button(
                        "Refresh",
                        id=self.page.ids.CalibrationPicker.refresh_button,
                        color="secondary",
                        outline=True,
                    ),
                    width="auto",
                ),
            ],
            className="g-2",
            align="center",
        )

    def _build_scattering_target_model_section(self) -> dash.html.Div:
        """
        Build target particle model controls shown for scattering calibration.
        """
        return dash.html.Div(
            [
                dash.html.H5(
                    "Target particle model",
                    style={
                        "marginBottom": "8px",
                    },
                ),
                dash.html.Div(
                    (
                        "The selected scattering calibration provides the instrument "
                        "response. These target model parameters are used to convert "
                        "calibrated optical coupling into equivalent diameter."
                    ),
                    style={
                        "marginBottom": "12px",
                        "opacity": 0.75,
                    },
                ),
                dash.html.Div(
                    [
                        dash.html.Div(
                            [
                                self._inline_row(
                                    "Particle type:",
                                    dash.dcc.Dropdown(
                                        id=self.page.ids.CalibrationPicker.target_mie_model,
                                        options=self.model_configuration.mie_model_options,
                                        value="Solid Sphere",
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
                                self._build_numeric_input_row(
                                    label="Medium refractive index:",
                                    component_id=self.page.ids.CalibrationPicker.target_medium_refractive_index,
                                    value=1.333,
                                    min_value=1.0,
                                    max_value=2.5,
                                    step=0.001,
                                ),
                                self._build_numeric_input_row(
                                    label="Particle refractive index:",
                                    component_id=self.page.ids.CalibrationPicker.target_particle_refractive_index,
                                    value=1.39,
                                    min_value=1.0,
                                    max_value=2.5,
                                    step=0.001,
                                ),
                                self._build_numeric_input_row(
                                    label="Diameter min [nm]:",
                                    component_id=self.page.ids.CalibrationPicker.target_diameter_min_nm,
                                    value=30,
                                    min_value=1,
                                    step=1,
                                ),
                                self._build_numeric_input_row(
                                    label="Diameter max [nm]:",
                                    component_id=self.page.ids.CalibrationPicker.target_diameter_max_nm,
                                    value=1000,
                                    min_value=1,
                                    step=1,
                                ),
                                self._build_numeric_input_row(
                                    label="Diameter points:",
                                    component_id=self.page.ids.CalibrationPicker.target_diameter_count,
                                    value=500,
                                    min_value=2,
                                    step=1,
                                ),
                            ],
                            style={
                                "flex": "1 1 460px",
                                "minWidth": "420px",
                            },
                        ),
                        dash.html.Div(
                            [
                                dbc.Alert(
                                    "Target Mie relation status will appear here.",
                                    id=self.page.ids.CalibrationPicker.target_mie_relation_status,
                                    color="secondary",
                                    style={
                                        "marginBottom": "10px",
                                    },
                                ),

                                scatter2d.Scatter2DGraph.build_component(
                                    component_ids=scatter2d.Scatter2DGraphIds(
                                        graph=self.page.ids.CalibrationPicker.target_mie_relation_graph,
                                        axis_scale_toggle=self.page.ids.CalibrationPicker.target_mie_relation_axis_scale_toggle,
                                    ),
                                    figure=self._build_empty_target_mie_relation_figure(),
                                    x_log_enabled=self._get_default_target_mie_relation_xscale() == "log",
                                    y_log_enabled=self._get_default_target_mie_relation_yscale() == "log",
                                    graph_style={
                                        "height": "320px",
                                        "width": "100%",
                                    },
                                ),
                            ],
                            style={
                                "flex": "1.25 1 560px",
                                "minWidth": "440px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "gap": "18px",
                        "alignItems": "flex-start",
                        "width": "100%",
                        "flexWrap": "wrap",
                    },
                ),
            ],
            id=self.page.ids.CalibrationPicker.scattering_target_model_container,
            style={
                "display": "none",
                "padding": "12px",
                "border": "1px solid #d9d9d9",
                "borderRadius": "8px",
                "backgroundColor": "rgba(0, 0, 0, 0.02)",
            },
        )

    def _build_numeric_input_row(
        self,
        *,
        label: str,
        component_id: str,
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
    ) -> dash.html.Div:
        """
        Build one labeled numeric input row.
        """
        return self._inline_row(
            label,
            dash.dcc.Input(
                id=component_id,
                type="number",
                value=value,
                min=min_value,
                max=max_value,
                step=step,
                debounce=True,
                persistence=True,
                persistence_type="session",
                style={
                    "width": "180px",
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
        Build one aligned label and control row.
        """
        row_style = {
            "display": "flex",
            "alignItems": "center",
            "width": "100%",
            "marginTop": "8px",
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
                        "width": "210px",
                        "minWidth": "210px",
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

    def register_callbacks(self) -> None:
        """
        Register calibration picker callbacks.
        """
        logger.debug("Registering CalibrationPicker callbacks.")

        self._register_dropdown_refresh_callback()
        self._register_selected_calibration_store_callback()
        self._register_selected_calibration_summary_callback()
        self._register_scattering_target_model_visibility_callback()
        self._register_target_mie_relation_preview_callback()
        self._register_target_mie_relation_axis_scale_runtime_sync_callback()

    def _register_target_mie_relation_axis_scale_runtime_sync_callback(self) -> None:
        """
        Synchronize the target Mie relation preview axis scale toggle from the
        active runtime profile.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_relation_axis_scale_toggle,
                "value",
            ),
            dash.Input(
                "runtime-config-store",
                "data",
            ),
            prevent_initial_call=False,
        )
        def sync_target_mie_relation_axis_scale_from_runtime_config(
            runtime_config_data: Any,
        ) -> list[str]:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            xscale = self._normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.target_mie_relation_xscale",
                    default="linear",
                ),
                default="linear",
            )

            yscale = self._normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.target_mie_relation_yscale",
                    default="log",
                ),
                default="log",
            )

            return self._build_axis_scale_toggle_values(
                xscale=xscale,
                yscale=yscale,
            )


    def _get_default_target_mie_relation_xscale(self) -> str:
        """
        Return the default x axis scale for the target Mie relation preview.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return self._normalize_axis_scale(
            runtime_config.get_str(
                "calibration.target_mie_relation_xscale",
                default="linear",
            ),
            default="linear",
        )


    def _get_default_target_mie_relation_yscale(self) -> str:
        """
        Return the default y axis scale for the target Mie relation preview.
        """
        runtime_config = RuntimeConfig.from_default_profile()

        return self._normalize_axis_scale(
            runtime_config.get_str(
                "calibration.target_mie_relation_yscale",
                default="log",
            ),
            default="log",
        )


    @staticmethod
    def _normalize_axis_scale(
        value: Any,
        *,
        default: str,
    ) -> str:
        """
        Normalize an axis scale value.
        """
        value_string = str(value or "").strip().lower()

        if value_string in (
            "linear",
            "log",
        ):
            return value_string

        return default


    @staticmethod
    def _build_axis_scale_toggle_values(
        *,
        xscale: Any,
        yscale: Any,
    ) -> list[str]:
        """
        Convert x and y axis scales to Scatter2DGraph checklist values.
        """
        axis_scale_toggle_values: list[str] = []

        if str(xscale).strip().lower() == "log":
            axis_scale_toggle_values.append(
                scatter2d.Scatter2DGraph.x_log_value,
            )

        if str(yscale).strip().lower() == "log":
            axis_scale_toggle_values.append(
                scatter2d.Scatter2DGraph.y_log_value,
            )

        return axis_scale_toggle_values


    def _register_dropdown_refresh_callback(self) -> None:
        """
        Register calibration dropdown refresh callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.dropdown,
                "options",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.dropdown,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.refresh_button,
                "n_clicks",
            ),
            dash.Input(
                self.page.ids.Page.location,
                "search",
            ),
            prevent_initial_call=False,
        )
        def refresh_calibration_picker(
            refresh_button_clicks: Optional[int],
            search: Optional[str],
        ) -> tuple[list[dict[str, str]], Optional[str]]:
            logger.debug(
                "refresh_calibration_picker called with refresh_button_clicks=%r search=%r",
                refresh_button_clicks,
                search,
            )

            dropdown_options = self._build_dropdown_options()

            allowed_values = {
                str(option["value"])
                for option in dropdown_options
                if isinstance(option, dict) and "value" in option
            }

            selected_calibration_from_url = self._extract_selected_calibration_from_search(
                search,
            )

            if (
                selected_calibration_from_url is not None
                and selected_calibration_from_url in allowed_values
            ):
                resolved_dropdown_value = selected_calibration_from_url

                logger.debug(
                    "Using URL selected calibration=%r",
                    resolved_dropdown_value,
                )

            elif dropdown_options:
                resolved_dropdown_value = str(
                    dropdown_options[0]["value"],
                )

                logger.debug(
                    "Using first available calibration=%r",
                    resolved_dropdown_value,
                )

            else:
                resolved_dropdown_value = None

                logger.debug(
                    "No calibration files found. Dropdown will remain empty."
                )

            logger.debug(
                "Returning calibration dropdown option_count=%d value=%r",
                len(dropdown_options),
                resolved_dropdown_value,
            )

            return dropdown_options, resolved_dropdown_value

    def _register_selected_calibration_store_callback(self) -> None:
        """
        Register selected calibration path store callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Stores.selected_calibration_path_store,
                "data",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.dropdown,
                "value",
            ),
            prevent_initial_call=False,
        )
        def sync_selected_calibration_store(
            selected_dropdown_value: Optional[str],
        ) -> Optional[str]:
            logger.debug(
                "sync_selected_calibration_store called with selected_dropdown_value=%r",
                selected_dropdown_value,
            )

            if selected_dropdown_value is None:
                return None

            resolved_selected_dropdown_value = str(
                selected_dropdown_value,
            ).strip()

            if not resolved_selected_dropdown_value:
                return None

            logger.debug(
                "Updating selected_calibration_path_store=%r",
                resolved_selected_dropdown_value,
            )

            return resolved_selected_dropdown_value

    def _register_selected_calibration_summary_callback(self) -> None:
        """
        Register selected calibration summary store callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.dropdown,
                "value",
            ),
            prevent_initial_call=False,
        )
        def sync_selected_calibration_summary_store(
            selected_dropdown_value: Optional[str],
        ) -> Optional[dict[str, Any]]:
            logger.debug(
                "sync_selected_calibration_summary_store called with selected_dropdown_value=%r",
                selected_dropdown_value,
            )

            if selected_dropdown_value is None:
                return None

            resolved_selected_dropdown_value = str(
                selected_dropdown_value,
            ).strip()

            if not resolved_selected_dropdown_value:
                return None

            try:
                calibration_file_path = self._resolve_calibration_file_path(
                    resolved_selected_dropdown_value,
                )

                calibration_payload = self._load_calibration_payload(
                    calibration_file_path,
                )

                calibration_summary = self._build_calibration_summary(
                    selected_calibration=resolved_selected_dropdown_value,
                    calibration_file_path=calibration_file_path,
                    calibration_payload=calibration_payload,
                )

                logger.debug(
                    "Updating selected_calibration_summary_store=%r",
                    calibration_summary,
                )

                return calibration_summary

            except Exception:
                logger.exception(
                    "Failed to load calibration summary for selected calibration=%r",
                    resolved_selected_dropdown_value,
                )

                return {
                    "selected_calibration": resolved_selected_dropdown_value,
                    "calibration_type": "",
                    "source_channel": "",
                    "output_quantity": "",
                    "version": None,
                    "is_valid": False,
                    "is_scattering": False,
                    "is_fluorescence": False,
                    "requires_target_model": False,
                    "error": "Failed to read selected calibration JSON file.",
                }

    def _register_scattering_target_model_visibility_callback(self) -> None:
        """
        Show target particle model controls only for scattering calibration.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.scattering_target_model_container,
                "style",
            ),
            dash.Input(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            prevent_initial_call=False,
        )
        def toggle_scattering_target_model_section(
            calibration_summary: Any,
        ) -> dict[str, str]:
            logger.debug(
                "toggle_scattering_target_model_section called with calibration_summary=%r",
                calibration_summary,
            )

            base_style = {
                "padding": "12px",
                "border": "1px solid #d9d9d9",
                "borderRadius": "8px",
                "backgroundColor": "rgba(0, 0, 0, 0.02)",
            }

            if (
                isinstance(calibration_summary, dict)
                and calibration_summary.get("requires_target_model")
            ):
                return {
                    **base_style,
                    "display": "block",
                }

            return {
                **base_style,
                "display": "none",
            }

    def _register_target_mie_relation_preview_callback(self) -> None:
        """
        Register target Mie relation preview callback.

        The preview uses the same policy as export:

        - full target relation if monotonic
        - largest monotonic branch if not monotonic
        - extrapolation allowed outside the selected branch during export
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_relation_graph,
                "figure",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_relation_status,
                "children",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_relation_status,
                "color",
            ),
            dash.Input(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_mie_model,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_medium_refractive_index,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_particle_refractive_index,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_diameter_min_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_diameter_max_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_diameter_count,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_mie_relation_axis_scale_toggle,
                "value",
            ),
            prevent_initial_call=False,
        )
        def update_target_mie_relation_preview(
            selected_calibration_summary: Any,
            target_mie_model: Any,
            target_medium_refractive_index: Any,
            target_particle_refractive_index: Any,
            target_diameter_min_nm: Any,
            target_diameter_max_nm: Any,
            target_diameter_count: Any,
            axis_scale_toggle_values: Any,
        ) -> tuple[Any, str, str]:
            logger.debug(
                "update_target_mie_relation_preview called with "
                "selected_calibration_summary=%r target_mie_model=%r "
                "target_medium_refractive_index=%r target_particle_refractive_index=%r "
                "target_diameter_min_nm=%r target_diameter_max_nm=%r "
                "target_diameter_count=%r axis_scale_toggle_values=%r",
                selected_calibration_summary,
                target_mie_model,
                target_medium_refractive_index,
                target_particle_refractive_index,
                target_diameter_min_nm,
                target_diameter_max_nm,
                target_diameter_count,
                axis_scale_toggle_values,
            )

            if not (
                isinstance(selected_calibration_summary, dict)
                and selected_calibration_summary.get("requires_target_model")
            ):
                return (
                    self._build_empty_target_mie_relation_figure(),
                    "Select a scattering calibration to preview the target Mie relation.",
                    "secondary",
                )

            try:
                from RosettaX.workflow.apply_calibration import io as apply_calibration_io
                from RosettaX.workflow.apply_calibration.scattering import (
                    ScatteringTargetModelParameters,
                    build_target_mie_relation,
                    find_strictly_monotonic_diameter_intervals,
                    format_monotonic_interval_suggestions,
                    get_finite_positive_mie_relation_arrays,
                    resolve_monotonic_target_mie_relation,
                )

                selected_calibration = selected_calibration_summary.get(
                    "selected_calibration",
                )

                calibration_file_path = apply_calibration_io.resolve_calibration_file_path(
                    selected_calibration,
                )

                calibration_payload = apply_calibration_io.load_calibration_payload(
                    calibration_file_path,
                )

                target_model_parameters = ScatteringTargetModelParameters.from_raw_values(
                    target_mie_model=target_mie_model,
                    target_medium_refractive_index=target_medium_refractive_index,
                    target_particle_refractive_index=target_particle_refractive_index,
                    target_diameter_min_nm=target_diameter_min_nm,
                    target_diameter_max_nm=target_diameter_max_nm,
                    target_diameter_count=target_diameter_count,
                )

                full_target_mie_relation = build_target_mie_relation(
                    calibration_payload=calibration_payload,
                    target_model_parameters=target_model_parameters,
                )

                full_diameter_values_nm, full_coupling_values = (
                    get_finite_positive_mie_relation_arrays(
                        target_mie_relation=full_target_mie_relation,
                    )
                )

                relation_resolution = resolve_monotonic_target_mie_relation(
                    target_mie_relation=full_target_mie_relation,
                )

                selected_diameter_values_nm, selected_coupling_values = (
                    get_finite_positive_mie_relation_arrays(
                        target_mie_relation=relation_resolution.target_mie_relation,
                    )
                )

                if relation_resolution.used_auto_largest_branch:
                    all_monotonic_intervals = find_strictly_monotonic_diameter_intervals(
                        diameter_nm=full_diameter_values_nm,
                        theoretical_coupling=full_coupling_values,
                    )

                    logger.info(
                        "Target Mie relation was not strictly monotonic. "
                        "Auto largest branch selected. selected_interval=%r "
                        "all_interval_suggestions=%s",
                        relation_resolution.selected_interval,
                        format_monotonic_interval_suggestions(
                            monotonic_intervals=all_monotonic_intervals,
                            max_interval_count=20,
                        ),
                    )

                    figure = self._build_target_mie_relation_figure(
                        full_diameter_values_nm=full_diameter_values_nm,
                        full_coupling_values=full_coupling_values,
                        selected_diameter_values_nm=selected_diameter_values_nm,
                        selected_coupling_values=selected_coupling_values,
                        show_selected_branch=True,
                        axis_scale_toggle_values=axis_scale_toggle_values,
                    )

                    selected_interval = relation_resolution.selected_interval

                    if selected_interval is None:
                        selected_interval_message = "largest detected monotonic branch"

                    else:
                        selected_interval_message = selected_interval.to_message_fragment()

                    return (
                        figure,
                        (
                            "Target Mie relation is not monotonic over the full range. "
                            "Using auto largest monotonic branch with linear extrapolation enabled: "
                            f"{selected_interval_message}."
                        ),
                        "warning",
                    )

                figure = self._build_target_mie_relation_figure(
                    full_diameter_values_nm=full_diameter_values_nm,
                    full_coupling_values=full_coupling_values,
                    selected_diameter_values_nm=selected_diameter_values_nm,
                    selected_coupling_values=selected_coupling_values,
                    show_selected_branch=False,
                    axis_scale_toggle_values=axis_scale_toggle_values,
                )

                return (
                    figure,
                    (
                        "Target Mie relation is strictly monotonic over the selected "
                        "diameter range. Full range will be used for diameter inversion."
                    ),
                    "success",
                )

            except Exception as exc:
                logger.exception(
                    "Failed to update target Mie relation preview."
                )

                return (
                    self._build_empty_target_mie_relation_figure(),
                    f"Failed to compute target Mie relation preview: {type(exc).__name__}: {exc}",
                    "danger",
                )

    def _build_dropdown_options(self) -> list[dict[str, str]]:
        """
        Build calibration dropdown options from disk.
        """
        logger.debug("Building calibration dropdown options from disk.")

        dropdown_options: list[dict[str, str]] = []

        for folder_key, folder_label, folder_path in self._folder_definitions:
            try:
                folder_path.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                calibration_file_paths = sorted(
                    [
                        path
                        for path in folder_path.glob("*.json")
                        if path.is_file()
                    ],
                    key=lambda path: path.name.lower(),
                )

                logger.debug(
                    "Found %d calibration files in folder_key=%r folder_path=%r",
                    len(calibration_file_paths),
                    folder_key,
                    str(folder_path),
                )

                for calibration_file_path in calibration_file_paths:
                    dropdown_options.append(
                        {
                            "label": f"{folder_label} | {calibration_file_path.name}",
                            "value": f"{folder_key}/{calibration_file_path.name}",
                        }
                    )

            except Exception:
                logger.exception(
                    "Failed while building dropdown options for folder_key=%r folder_path=%r",
                    folder_key,
                    str(folder_path),
                )

        logger.debug(
            "Returning %d total calibration dropdown options.",
            len(dropdown_options),
        )

        return dropdown_options

    def _resolve_calibration_file_path(
        self,
        selected_calibration: Any,
    ) -> Path:
        """
        Resolve a selected dropdown value into a calibration file path.
        """
        selected_calibration_string = str(
            selected_calibration,
        ).strip()

        if not selected_calibration_string:
            raise ValueError("Selected calibration path is empty.")

        if "/" not in selected_calibration_string:
            raise ValueError(
                f"Invalid selected calibration value: {selected_calibration_string!r}."
            )

        folder_key, file_name = selected_calibration_string.split(
            "/",
            1,
        )

        for known_folder_key, _folder_label, folder_path in self._folder_definitions:
            if folder_key == known_folder_key:
                return folder_path / file_name

        raise ValueError(
            f"Unsupported calibration folder key: {folder_key!r}."
        )

    @staticmethod
    def _load_calibration_payload(
        calibration_file_path: Path,
    ) -> dict[str, Any]:
        """
        Load the top level payload from a calibration JSON file.
        """
        record = json.loads(
            calibration_file_path.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(record, dict):
            raise ValueError("Calibration file root record is invalid.")

        payload = record.get(
            "payload",
        )

        if not isinstance(payload, dict):
            raise ValueError('Calibration file is missing top level "payload".')

        return payload

    @staticmethod
    def _build_calibration_summary(
        *,
        selected_calibration: str,
        calibration_file_path: Path,
        calibration_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build a lightweight calibration summary for UI decisions.
        """
        calibration_type = str(
            calibration_payload.get(
                "calibration_type",
                "",
            )
        ).strip()

        source_channel = str(
            calibration_payload.get(
                "source_channel",
                "",
            )
        ).strip()

        output_quantity = str(
            calibration_payload.get(
                "output_quantity",
                "",
            )
        ).strip()

        version = calibration_payload.get(
            "version",
            None,
        )

        instrument_response = calibration_payload.get(
            "instrument_response",
            {},
        )

        if isinstance(instrument_response, dict):
            measured_channel = str(
                instrument_response.get(
                    "measured_channel",
                    "",
                )
            ).strip()
        else:
            measured_channel = ""

        if not source_channel and measured_channel:
            source_channel = measured_channel

        return {
            "selected_calibration": selected_calibration,
            "file_name": calibration_file_path.name,
            "file_path": str(calibration_file_path),
            "calibration_type": calibration_type,
            "source_channel": source_channel,
            "output_quantity": output_quantity,
            "version": version,
            "is_scattering": calibration_type == "scattering",
            "is_fluorescence": calibration_type == "fluorescence",
            "requires_target_model": calibration_type == "scattering",
            "is_valid": bool(calibration_type),
            "error": "",
        }

    @staticmethod
    def _extract_selected_calibration_from_search(
        search: Optional[str],
    ) -> Optional[str]:
        """
        Extract selected calibration value from the URL query string.
        """
        logger.debug(
            "Extracting selected_calibration from search=%r",
            search,
        )

        if not search:
            return None

        parsed_query = parse_qs(
            search.lstrip("?"),
        )

        selected_calibration_values = parsed_query.get(
            "selected_calibration",
            [],
        )

        if not selected_calibration_values:
            return None

        selected_calibration = str(
            selected_calibration_values[0],
        ).strip()

        if not selected_calibration:
            return None

        logger.debug(
            "Extracted selected_calibration=%r from URL query string.",
            selected_calibration,
        )

        return selected_calibration

    @staticmethod
    def _build_empty_target_mie_relation_figure() -> Any:
        """
        Build an empty target Mie relation preview figure.
        """
        return scatter2d.Scatter2DGraph.build_empty_figure(
            message="Select a scattering calibration to compute the preview.",
        )

    @staticmethod
    def _build_target_mie_relation_figure(
        *,
        full_diameter_values_nm: Any,
        full_coupling_values: Any,
        selected_diameter_values_nm: Any,
        selected_coupling_values: Any,
        show_selected_branch: bool,
        axis_scale_toggle_values: Any,
    ) -> Any:
        """
        Build the target Mie relation preview figure.

        The full Mie relation is always shown. If the full relation is not
        monotonic, the automatically selected largest monotonic branch is shown
        as a second curve.
        """
        traces = [
            scatter2d.Scatter2DTrace(
                x_values=full_diameter_values_nm,
                y_values=full_coupling_values,
                name="Full target Mie relation",
                mode="lines",
            )
        ]

        if show_selected_branch:
            traces.append(
                scatter2d.Scatter2DTrace(
                    x_values=selected_diameter_values_nm,
                    y_values=selected_coupling_values,
                    name="Auto selected largest monotonic branch",
                    mode="lines",
                )
            )

        return scatter2d.Scatter2DGraph.build_figure(
            traces=traces,
            title="Target Mie relation preview",
            x_axis_title="Target diameter [nm]",
            y_axis_title="Theoretical optical coupling",
            axis_scale_toggle_values=axis_scale_toggle_values,
            show_grid=True,
            hovermode="closest",
            uirevision="target_mie_relation_preview",
        )