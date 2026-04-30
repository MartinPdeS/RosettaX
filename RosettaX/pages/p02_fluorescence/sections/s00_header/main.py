# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc

from . import layout as _layout
from . import callbacks as _callbacks


logger = logging.getLogger(__name__)


class Header:
    """
    Fluorescence calibration page header.

    Responsibilities
    ----------------
    - Explain the purpose of the fluorescence calibration page.
    - Show the calibration workflow before the user starts.
    - Clarify what each step produces.
    - Keep explanatory UX content separate from upload and processing logic.
    """

    def __init__(
        self,
        page: Any,
        card_color: str,
    ) -> None:
        self.page = page
        self.card_color = card_color

        logger.debug(
            "Initialized Fluorescence Header section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence calibration header layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Header section has no callbacks.
        """
        return _callbacks.register_callbacks(self)
