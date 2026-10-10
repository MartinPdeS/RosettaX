from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dash

from RosettaX.pages.p00_sidebar.ids import SidebarIds

from . import services

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)


def register_runtime_sync_callbacks(section: Model) -> None:
    """
    Register runtime configuration synchronization callback.
    """

    @dash.callback(
        dash.Output(section.ids.detector_configuration_preset, "value"),
        dash.Output(section.ids.scatterer_preset, "value"),
        dash.Output(section.ids.mie_model, "value"),
        dash.Output(section.ids.medium_refractive_index_custom, "value"),
        dash.Output(section.ids.particle_refractive_index_custom, "value"),
        dash.Output(section.ids.core_refractive_index_custom, "value"),
        dash.Output(section.ids.shell_refractive_index_custom, "value"),
        dash.Output(section.ids.wavelength_nm, "value"),
        dash.Output(section.ids.detector_numerical_aperture, "value"),
        dash.Output(section.ids.detector_cache_numerical_aperture, "value"),
        dash.Output(section.ids.blocker_bar_numerical_aperture, "value"),
        dash.Output(section.ids.detector_sampling, "value"),
        dash.Output(section.ids.detector_phi_angle_degree, "value"),
        dash.Output(section.ids.detector_gamma_angle_degree, "value"),
        dash.Input("runtime-config-store", "data"),
        dash.Input(SidebarIds.profile_load_event_store, "data"),
        prevent_initial_call=False,
    )
    def sync_parameters_from_runtime_config(
        runtime_config_data: Any,
        _profile_load_event_data: Any,
    ) -> tuple[Any, ...]:
        if dash.ctx.triggered_id == "runtime-config-store":
            return tuple(dash.no_update for _ in range(14))

        logger.debug(
            "sync_parameters_from_runtime_config called with runtime_config_data=%r",
            runtime_config_data,
        )

        state = services.resolve_profile_parameter_state(
            runtime_config_data,
            configuration=section.model_configuration,
        )
        return state.to_callback_values()


def register_scatterer_preset_callbacks(section: Model) -> None:
    """
    Register scatterer preset callbacks.
    """

    @dash.callback(
        dash.Output(section.ids.mie_model, "value", allow_duplicate=True),
        dash.Output(
            section.ids.medium_refractive_index_source, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.medium_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.particle_refractive_index_source, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.particle_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.core_refractive_index_source, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.core_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.shell_refractive_index_source, "value", allow_duplicate=True
        ),
        dash.Output(
            section.ids.shell_refractive_index_custom, "value", allow_duplicate=True
        ),
        dash.Input(section.ids.scatterer_preset, "value"),
        dash.State(section.ids.mie_model, "value"),
        dash.State(section.ids.medium_refractive_index_source, "value"),
        dash.State(section.ids.medium_refractive_index_custom, "value"),
        dash.State(section.ids.particle_refractive_index_source, "value"),
        dash.State(section.ids.particle_refractive_index_custom, "value"),
        dash.State(section.ids.core_refractive_index_source, "value"),
        dash.State(section.ids.core_refractive_index_custom, "value"),
        dash.State(section.ids.shell_refractive_index_source, "value"),
        dash.State(section.ids.shell_refractive_index_custom, "value"),
        dash.State(section.ids.wavelength_nm, "value"),
        prevent_initial_call=True,
    )
    def apply_scatterer_preset(
        preset_name: Any,
        current_mie_model: Any,
        current_medium_refractive_index_source: Any,
        current_medium_refractive_index: Any,
        current_particle_refractive_index_source: Any,
        current_particle_refractive_index: Any,
        current_core_refractive_index_source: Any,
        current_core_refractive_index: Any,
        current_shell_refractive_index_source: Any,
        current_shell_refractive_index: Any,
        wavelength_nm: Any,
    ) -> tuple[Any, ...]:
        logger.debug(
            "apply_scatterer_preset called with triggered_id=%r preset_name=%r",
            dash.ctx.triggered_id,
            preset_name,
        )

        (
            resolved_mie_model,
            resolved_medium_refractive_index_source,
            resolved_medium_refractive_index,
            resolved_particle_refractive_index_source,
            resolved_particle_refractive_index,
            resolved_core_refractive_index_source,
            resolved_core_refractive_index,
            resolved_shell_refractive_index_source,
            resolved_shell_refractive_index,
        ) = section.model_configuration.resolve_scatterer_preset_values(
            preset_name=preset_name,
            current_mie_model=current_mie_model,
            current_medium_refractive_index_source=current_medium_refractive_index_source,
            current_medium_refractive_index=current_medium_refractive_index,
            current_particle_refractive_index_source=current_particle_refractive_index_source,
            current_particle_refractive_index=current_particle_refractive_index,
            current_core_refractive_index_source=current_core_refractive_index_source,
            current_core_refractive_index=current_core_refractive_index,
            current_shell_refractive_index_source=current_shell_refractive_index_source,
            current_shell_refractive_index=current_shell_refractive_index,
            wavelength_nm=wavelength_nm,
        )

        return (
            resolved_mie_model,
            resolved_medium_refractive_index_source,
            resolved_medium_refractive_index,
            resolved_particle_refractive_index_source,
            resolved_particle_refractive_index,
            resolved_core_refractive_index_source,
            resolved_core_refractive_index,
            resolved_shell_refractive_index_source,
            resolved_shell_refractive_index,
        )

    @dash.callback(
        dash.Output(section.ids.mie_model, "disabled"),
        dash.Output(section.ids.medium_refractive_index_source, "disabled"),
        dash.Output(section.ids.medium_refractive_index_custom, "disabled"),
        dash.Output(section.ids.particle_refractive_index_source, "disabled"),
        dash.Output(section.ids.particle_refractive_index_custom, "disabled"),
        dash.Output(section.ids.core_refractive_index_source, "disabled"),
        dash.Output(section.ids.core_refractive_index_custom, "disabled"),
        dash.Output(section.ids.shell_refractive_index_source, "disabled"),
        dash.Output(section.ids.shell_refractive_index_custom, "disabled"),
        dash.Input(section.ids.scatterer_preset, "value"),
        prevent_initial_call=False,
    )
    def sync_scatterer_preset_disabled_state(
        preset_name: Any,
    ) -> tuple[bool, ...]:
        is_locked = (
            section.model_configuration.scatterer_preset_disables_manual_controls(
                preset_name=preset_name,
            )
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
