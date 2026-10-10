from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dash

from RosettaX.utils import casting

from . import detector_callbacks, preview_callbacks, profile_callbacks, services

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)


def register_callbacks(section: Model) -> None:
    """
    Register parameter callbacks.
    """
    logger.debug("Registering Parameters callbacks.")

    register_visibility_callbacks(section)
    profile_callbacks.register_scatterer_preset_callbacks(section)
    register_refractive_index_callbacks(section)
    detector_callbacks.register_detector_configuration_callbacks(section)
    register_detector_numerical_aperture_warning_callback(section)
    preview_callbacks.register_optical_configuration_preview_callback(section)
    profile_callbacks.register_runtime_sync_callbacks(section)


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
        dash.Input(section.ids.scatterer_preset, "value"),
        prevent_initial_call=False,
    )
    def toggle_parameter_blocks(
        runtime_config_data: Any,
        mie_model_value: str | None,
        scatterer_preset: Any,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        resolved_mie_model = section.model_configuration.resolve_mie_model(
            mie_model_value,
        )
        show_preset_configuration = services.resolve_show_preset_configuration(
            runtime_config_data,
        )

        resolved_styles = (
            services.build_parameter_group_style(
                is_visible=services.should_show_scatterer_preset_configuration(
                    section,
                    preset_name=scatterer_preset,
                    show_preset_configuration=show_preset_configuration,
                ),
            ),
            services.build_parameter_group_style(
                is_visible=resolved_mie_model != "Core/Shell Sphere",
            ),
            services.build_parameter_group_style(
                is_visible=resolved_mie_model == "Core/Shell Sphere",
            ),
        )

        logger.debug(
            "toggle_parameter_blocks called with mie_model_value=%r scatterer_preset=%r show_preset_configuration=%r styles=%r",
            mie_model_value,
            scatterer_preset,
            show_preset_configuration,
            resolved_styles,
        )

        return resolved_styles


def register_refractive_index_callbacks(section: Model) -> None:
    """
    Register refractive index preset callbacks.
    """

    @dash.callback(
        dash.Output(
            section.ids.medium_refractive_index_custom,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.medium_refractive_index_source, "value"),
        dash.Input(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.medium_refractive_index_custom, "value"),
        prevent_initial_call=True,
    )
    def apply_medium_preset(
        preset_value: Any,
        wavelength_nm: Any,
        current_value: Any,
    ) -> Any:
        return section.model_configuration.apply_refractive_index_preset(
            preset_value=preset_value,
            wavelength_nm=wavelength_nm,
            current_value=current_value,
        )

    @dash.callback(
        dash.Output(
            section.ids.particle_refractive_index_custom,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.particle_refractive_index_source, "value"),
        dash.Input(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.particle_refractive_index_custom, "value"),
        prevent_initial_call=True,
    )
    def apply_particle_preset(
        preset_value: Any,
        wavelength_nm: Any,
        current_value: Any,
    ) -> Any:
        return section.model_configuration.apply_refractive_index_preset(
            preset_value=preset_value,
            wavelength_nm=wavelength_nm,
            current_value=current_value,
        )

    @dash.callback(
        dash.Output(
            section.ids.core_refractive_index_custom,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.core_refractive_index_source, "value"),
        dash.Input(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.core_refractive_index_custom, "value"),
        prevent_initial_call=True,
    )
    def apply_core_preset(
        preset_value: Any,
        wavelength_nm: Any,
        current_value: Any,
    ) -> Any:
        return section.model_configuration.apply_refractive_index_preset(
            preset_value=preset_value,
            wavelength_nm=wavelength_nm,
            current_value=current_value,
        )

    @dash.callback(
        dash.Output(
            section.ids.shell_refractive_index_custom,
            "value",
            allow_duplicate=True,
        ),
        dash.Input(section.ids.shell_refractive_index_source, "value"),
        dash.Input(section.ids.wavelength_nm, "value"),
        dash.State(section.ids.shell_refractive_index_custom, "value"),
        prevent_initial_call=True,
    )
    def apply_shell_preset(
        preset_value: Any,
        wavelength_nm: Any,
        current_value: Any,
    ) -> Any:
        return section.model_configuration.apply_refractive_index_preset(
            preset_value=preset_value,
            wavelength_nm=wavelength_nm,
            current_value=current_value,
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
