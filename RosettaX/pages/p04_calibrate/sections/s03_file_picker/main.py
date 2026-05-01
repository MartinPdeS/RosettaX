# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Any

import dash_bootstrap_components as dbc

from . import services
from .callbacks import FilePickerCallbacks
from .layout import FilePickerLayout


logger = logging.getLogger(__name__)


class FilePicker:
    """
    Input FCS file picker section.

    This class is intentionally thin. The implementation is split across:

    - ``layout`` for Dash component construction.
    - ``callbacks`` for Dash callback registration.
    - ``services`` for file saving, validation, and consistency checks.

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

        services.validate_page_contract(
            page=self.page,
        )

        self.upload_directory: Path = services.build_upload_directory()

        self.layout_builder = FilePickerLayout(
            page=self.page,
            section_number=self.section_number,
            card_color=self.card_color,
        )

        self.callback_registrar = FilePickerCallbacks(
            page=self.page,
            upload_directory=self.upload_directory,
        )

        logger.debug(
            "Initialized FilePicker section with page=%s section_number=%r "
            "card_color=%r upload_directory=%r",
            self.page.__class__.__name__,
            self.section_number,
            self.card_color,
            str(self.upload_directory),
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the file picker layout.

        Returns
        -------
        dbc.Card
            File picker section card.
        """
        logger.debug(
            "FilePicker.get_layout called for page=%s",
            self.page.__class__.__name__,
        )

        return self.layout_builder.build_layout()

    def register_callbacks(self) -> None:
        """
        Register all file picker callbacks.
        """
        logger.debug(
            "FilePicker.register_callbacks called for page=%s",
            self.page.__class__.__name__,
        )

        self.callback_registrar.register_callbacks()


__all__ = [
    "FilePicker",
]