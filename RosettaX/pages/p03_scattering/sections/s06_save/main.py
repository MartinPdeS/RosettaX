# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc

from RosettaX.pages.p03_scattering.state import ScatteringPageState
from RosettaX.utils import styling, ui_forms
from RosettaX.workflow.save.adapters import PageStateSaveAdapter
from RosettaX.workflow.save.callbacks import register_save_callbacks
from RosettaX.workflow.save.layout import SaveLayout
from RosettaX.workflow.save.models import SaveConfig


logger = logging.getLogger(__name__)


class Save:
    """
    Scattering calibration save section.
    """

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.ids = page.ids.Save
        self.section_number = section_number
        self.card_color = card_color

        self.config = SaveConfig(
            calibration_kind="scattering",
            header_title=f"{self.section_number}. Save calibration",
            button_text="Download calibration.json",
            file_name_placeholder="calibration name",
            saved_message_prefix="Prepared calibration download",
            failure_message="Failed to prepare calibration download. See terminal logs for details.",
        )

        self.adapter = PageStateSaveAdapter(
            state_class=ScatteringPageState,
            calibration_payload_attribute="calibration_payload",
        )

        self.layout_builder = SaveLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Scattering Save section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Create the scattering save section layout.
        """
        return ui_forms.apply_workflow_section_card_style(
            card=self.layout_builder.get_layout(),
            color_name=self.card_color,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the scattering save section.
        """
        register_save_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
            calibration_store_id=None,
            page_state_store_id=self.page.ids.State.page_state_store,
        )