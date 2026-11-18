from __future__ import annotations

import dash
import logging
from . import detector_callbacks, preview_callbacks, profile_callbacks, services
from .input_validation import detector_input_validity
from RosettaX.utils import casting
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)


def register_callbacks(section: Model) -> None:
    """
    Register parameter callbacks.
    """
    logger.debug("Registering Parameters callbacks.")

    register_visibility_callbacks(section)
    register_refractive_index_callbacks(section)
    detector_callbacks.register_detector_configuration_callbacks(section)
    register_detector_numerical_aperture_warning_callback(section)
    register_detector_input_validation_callback(section)
    preview_callbacks.register_optical_configuration_preview_callback(section)
    profile_callbacks.register_runtime_sync_callbacks(section)


def register_detector_input_validation_callback(section: Model) -> None:
    """Highlight invalid custom detector values and angular weighting."""
    field_ids = (
        section.ids.wavelength_nm,
        section.ids.detector_numerical_aperture,
        section.ids.detector_cache_numerical_aperture,
        section.ids.blocker_bar_numerical_aperture,
        section.ids.detector_sampling,
        section.ids.detector_phi_angle_degree,
        section.ids.detector_gamma_angle_degree,
    )

    @dash.callback(
        *[dash.Output(field_id, "className") for field_id in field_ids],
        dash.Output(section.ids.detector_angular_weighting_json, "className"),
        *[dash.Input(field_id, "value") for field_id in field_ids],
        dash.Input(section.ids.medium_refractive_index_custom, "value"),
        dash.Input(section.ids.detector_angular_weighting_alert, "is_open"),
        prevent_initial_call=False,
    )
    def update_detector_input_validation(
        wavelength_nm: Any, detector_na: Any, cache_na: Any, blocker_na: Any,
        sampling: Any, phi_degree: Any, gamma_degree: Any,
        medium_refractive_index: Any, angular_weighting_invalid: Any,
    ) -> tuple[str, ...]:
        validity = detector_input_validity(
            wavelength_nm=wavelength_nm, detector_na=detector_na, cache_na=cache_na,
            blocker_na=blocker_na, sampling=sampling, phi_degree=phi_degree,
            gamma_degree=gamma_degree, medium_refractive_index=medium_refractive_index,
        )
        invalid_class = "custom-detector-input-invalid"
        return (*("" if valid else invalid_class for valid in validity),
                invalid_class if angular_weighting_invalid else "")


def register_visibility_callbacks(section: Model) -> None:
    """
    Register particle model visibility callbacks.
    """

    @dash.callback(
        dash.Output(
            section.ids.particle_configuration_custom_values_container,
            "style",
        ),
        dash.Output(section.ids.solid_sphere_container, "style"),
        dash.Output(section.ids.core_shell_container, "style"),
        dash.Input("runtime-config-store", "data"),
        dash.Input(section.ids.mie_model, "value"),
        prevent_initial_call=False,
    )
    def toggle_parameter_blocks(
        runtime_config_data: Any,
        mie_model_value: str | None,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        resolved_mie_model = section.model_configuration.resolve_mie_model(mie_model_value)
        show_preset_configuration = services.resolve_show_preset_configuration(
            runtime_config_data,
        )

        resolved_styles = (
            services.build_parameter_group_style(
                is_visible=show_preset_configuration,
            ),
            services.build_parameter_group_style(
                is_visible=resolved_mie_model != "Core/Shell Sphere",
            ),
            services.build_parameter_group_style(
                is_visible=resolved_mie_model == "Core/Shell Sphere",
            ),
        )

        logger.debug(
            "toggle_parameter_blocks called with mie_model_value=%r show_preset_configuration=%r styles=%r",
            mie_model_value,
            show_preset_configuration,
            resolved_styles,
        )

        return resolved_styles


def register_refractive_index_callbacks(section: Model) -> None:
    """Resolve material inputs together and avoid emitting unchanged values."""

    @dash.callback(
        dash.Output(
            section.ids.medium_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.particle_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.core_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.shell_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Input(section.ids.medium_refractive_index_source, "value"),
        dash.Input(section.ids.particle_refractive_index_source, "value"),
        dash.Input(section.ids.core_refractive_index_source, "value"),
        dash.Input(section.ids.shell_refractive_index_source, "value"),
        dash.Input(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.medium_refractive_index_custom, "value"),
        dash.State(section.ids.particle_refractive_index_custom, "value"),
        dash.State(section.ids.core_refractive_index_custom, "value"),
        dash.State(section.ids.shell_refractive_index_custom, "value"),
        prevent_initial_call=True,
    )
    def apply_refractive_index_presets(
        medium_source: Any,
        particle_source: Any,
        core_source: Any,
        shell_source: Any,
        wavelength_nm: Any,
        current_medium: Any,
        current_particle: Any,
        current_core: Any,
        current_shell: Any,
    ) -> tuple[Any, ...]:
        sources = (medium_source, particle_source, core_source, shell_source)
        current_values = (current_medium, current_particle, current_core, current_shell)
        resolved_values = (
            section.model_configuration.apply_refractive_index_preset(
                preset_value=source,
                wavelength_nm=wavelength_nm,
                current_value=current,
            )
            for source, current in zip(sources, current_values, strict=True)
        )
        return tuple(
            dash.no_update if resolved == current else resolved
            for resolved, current in zip(resolved_values, current_values, strict=True)
        )


def register_detector_numerical_aperture_warning_callback(section: Model) -> None:
    """
    Register a warning callback when detector NA exceeds the medium index.
    """

    @dash.callback(
        dash.Output(section.ids.detector_numerical_aperture_warning, "children"),
        dash.Output(section.ids.detector_numerical_aperture_warning, "is_open"),
        dash.Input(section.ids.detector_numerical_aperture, "value"),
        dash.Input(section.ids.medium_refractive_index_custom, "value"),
        prevent_initial_call=False,
    )
    def update_detector_numerical_aperture_warning(
        detector_numerical_aperture: Any,
        medium_refractive_index: Any,
    ) -> tuple[str, bool]:
        resolved_detector_numerical_aperture = casting.as_optional_float(
            detector_numerical_aperture,
        )
        resolved_medium_refractive_index = casting.as_optional_float(
            medium_refractive_index,
        )

        if (
            resolved_detector_numerical_aperture is None
            or resolved_medium_refractive_index is None
            or resolved_detector_numerical_aperture <= resolved_medium_refractive_index
        ):
            return "", False

        warning_message = (
            f"Detector NA ({resolved_detector_numerical_aperture:.3f}) exceeds the medium refractive index "
            f"({resolved_medium_refractive_index:.3f}). Physically, NA should satisfy NA <= n_medium."
        )

        logger.debug(
            "update_detector_numerical_aperture_warning opening alert with detector_numerical_aperture=%r medium_refractive_index=%r",
            resolved_detector_numerical_aperture,
            resolved_medium_refractive_index,
        )

        return warning_message, True
