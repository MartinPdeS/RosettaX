# -*- coding: utf-8 -*-

import logging
from typing import Any, Optional

import dash

from RosettaX.utils import RuntimeConfig
from RosettaX.workflow.apply_calibration.scattering import (
    CUSTOM_PRESET_NAME,
    build_scattering_target_model_preset_options,
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
    ) -> None:
        self.page = page

    def register_callbacks(self) -> None:
        """
        Register calibration picker callbacks.
        """
        logger.debug("Registering CalibrationPicker callbacks.")

        self._register_calibration_upload_callback()
        self._register_calibration_preview_callback()
        self._register_scattering_target_model_visibility_callback()
        self._register_target_model_preset_runtime_sync_callback()
        self._register_target_model_preset_callback()
        self._register_target_model_preset_disabled_state_callback()
        self._register_target_model_details_visibility_callback()
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

            configured_value = runtime_config.get_str(
                "calibration.target_model_preset",
                default=CUSTOM_PRESET_NAME,
            )

            available_values = {
                option.get("value")
                for option in build_scattering_target_model_preset_options(
                    include_empty_option=True,
                    empty_label="Select",
                )
                if isinstance(option, dict)
            }

            if configured_value in available_values:
                return configured_value

            return get_scattering_target_model_preset(
                configured_value,
            ).name

    def _register_target_model_details_visibility_callback(self) -> None:
        """
        Show target model detail boxes only after a preset is selected.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.target_model_details_container,
                "style",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.target_mie_relation_preview_container,
                "style",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            prevent_initial_call=False,
        )
        def toggle_target_model_detail_boxes(
            target_model_preset: Any,
        ) -> tuple[dict[str, str], dict[str, str]]:
            has_selected_preset = services.has_selected_target_model_preset(
                target_model_preset,
            )

            visible_style = services.build_scattering_target_model_container_style(
                is_visible=has_selected_preset,
            )

            return visible_style, dict(visible_style)

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

            if not services.has_selected_target_model_preset(target_model_preset):
                hidden_style = services.build_target_parameter_container_style(
                    is_visible=False,
                )

                return hidden_style, dict(hidden_style)

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

    def _register_calibration_upload_callback(self) -> None:
        """
        Register calibration upload parsing callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.upload_status,
                "children",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.upload_status,
                "color",
            ),
            dash.Input(
                self.page.ids.CalibrationPicker.upload,
                "contents",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.upload,
                "filename",
            ),
            prevent_initial_call=False,
        )
        def sync_uploaded_calibration_summary(
            uploaded_contents: Any,
            uploaded_filename: Any,
        ) -> tuple[Optional[list[dict[str, Any]]], str, str]:
            logger.debug(
                "sync_uploaded_calibration_summary called with uploaded_filename=%r",
                uploaded_filename,
            )

            if uploaded_contents is None:
                return (
                    None,
                    services.build_upload_prompt_text(),
                    "secondary",
                )

            try:
                if isinstance(uploaded_contents, list):
                    contents_list = uploaded_contents
                else:
                    contents_list = [uploaded_contents]

                if isinstance(uploaded_filename, list):
                    filename_list = uploaded_filename
                else:
                    filename_list = [uploaded_filename]

                if len(contents_list) != len(filename_list):
                    raise ValueError(
                        "Calibration upload payload is inconsistent."
                    )

                calibration_summaries: list[dict[str, Any]] = []

                for contents_item, filename_item in zip(
                    contents_list,
                    filename_list,
                ):
                    resolved_filename, calibration_payload = services.parse_uploaded_calibration(
                        contents=contents_item,
                        filename=filename_item,
                    )

                    calibration_summaries.append(
                        services.build_calibration_summary(
                            selected_calibration=resolved_filename,
                            calibration_payload=calibration_payload,
                        )
                    )

                logger.debug(
                    "Updating selected_calibration_summary_store=%r",
                    calibration_summaries,
                )

                loaded_file_count = len(calibration_summaries)

                return (
                    calibration_summaries,
                    f"Loaded {loaded_file_count} calibration file(s).",
                    "success",
                )

            except Exception as exc:
                logger.exception(
                    "Failed to parse uploaded calibration filename=%r",
                    uploaded_filename,
                )

                return (
                    None,
                    f"Failed to load calibration JSON: {type(exc).__name__}: {exc}",
                    "danger",
                )

    def _register_calibration_preview_callback(self) -> None:
        """
        Register callback to populate and display calibration preview.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.CalibrationPicker.preview_container,
                "style",
            ),
            dash.Output(
                self.page.ids.CalibrationPicker.preview_content,
                "children",
            ),
            dash.Input(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            prevent_initial_call=False,
        )
        def update_preview(
            calibration_summary: Any,
        ) -> tuple[dict[str, Any], Any]:
            calibration_summaries = services.normalize_calibration_summaries(
                calibration_summary,
            )

            if not calibration_summaries:
                return {"display": "none"}, None

            preview_children = []

            for index, summary in enumerate(calibration_summaries, start=1):
                if not summary.get("calibration_type"):
                    continue

                preview_children.append(
                    dash.html.Div(
                        [
                            dash.html.Div(
                                f"Calibration {index}",
                                style={
                                    "fontWeight": "700",
                                    "fontSize": "0.93rem",
                                    "marginBottom": "10px",
                                },
                            ),
                            dash.html.Div(
                                services.build_preview_items(summary),
                            ),
                        ],
                        style={
                            "padding": "10px 0px",
                            "borderBottom": (
                                "1px solid rgba(0, 0, 0, 0.08)"
                                if index < len(calibration_summaries)
                                else "none"
                            ),
                        },
                    )
                )

            if not preview_children:
                return {"display": "none"}, None

            return (
                {"display": "block"},
                preview_children,
            )

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

            is_visible = services.calibration_summaries_require_target_model(
                calibration_summary,
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
                self.page.ids.CalibrationPicker.target_model_preset,
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
            target_model_preset: Any,
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
                target_model_preset,
                axis_scale_toggle_values,
            )

            scattering_calibration_summary = (
                services.get_primary_scattering_calibration_summary(
                    selected_calibration_summary,
                )
            )

            if scattering_calibration_summary is None:
                return (
                    services.build_empty_target_mie_relation_figure(),
                    "Select a scattering calibration to preview the target Mie relation.",
                    "secondary",
                )

            if not services.has_selected_target_model_preset(target_model_preset):
                return (
                    services.build_empty_target_mie_relation_figure(),
                    "Select a target model preset to preview the target Mie relation.",
                    "secondary",
                )

            try:
                from RosettaX.workflow.apply_calibration.scattering import (
                    ScatteringTargetModelParameters,
                    build_target_mie_relation,
                    find_strictly_monotonic_diameter_intervals,
                    format_monotonic_interval_suggestions,
                    get_finite_positive_mie_relation_arrays,
                    resolve_monotonic_target_mie_relation,
                )

                calibration_payload = scattering_calibration_summary.get(
                    "calibration_payload",
                )

                if not isinstance(calibration_payload, dict) or not calibration_payload:
                    raise ValueError("Uploaded calibration payload is missing.")

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

                if relation_resolution.used_auto_largest_branch:
                    selected_interval = relation_resolution.selected_interval

                    if selected_interval is None:
                        raise ValueError(
                            "Expected a selected monotonic interval for non-monotonic target Mie relation."
                        )

                    selected_diameter_values_nm = full_diameter_values_nm[
                        selected_interval.start_index : selected_interval.end_index + 1
                    ]
                    selected_coupling_values = full_coupling_values[
                        selected_interval.start_index : selected_interval.end_index + 1
                    ]

                    (
                        approximation_diameter_values_nm,
                        approximation_coupling_values,
                    ) = get_finite_positive_mie_relation_arrays(
                        target_mie_relation=relation_resolution.target_mie_relation,
                    )

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
                        approximation_diameter_values_nm=approximation_diameter_values_nm,
                        approximation_coupling_values=approximation_coupling_values,
                        selected_interval=relation_resolution.selected_interval,
                        show_selected_branch=True,
                        axis_scale_toggle_values=axis_scale_toggle_values,
                        x_axis_title=x_axis_title,
                    )

                    selected_interval_message = selected_interval.to_message_fragment()

                    return (
                        figure,
                        (
                            "Target Mie relation is not monotonic over the full range. "
                            "Using auto largest monotonic branch to build a monotone approximation: "
                            f"{selected_interval_message}."
                        ),
                        "warning",
                    )

                selected_diameter_values_nm, selected_coupling_values = (
                    get_finite_positive_mie_relation_arrays(
                        target_mie_relation=relation_resolution.target_mie_relation,
                    )
                )

                figure = services.build_target_mie_relation_figure(
                    full_diameter_values_nm=full_diameter_values_nm,
                    full_coupling_values=full_coupling_values,
                    selected_diameter_values_nm=selected_diameter_values_nm,
                    selected_coupling_values=selected_coupling_values,
                    approximation_diameter_values_nm=None,
                    approximation_coupling_values=None,
                    selected_interval=None,
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
