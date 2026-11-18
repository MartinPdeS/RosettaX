from __future__ import annotations

import dash
import logging
from . import services
from RosettaX.pages.p00_sidebar.ids import SidebarIds
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main import Model

logger = logging.getLogger(__name__)


def register_runtime_sync_callbacks(section: Model) -> None:
    """
    Register runtime configuration synchronization callback.
    """

    @dash.callback(
        dash.Output(section.ids.detector_configuration_preset, "value"),
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
            return tuple(dash.no_update for _ in range(13))

        logger.debug(
            "sync_parameters_from_runtime_config called with runtime_config_data=%r",
            runtime_config_data,
        )

        state = services.resolve_profile_parameter_state(
            runtime_config_data,
            configuration=section.model_configuration,
        )
        return state.to_callback_values()
