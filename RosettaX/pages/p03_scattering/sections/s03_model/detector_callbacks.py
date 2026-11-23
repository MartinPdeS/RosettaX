from __future__ import annotations

import dash
import logging
from . import services
from .models import DetectorGeometryValues
from dataclasses import replace
from RosettaX.utils import casting
from RosettaX.workflow.detector.configuration import infer_detector_preset_from_metadata
from typing import TYPE_CHECKING, Any

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
        dash.Input(section.ids.detector_configuration_auto_detect_button, "n_clicks"),
        dash.Input(section.page.ids.Scattering.process_dropdown, "value"),
        dash.Input(
            section.page.ids.Scattering.process_detector_dropdown_pattern(),
            "value",
        ),
        dash.Input(section.page.ids.State.system_model, "value"),
        dash.State(section.page.ids.State.page_state_store, "data"),
        dash.State(
            section.page.ids.Scattering.process_detector_dropdown_pattern(),
            "id",
        ),
        dash.State(section.ids.wavelength_nm, "value"),
        prevent_initial_call=True,
    )
    def auto_detect_detector_configuration_preset(
        n_clicks: Any,
        selected_peak_process_name: Any,
        detector_dropdown_values: list[Any],
        instrument_catalog_key: str | None,
        page_state_payload: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        current_wavelength_nm: Any,
    ) -> tuple[Any, Any, str]:
        requested = dash.ctx.triggered_id == section.ids.detector_configuration_auto_detect_button
        if requested and not n_clicks:
            return dash.no_update, dash.no_update, ""

        uploaded_fcs_path = (page_state_payload or {}).get("uploaded_fcs_path")
        if not str(uploaded_fcs_path or "").strip():
            return (
                dash.no_update,
                dash.no_update,
                "Upload a scattering FCS file to match an optical preset." if requested else "",
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
                "Select the scatter channel in Detect peaks first." if requested else "",
            )

        detected_preset = infer_detector_preset_from_metadata(
            metadata=None,
            selected_detector_channel=selected_detector_channel,
            instrument_catalog_key=instrument_catalog_key,
        )

        if not detected_preset:
            channel_wavelength_nm = section.model_configuration.detect_wavelength_nm_from_detector_channel(
                selected_detector_channel,
            )
            if channel_wavelength_nm is not None:
                return (
                    dash.no_update,
                    channel_wavelength_nm,
                    f"Detected {channel_wavelength_nm:g} nm from {selected_detector_channel}. "
                    "No matching optical preset. Enter or verify the detector geometry.",
                )
            return (
                dash.no_update,
                dash.no_update,
                f"No matching optical preset for {selected_detector_channel}. "
                "Enter or verify the detector geometry and wavelength.",
            )

        detected_wavelength_nm = (
            section.model_configuration.resolve_detector_preset_wavelength_nm(
                preset_name=detected_preset,
                current_wavelength_nm=current_wavelength_nm,
            )
        )

        return (
            detected_preset,
            detected_wavelength_nm
            if detected_wavelength_nm is not None
            else current_wavelength_nm,
            "Detector preset applied." if requested else "",
        )

    @dash.callback(
        dash.Output(
            section.ids.detector_configuration_custom_values_container,
            "style",
        ),
        dash.Input(section.ids.detector_configuration_preset, "value"),
        prevent_initial_call=False,
    )
    def toggle_detector_configuration_custom_values(
        preset_name: Any,
    ) -> dict[str, str]:
        return services.build_parameter_group_style(
            is_visible=(
                str(preset_name or "").strip()
                == section.model_configuration.custom_detector_preset_name
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
