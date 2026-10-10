"""Assembly of the scattering optical configuration section."""

import logging
from typing import Any

import dash_bootstrap_components as dbc

from RosettaX.workflow.scattering import ModelConfiguration

from . import callbacks, layout

logger = logging.getLogger(__name__)


class Model:
    """Assemble scattering controls and register their section callbacks.

    Layout builders own the component tree; services resolve local state.
    Reusable scientific behavior belongs to the scattering workflow.
    """

    model_configuration = ModelConfiguration

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.ids = page.ids.Parameters
        self.section_number = section_number
        self.card_color = card_color
        self.default_values = self.model_configuration.build_default_profile_defaults()

        self.section_tooltip_target_id = f"{self.ids.mie_model}-section-info-target"
        self.section_tooltip_id = f"{self.ids.mie_model}-section-info-tooltip"

        self.particle_configuration_tooltip_target_id = (
            f"{self.ids.mie_model}-particle-info-target"
        )
        self.particle_configuration_tooltip_id = (
            f"{self.ids.mie_model}-particle-info-tooltip"
        )

        self.scatterer_preset_tooltip_target_id = (
            f"{self.ids.scatterer_preset}-info-target"
        )
        self.scatterer_preset_tooltip_id = f"{self.ids.scatterer_preset}-info-tooltip"

        self.detector_preset_tooltip_target_id = (
            f"{self.ids.detector_configuration_preset}-info-target"
        )
        self.detector_preset_tooltip_id = (
            f"{self.ids.detector_configuration_preset}-info-tooltip"
        )

        self.optical_preview_tooltip_target_id = (
            f"{self.ids.optical_configuration_preview}-info-target"
        )
        self.optical_preview_tooltip_id = (
            f"{self.ids.optical_configuration_preview}-info-tooltip"
        )

        logger.debug(
            "Initialized Parameters section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """Build the section layout."""
        return layout.get_layout(self)

    def register_callbacks(self) -> None:
        """Register the section callbacks."""
        callbacks.register_callbacks(self)
