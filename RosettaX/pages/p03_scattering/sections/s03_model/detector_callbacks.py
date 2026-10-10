from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import dash

from RosettaX.utils import RuntimeConfig, casting

from . import services
from .models import DetectorGeometryValues

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)


def _skip_unchanged_selector_values(
    resolved_values: tuple[Any, Any, bool],
    current_values: tuple[Any, Any, Any],
) -> tuple[Any, Any, Any]:
    return tuple(
        dash.no_update if resolved == current else resolved
        for resolved, current in zip(resolved_values, current_values, strict=True)
    )


def register_detector_configuration_callbacks(section: Model) -> None:
    """
    Register detector configuration callbacks.
    """

    @dash.callback(
        dash.Output(section.ids.detector_configuration_brand, "value"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.State(section.ids.detector_configuration_brand, "value"),
        prevent_initial_call=False,
    )
    def sync_detector_configuration_brand_from_preset(
        preset_name: Any,
        current_brand: Any,
    ) -> Any:
        resolved_brand = section.model_configuration.resolve_detector_preset_brand(
            preset_name,
        )

        resolved_brand = resolved_brand or str(current_brand or "").strip()
        return dash.no_update if resolved_brand == current_brand else resolved_brand

    @dash.callback(
        dash.Output(section.ids.detector_configuration_model, "options"),
        dash.Output(section.ids.detector_configuration_model, "value"),
        dash.Output(section.ids.detector_configuration_model, "disabled"),
        dash.Input(section.ids.detector_configuration_brand, "value"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.State(section.ids.detector_configuration_model, "value"),
        dash.State(section.ids.detector_configuration_model, "options"),
        dash.State(section.ids.detector_configuration_model, "disabled"),
        prevent_initial_call=False,
    )
    def sync_detector_configuration_models_for_brand(
        brand_name: Any,
        current_preset_name: Any,
        current_model_name: Any,
        current_options: Any,
        current_disabled: Any,
    ) -> tuple[Any, Any, Any]:
        resolved_options = (
            section.model_configuration.build_detector_preset_model_options(
                brand_name,
            )
        )

        if not resolved_options:
            return _skip_unchanged_selector_values(
                ([], None, True),
                (current_options, current_model_name, current_disabled),
            )

        option_values = {option["value"] for option in resolved_options}
        resolved_model_from_preset = (
            section.model_configuration.resolve_detector_preset_model(
                current_preset_name,
            )
        )

        if resolved_model_from_preset in option_values:
            resolved_value = resolved_model_from_preset
        elif current_model_name in option_values:
            resolved_value = current_model_name
        elif len(resolved_options) == 1:
            resolved_value = resolved_options[0]["value"]
        else:
            resolved_value = None

        return _skip_unchanged_selector_values(
            (resolved_options, resolved_value, False),
            (current_options, current_model_name, current_disabled),
        )

    @dash.callback(
        dash.Output(section.ids.detector_configuration_type, "options"),
        dash.Output(section.ids.detector_configuration_type, "value"),
        dash.Output(section.ids.detector_configuration_type, "disabled"),
        dash.Input(section.ids.detector_configuration_model, "value"),
        dash.State(section.ids.detector_configuration_brand, "value"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.State(section.ids.detector_configuration_type, "value"),
        dash.State(section.ids.detector_configuration_type, "options"),
        dash.State(section.ids.detector_configuration_type, "disabled"),
        prevent_initial_call=False,
    )
    def sync_detector_configuration_types_for_model(
        model_name: Any,
        brand_name: Any,
        current_preset_name: Any,
        current_type_name: Any,
        current_options: Any,
        current_disabled: Any,
    ) -> tuple[Any, Any, Any]:
        resolved_options = (
            section.model_configuration.build_detector_preset_type_options(
                brand=brand_name,
                model=model_name,
            )
        )

        if not resolved_options:
            return _skip_unchanged_selector_values(
                ([], None, True), (current_options, current_type_name, current_disabled)
            )

        option_values = {option["value"] for option in resolved_options}

        if current_preset_name in option_values:
            resolved_value = current_preset_name
        elif current_type_name in option_values:
            resolved_value = current_type_name
        elif len(resolved_options) == 1:
            resolved_value = resolved_options[0]["value"]
        else:
            resolved_value = None

        return _skip_unchanged_selector_values(
            (resolved_options, resolved_value, False),
            (current_options, current_type_name, current_disabled),
        )

    @dash.callback(
        dash.Output(
            section.ids.detector_configuration_preset,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.detector_configuration_type, "value"),
        dash.State(section.ids.detector_configuration_preset, "value"),
        prevent_initial_call=True,
    )
    def sync_detector_configuration_preset_from_model(
        type_value: Any,
        current_preset_name: Any,
    ) -> Any:
        resolved_preset_name = type_value or ""
        return (
            dash.no_update
            if resolved_preset_name == current_preset_name
            else resolved_preset_name
        )

    @dash.callback(
        dash.Output(
            section.ids.detector_configuration_preset,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.wavelength_nm,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(section.ids.detector_configuration_auto_detect_status, "children"),
        dash.Output(section.ids.detector_configuration_auto_detect_status, "color"),
        dash.Output(section.ids.detector_configuration_auto_detect_status, "is_open"),
        dash.Input(section.ids.detector_configuration_auto_detect_button, "n_clicks"),
        dash.State("runtime-config-store", "data"),
        dash.State(section.page.ids.Scattering.process_dropdown, "value"),
        dash.State(
            section.page.ids.Scattering.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(
            section.page.ids.Scattering.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.State(section.ids.wavelength_nm, "value"),
        prevent_initial_call=True,
    )
    def auto_detect_detector_configuration_preset(
        n_clicks: Any,
        runtime_config_data: Any,
        selected_peak_process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
        current_wavelength_nm: Any,
    ) -> tuple[Any, Any, str, str, bool]:
        if not n_clicks:
            return dash.no_update, dash.no_update, "", "info", False

        runtime_config = RuntimeConfig.from_dict(
            runtime_config_data if isinstance(runtime_config_data, dict) else None
        )
        uploaded_fcs_path = runtime_config.get_str(
            "files.scattering_fcs_file_path",
            default="",
        )

        if not str(uploaded_fcs_path or "").strip():
            return (
                dash.no_update,
                dash.no_update,
                "Upload a scattering FCS file before running detector auto-detect.",
                "warning",
                True,
            )

        selected_detector_channel = services.resolve_selected_peak_detector_channel(
            selected_peak_process_name=selected_peak_process_name,
            detector_dropdown_ids=detector_dropdown_ids,
            detector_dropdown_values=detector_dropdown_values,
        )

        if not str(selected_detector_channel or "").strip():
            return (
                dash.no_update,
                dash.no_update,
                "Select the peak detector channel before running detector auto-detect.",
                "warning",
                True,
            )

        detected_preset = (
            section.model_configuration.detect_detector_preset_from_uploaded_fcs(
                uploaded_fcs_path=uploaded_fcs_path,
                selected_detector_channel=selected_detector_channel,
            )
        )

        if not detected_preset:
            filled_fields: list[str] = []
            missing_fields: list[str] = ["detector preset", "wavelength"]

            status_text = (
                "Auto-detect could only fill some fields. "
                f"Filled: {', '.join(filled_fields) if filled_fields else 'none'}. "
                f"Missing: {', '.join(missing_fields)}. "
                f"Selected peak detector channel: {selected_detector_channel}."
            )

            return (
                dash.no_update,
                dash.no_update,
                status_text,
                "warning",
                True,
            )

        detected_wavelength_nm = (
            section.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=detected_preset,
                current_wavelength_nm=current_wavelength_nm,
            )
        )

        wavelength_status_text = ""

        if detected_wavelength_nm is not None:
            wavelength_status_text = f" Wavelength: {detected_wavelength_nm} nm."

        filled_fields = [f"detector preset={detected_preset}"]
        missing_fields: list[str] = []

        if detected_wavelength_nm is not None:
            filled_fields.append(f"wavelength={detected_wavelength_nm} nm")
        else:
            missing_fields.append("wavelength")

        return (
            detected_preset,
            detected_wavelength_nm
            if detected_wavelength_nm is not None
            else current_wavelength_nm,
            (
                "Auto-detect completed. "
                f"Filled: {', '.join(filled_fields)}. "
                f"Missing: {', '.join(missing_fields) if missing_fields else 'none'}. "
                f"Selected peak detector channel: {selected_detector_channel}."
                f"{wavelength_status_text}"
            ),
            "info",
            True,
        )

    @dash.callback(
        dash.Output(
            section.ids.detector_configuration_custom_values_container,
            "style",
        ),
        dash.Input("runtime-config-store", "data"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        prevent_initial_call=False,
    )
    def toggle_detector_configuration_custom_values(
        runtime_config_data: Any,
        preset_name: Any,
    ) -> dict[str, str]:
        logger.debug(
            "toggle_detector_configuration_custom_values called with preset_name=%r",
            preset_name,
        )

        show_preset_configuration = services.resolve_show_preset_configuration(
            runtime_config_data,
        )

        return services.build_parameter_group_style(
            is_visible=services.should_show_detector_preset_configuration(
                section,
                preset_name=preset_name,
                show_preset_configuration=show_preset_configuration,
            ),
        )

    @dash.callback(
        dash.Output(section.ids.wavelength_nm, "disabled"),
        dash.Output(section.ids.detector_numerical_aperture, "disabled"),
        dash.Output(section.ids.detector_cache_numerical_aperture, "disabled"),
        dash.Output(section.ids.blocker_bar_numerical_aperture, "disabled"),
        dash.Output(section.ids.detector_sampling, "disabled"),
        dash.Output(section.ids.detector_phi_angle_degree, "disabled"),
        dash.Output(section.ids.detector_gamma_angle_degree, "disabled"),
        dash.Output(section.ids.detector_angular_weighting_json, "disabled"),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        prevent_initial_call=False,
    )
    def sync_detector_preset_disabled_state(
        preset_name: Any,
    ) -> tuple[bool, ...]:
        normalized_preset_name = str(preset_name or "").strip()
        is_locked = (
            normalized_preset_name
            != section.model_configuration.custom_detector_preset_name
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
        )

    @dash.callback(
        dash.Output(
            section.ids.wavelength_nm,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.detector_numerical_aperture,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.detector_cache_numerical_aperture,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.blocker_bar_numerical_aperture,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.detector_sampling,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.detector_phi_angle_degree,
            "value",
            allow_duplicate=True,
        ),
        dash.Output(
            section.ids.detector_gamma_angle_degree,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        dash.State(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.detector_numerical_aperture, "value"),
        dash.State(section.ids.detector_cache_numerical_aperture, "value"),
        dash.State(section.ids.blocker_bar_numerical_aperture, "value"),
        dash.State(section.ids.detector_sampling, "value"),
        dash.State(section.ids.detector_phi_angle_degree, "value"),
        dash.State(section.ids.detector_gamma_angle_degree, "value"),
        prevent_initial_call=True,
    )
    def apply_detector_configuration_preset(
        preset_name: Any,
        current_wavelength_nm: Any,
        current_detector_numerical_aperture: Any,
        current_detector_cache_numerical_aperture: Any,
        current_blocker_bar_numerical_aperture: Any,
        current_detector_sampling: Any,
        current_detector_phi_angle_degree: Any,
        current_detector_gamma_angle_degree: Any,
    ) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
        logger.debug(
            "apply_detector_configuration_preset called with preset_name=%r",
            preset_name,
        )

        resolved_values = DetectorGeometryValues(
            *section.model_configuration.resolve_detector_configuration_values(
                preset_name=preset_name,
                current_detector_numerical_aperture=current_detector_numerical_aperture,
                current_detector_cache_numerical_aperture=current_detector_cache_numerical_aperture,
                current_blocker_bar_numerical_aperture=current_blocker_bar_numerical_aperture,
                current_detector_sampling=current_detector_sampling,
                current_detector_phi_angle_degree=current_detector_phi_angle_degree,
                current_detector_gamma_angle_degree=current_detector_gamma_angle_degree,
            )
        )

        resolved_wavelength_nm = (
            section.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=preset_name,
                current_wavelength_nm=current_wavelength_nm,
            )
        )

        logger.debug(
            "apply_detector_configuration_preset returning resolved_values=%r",
            resolved_values,
        )

        resolved_values = replace(
            resolved_values,
            detector_cache_numerical_aperture=services.clamp_detector_cache_numerical_aperture(
                resolved_values.detector_numerical_aperture,
                resolved_values.detector_cache_numerical_aperture,
            ),
        )

        current_values = (
            current_wavelength_nm,
            current_detector_numerical_aperture,
            current_detector_cache_numerical_aperture,
            current_blocker_bar_numerical_aperture,
            current_detector_sampling,
            current_detector_phi_angle_degree,
            current_detector_gamma_angle_degree,
        )
        return tuple(
            dash.no_update if resolved == current else resolved
            for resolved, current in zip(
                (resolved_wavelength_nm, *resolved_values.to_callback_values()),
                current_values,
                strict=True,
            )
        )

    @dash.callback(
        dash.Output(
            section.ids.detector_cache_numerical_aperture,
            "max",
        ),
        dash.Input(section.ids.detector_numerical_aperture, "value"),
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
                - services.DETECTOR_NUMERICAL_APERTURE_EPSILON,
            )

        logger.debug(
            "sync_detector_cache_numerical_aperture_max called with detector_numerical_aperture=%r resolved_max=%r",
            detector_numerical_aperture,
            resolved_cache_max,
        )

        return resolved_cache_max

    @dash.callback(
        dash.Output(
            section.ids.detector_cache_numerical_aperture,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.detector_numerical_aperture, "value"),
        dash.State(section.ids.detector_cache_numerical_aperture, "value"),
        prevent_initial_call=True,
    )
    def clamp_detector_cache_numerical_aperture_after_detector_change(
        detector_numerical_aperture: Any,
        detector_cache_numerical_aperture: Any,
    ) -> Any:
        resolved_detector_cache_numerical_aperture = (
            services.clamp_detector_cache_numerical_aperture(
                detector_numerical_aperture,
                detector_cache_numerical_aperture,
            )
        )

        if (
            resolved_detector_cache_numerical_aperture
            == detector_cache_numerical_aperture
        ):
            return dash.no_update

        return resolved_detector_cache_numerical_aperture
