# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc

from .callbacks import ApplyCallbacks
from .layout import ApplyLayout


logger = logging.getLogger(__name__)


class Apply:
    """
    Apply a saved calibration to uploaded FCS files and export calibrated files.

    This class is intentionally thin. The implementation is split across:

    - ``apply_section.layout`` for Dash component construction.
    - ``apply_section.callbacks`` for Dash callback registration.
    - ``apply_section.services`` for pure helper logic.

    Responsibilities
    ----------------
    - Keep the public section API used by the page.
    - Hold shared section configuration.
    - Delegate layout construction.
    - Delegate callback registration.
    """

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color

        self.layout_builder = ApplyLayout(
            page=self.page,
            section_number=self.section_number,
            card_color=self.card_color,
        )

        self.callback_registrar = ApplyCallbacks(
            page=self.page,
        )

        logger.debug(
            "Initialized Apply section with page=%s section_number=%r card_color=%r",
            self.page.__class__.__name__,
            self.section_number,
            self.card_color,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the apply and export layout.

        Returns
        -------
        dbc.Card
            Apply and export section card.
        """
        logger.debug(
            "Apply.get_layout called for page=%s",
            self.page.__class__.__name__,
        )

        return self.layout_builder.build_layout()

    def register_callbacks(self) -> None:
        """
        Register all apply and export callbacks.
        """
        logger.debug(
            "Apply.register_callbacks called for page=%s",
            self.page.__class__.__name__,
        )

        self.callback_registrar.register_callbacks()


__all__ = [
    "Apply",
]