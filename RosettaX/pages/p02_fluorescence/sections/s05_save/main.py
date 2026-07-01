# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc
from RosettaX.workflow.save.adapters import CalibrationStoreSaveAdapter
from RosettaX.workflow.save.layout import SaveLayout
from RosettaX.workflow.save.models import SaveConfig

from . import layout as _layout
from . import callbacks as _callbacks


logger = logging.getLogger(__name__)


class Save:
    """
    Fluorescence calibration save section.

    Responsibilities
    ----------------
    - Provide the fluorescence save layout.
    - Register the reusable save workflow callbacks.

    Notes
    -----
    The fluorescence calibration payload is read from the calibration store.
    Saving, validation, file creation, and sidebar refresh signaling are
    delegated to RosettaX.workflow.save.
    """

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "pink",
    ) -> None:
        self.page = page
        self.ids = page.ids.Save
        self.section_number = section_number
        self.card_color = card_color

        self.config = SaveConfig(
            calibration_kind="fluorescence",
            header_title=f"{self.section_number}. Save calibration",
            button_text="Download calibration.json",
            file_name_placeholder="calibration name",
            output_channel_name_placeholder="e.g. FITC (MESF)",
            require_output_channel_name=True,
            saved_message_prefix="Prepared calibration download",
            failure_message="Failed to prepare calibration download. See terminal logs for details.",
        )

        self.adapter = CalibrationStoreSaveAdapter()

        self.layout_builder = SaveLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Fluorescence Save section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Create the fluorescence save section layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence save section.
        """
        _callbacks.register_callbacks(self)
