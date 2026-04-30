# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc

from RosettaX.workflow import save
from RosettaX.utils import directories
from RosettaX.utils import styling
from RosettaX.utils import ui_forms


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

        self.config = save.SaveConfig(
            calibration_kind="fluorescence",
            output_directory=directories.fluorescence_calibration,
            header_title=f"{self.section_number}. Save calibration",
            button_text="Save calibration",
            file_name_placeholder="calibration name",
            saved_message_prefix="Saved calibration",
            failure_message="Failed to save calibration. See terminal logs for details.",
        )

        self.adapter = save.CalibrationStoreSaveAdapter()

        self.layout_builder = save.SaveLayout(
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
        card = self.layout_builder.get_layout()

        section_style = styling.build_workflow_section_legacy_style(
            self.card_color,
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_background=section_style["header_background"],
            header_border=section_style["header_border"],
            left_border=section_style["left_border"],
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence save section.
        """
        save.register_save_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
            calibration_store_id=self.page.ids.Calibration.calibration_store,
            page_state_store_id=None,
        )