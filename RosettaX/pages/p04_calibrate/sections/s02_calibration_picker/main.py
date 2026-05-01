# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any

import dash_bootstrap_components as dbc

from . import services
from .callbacks import CalibrationPickerCallbacks
from .layout import CalibrationPickerLayout


logger = logging.getLogger(__name__)


class CalibrationPicker:
    """
    Calibration file picker section.

    This class is intentionally thin. The implementation is split across:

    - ``calibration_picker.layout`` for Dash component construction.
    - ``calibration_picker.callbacks`` for Dash callback registration.
    - ``calibration_picker.services`` for pure helper logic.

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
        self.secondary_card_color = "gray"

        self.folder_definitions: list[tuple[str, str, Path]] = (
            services.build_default_folder_definitions()
        )

        self.layout_builder = CalibrationPickerLayout(
            page=self.page,
            section_number=self.section_number,
            card_color=self.card_color,
            secondary_card_color=self.secondary_card_color,
        )

        self.callback_registrar = CalibrationPickerCallbacks(
            page=self.page,
            folder_definitions=self.folder_definitions,
        )

        logger.debug(
            "Initialized CalibrationPicker section with page=%s section_number=%r "
            "card_color=%r secondary_card_color=%r folder_definitions=%r",
            self.page.__class__.__name__,
            self.section_number,
            self.card_color,
            self.secondary_card_color,
            [
                (
                    folder_key,
                    folder_label,
                    str(folder_path),
                )
                for folder_key, folder_label, folder_path in self.folder_definitions
            ],
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the calibration picker layout.

        Returns
        -------
        dbc.Card
            Calibration picker section card.
        """
        logger.debug(
            "CalibrationPicker.get_layout called for page=%s",
            self.page.__class__.__name__,
        )

        return self.layout_builder.build_layout()

    def register_callbacks(self) -> None:
        """
        Register all calibration picker callbacks.
        """
        logger.debug(
            "CalibrationPicker.register_callbacks called for page=%s",
            self.page.__class__.__name__,
        )

        self.callback_registrar.register_callbacks()


__all__ = [
    "CalibrationPicker",
]