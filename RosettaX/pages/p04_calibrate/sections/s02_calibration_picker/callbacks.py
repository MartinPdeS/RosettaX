# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any, Optional

import dash

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import (
    CUSTOM_PRESET_NAME,
    get_scattering_target_model_preset,
)

from . import services


logger = logging.getLogger(__name__)


class CalibrationPickerCallbacks:
    """
    Callback registrar for the calibration picker section.
    """

    def __init__(
        self,
        *,
        page: Any,
        folder_definitions: list[tuple[str, str, Path]],
    ) -> None:
        self.page = page
        self.folder_definitions = folder_definitions

    def register_callbacks(self) -> None:
        """
        Register calibration picker callbacks.
        """
        logger.debug("Registering CalibrationPicker callbacks.")

        self._register_dropdown_refresh_callback()
        self._register_selected_calibration_store_callback()
        self._register_selected_calibration_summary_callback()
        self._register_scattering_target_model_visibility_callback()
        self._register_target_model_preset_runtime_sync_callback()
        self._register_target_model_preset_callback()
        self._register_target_model_preset_disabled_state_callback()
        self._register_target_model_parameter_visibility_callback()
        self._register_target_mie_relation_preview_callback()
        self._register_target_mie_relation_axis_scale_runtime_sync_callback()

    def _register_target_model_preset_runtime_sync_callback(self) -> None:
        """
        Synchronize the target model preset selection from the active runtime profile.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            dash.Input(
                "runtime-config-store",
                "data",
            ),
            prevent_initial_call=False,
        )
        def sync_target_model_preset_from_runtime_config(
            runtime_config_data: Any,
        ) -> str:
            runtime_config = RuntimeConfig.from_dict(
                runtime_config_data if isinstance(runtime_config_data, dict) else None
            )

            return get_scattering_target_model_preset(
                runtime_config.get_str(
                    "calibration.target_model_preset",
                    default=CUSTOM_PRESET_NAME,
                )
            ).name

    def _register_target_model_preset_callback(self) -> None:
        """
        Apply target model preset values to the target model controls.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_model,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_medium_refractive_index,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_particle_refractive_index,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_refractive_index,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_shell_refractive_index,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_shell_thickness_nm,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm,
                "value",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            prevent_initial_call=True,
        )
        def apply_target_model_preset(
            target_model_preset: Any,
        ) -> tuple:
            logger.debug(
                "apply_target_model_preset called with target_model_preset=%r",
                target_model_preset,
            )

            preset = get_scattering_target_model_preset(
                target_model_preset,
            )

            logger.debug(
                "apply_target_model_preset resolved preset=%r",
                preset,
            )

            return (
                preset.mie_model,
                preset.medium_refractive_index,
                preset.particle_refractive_index,
                preset.particle_diameter_min_nm,
                preset.particle_diameter_max_nm,
                preset.particle_diameter_count,
                preset.core_refractive_index,
                preset.shell_refractive_index,
                preset.shell_thickness_nm,
                preset.core_diameter_min_nm,
                preset.core_diameter_max_nm,
                preset.core_diameter_count,
            )

    def _register_target_model_preset_disabled_state_callback(self) -> None:
        """
        Disable target model controls when a preset owns their values.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_model,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_medium_refractive_index,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_particle_refractive_index,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_refractive_index,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_shell_refractive_index,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_shell_thickness_nm,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm,
                "disabled",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count,
                "disabled",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            prevent_initial_call=False,
        )
        def sync_target_model_controls_disabled_state(
            target_model_preset: Any,
        ) -> tuple[bool, ...]:
            logger.debug(
                "sync_target_model_controls_disabled_state called with target_model_preset=%r",
                target_model_preset,
            )

            is_preset_selected = str(
                target_model_preset or CUSTOM_PRESET_NAME,
            ).strip() != CUSTOM_PRESET_NAME

            logger.debug(
                "sync_target_model_controls_disabled_state returning disabled=%r",
                is_preset_selected,
            )

            return (
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
                is_preset_selected,
            )

    def _register_target_model_parameter_visibility_callback(self) -> None:
        """
        Show only the parameter controls required by the selected target Mie model.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_solid_sphere_parameter_container,
                "style",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_core_shell_parameter_container,
                "style",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_mie_model,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            prevent_initial_call=False,
        )
        def toggle_target_model_parameter_groups(
            target_mie_model: Any,
            target_model_preset: Any,
        ) -> tuple[dict[str, str], dict[str, str]]:
            logger.debug(
                "toggle_target_model_parameter_groups called with target_mie_model=%r target_model_preset=%r",
                target_mie_model,
                target_model_preset,
            )

            resolved_target_mie_model = services.resolve_target_mie_model(
                target_mie_model=target_mie_model,
            )

            is_core_shell_model = resolved_target_mie_model == "Core/Shell Sphere"

            is_preset_selected = str(
                target_model_preset or CUSTOM_PRESET_NAME,
            ).strip() != CUSTOM_PRESET_NAME

            solid_sphere_style = services.build_target_parameter_container_style(
                is_visible=not is_core_shell_model,
                is_locked=is_preset_selected,
            )

            core_shell_style = services.build_target_parameter_container_style(
                is_visible=is_core_shell_model,
                is_locked=is_preset_selected,
            )

            logger.debug(
                "toggle_target_model_parameter_groups returning solid_sphere_style=%r core_shell_style=%r",
                solid_sphere_style,
                core_shell_style,
            )

            return solid_sphere_style, core_shell_style

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

            xscale = services.normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.target_mie_relation_xscale",
                    default="linear",
                ),
                default="linear",
            )

            yscale = services.normalize_axis_scale(
                runtime_config.get_str(
                    "calibration.target_mie_relation_yscale",
                    default="log",
                ),
                default="log",
            )

            return services.build_axis_scale_toggle_values(
                xscale=xscale,
                yscale=yscale,
            )

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

            dropdown_options = services.build_dropdown_options(
                folder_definitions=self.folder_definitions,
            )

            allowed_values = {
                str(option["value"])
                for option in dropdown_options
                if isinstance(option, dict) and "value" in option
            }

            selected_calibration_from_url = services.extract_selected_calibration_from_search(
                search=search,
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
                calibration_file_path = services.resolve_calibration_file_path(
                    selected_calibration=resolved_selected_dropdown_value,
                    folder_definitions=self.folder_definitions,
                )

                calibration_payload = services.load_calibration_payload(
                    calibration_file_path=calibration_file_path,
                )

                calibration_summary = services.build_calibration_summary(
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

            is_visible = (
                isinstance(calibration_summary, dict)
                and calibration_summary.get("requires_target_model")
            )

            return services.build_scattering_target_model_container_style(
                is_visible=bool(is_visible),
            )

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
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_core_refractive_index,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_shell_refractive_index,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_shell_thickness_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm,
                "value",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count,
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
            target_solid_sphere_diameter_min_nm: Any,
            target_solid_sphere_diameter_max_nm: Any,
            target_solid_sphere_diameter_count: Any,
            target_core_refractive_index: Any,
            target_shell_refractive_index: Any,
            target_shell_thickness_nm: Any,
            target_core_shell_core_diameter_min_nm: Any,
            target_core_shell_core_diameter_max_nm: Any,
            target_core_shell_core_diameter_count: Any,
            axis_scale_toggle_values: Any,
        ) -> tuple[Any, str, str]:
            logger.debug(
                "update_target_mie_relation_preview called with "
                "selected_calibration_summary=%r target_mie_model=%r "
                "target_medium_refractive_index=%r target_particle_refractive_index=%r "
                "target_solid_sphere_diameter_min_nm=%r "
                "target_solid_sphere_diameter_max_nm=%r "
                "target_solid_sphere_diameter_count=%r "
                "target_core_refractive_index=%r target_shell_refractive_index=%r "
                "target_shell_thickness_nm=%r "
                "target_core_shell_core_diameter_min_nm=%r "
                "target_core_shell_core_diameter_max_nm=%r "
                "target_core_shell_core_diameter_count=%r "
                "axis_scale_toggle_values=%r",
                selected_calibration_summary,
                target_mie_model,
                target_medium_refractive_index,
                target_particle_refractive_index,
                target_solid_sphere_diameter_min_nm,
                target_solid_sphere_diameter_max_nm,
                target_solid_sphere_diameter_count,
                target_core_refractive_index,
                target_shell_refractive_index,
                target_shell_thickness_nm,
                target_core_shell_core_diameter_min_nm,
                target_core_shell_core_diameter_max_nm,
                target_core_shell_core_diameter_count,
                axis_scale_toggle_values,
            )

            if not (
                isinstance(selected_calibration_summary, dict)
                and selected_calibration_summary.get("requires_target_model")
            ):
                return (
                    services.build_empty_target_mie_relation_figure(),
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

                resolved_target_mie_model = services.resolve_target_mie_model(
                    target_mie_model=target_mie_model,
                )

                is_core_shell_model = resolved_target_mie_model == "Core/Shell Sphere"

                if is_core_shell_model:
                    resolved_target_diameter_min_nm = target_core_shell_core_diameter_min_nm
                    resolved_target_diameter_max_nm = target_core_shell_core_diameter_max_nm
                    resolved_target_diameter_count = target_core_shell_core_diameter_count
                    x_axis_title = "Target core diameter [nm]"

                else:
                    resolved_target_diameter_min_nm = target_solid_sphere_diameter_min_nm
                    resolved_target_diameter_max_nm = target_solid_sphere_diameter_max_nm
                    resolved_target_diameter_count = target_solid_sphere_diameter_count
                    x_axis_title = "Target particle diameter [nm]"

                target_model_parameters = ScatteringTargetModelParameters.from_raw_values(
                    target_mie_model=resolved_target_mie_model,
                    target_medium_refractive_index=target_medium_refractive_index,
                    target_particle_refractive_index=target_particle_refractive_index,
                    target_core_refractive_index=target_core_refractive_index,
                    target_shell_refractive_index=target_shell_refractive_index,
                    target_shell_thickness_nm=target_shell_thickness_nm,
                    target_diameter_min_nm=resolved_target_diameter_min_nm,
                    target_diameter_max_nm=resolved_target_diameter_max_nm,
                    target_diameter_count=resolved_target_diameter_count,
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

                    figure = services.build_target_mie_relation_figure(
                        full_diameter_values_nm=full_diameter_values_nm,
                        full_coupling_values=full_coupling_values,
                        selected_diameter_values_nm=selected_diameter_values_nm,
                        selected_coupling_values=selected_coupling_values,
                        show_selected_branch=True,
                        axis_scale_toggle_values=axis_scale_toggle_values,
                        x_axis_title=x_axis_title,
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

                figure = services.build_target_mie_relation_figure(
                    full_diameter_values_nm=full_diameter_values_nm,
                    full_coupling_values=full_coupling_values,
                    selected_diameter_values_nm=selected_diameter_values_nm,
                    selected_coupling_values=selected_coupling_values,
                    show_selected_branch=False,
                    axis_scale_toggle_values=axis_scale_toggle_values,
                    x_axis_title=x_axis_title,
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
                    services.build_empty_target_mie_relation_figure(),
                    f"Failed to compute target Mie relation preview: {type(exc).__name__}: {exc}",
                    "danger",
                )