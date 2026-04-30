# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash_bootstrap_components as dbc

from RosettaX.pages.p03_scattering.state import ScatteringPageState
from RosettaX.utils import directories
from RosettaX.utils import styling
from RosettaX.utils import ui_forms
from RosettaX.workflow import save


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

        self.config = save.SaveConfig(
            calibration_kind="scattering",
            output_directory=directories.scattering_calibration,
            header_title=f"{self.section_number}. Save calibration",
            button_text="Save calibration",
            file_name_placeholder="calibration name",
            saved_message_prefix="Saved calibration",
            failure_message="Failed to save calibration. See terminal logs for details.",
        )

        self.adapter = save.PageStateSaveAdapter(
            state_class=ScatteringPageState,
            calibration_payload_attribute="calibration_payload",
        )

        self.layout_builder = save.SaveLayout(
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
        section_style = styling.build_workflow_section_legacy_style(
            self.card_color,
        )

        return ui_forms.apply_workflow_section_card_style(
            card=self.layout_builder.get_layout(),
            header_background=section_style["header_background"],
            header_border=section_style["header_border"],
            left_border=section_style["left_border"],
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the scattering save section.
        """
        save.register_save_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
            calibration_store_id=None,
            page_state_store_id=self.page.ids.State.page_state_store,
        )