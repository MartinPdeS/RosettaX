# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from ...state import ScatteringPageState
from RosettaX.utils import styling, ui_forms
from RosettaX.workflow import upload


logger = logging.getLogger(__name__)


class Upload:
    """
    Scattering FCS upload section.
    """

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "blue",
    ) -> None:
        self.page = page
        self.ids = page.ids.Upload
        self.section_number = section_number
        self.card_color = card_color

        self.upload_tooltip_target_id = f"{self.ids.upload}-calibration-file-info-target"
        self.upload_tooltip_id = f"{self.ids.upload}-calibration-file-info-tooltip"

        self.config = upload.UploadConfig(
            card_title=self._build_card_title(),
            upload_link_text="Select bead FCS file",
            initial_runtime_config_path="files.scattering_fcs_file_path",
            runtime_config_output_path="files.scattering_fcs_file_path",
            accepted_file_extensions=".fcs",
            runtime_config_store_id="runtime-config-store",
            body_style_key="card_body_scroll",
        )

        self.adapter = upload.ScatteringUploadAdapter(
            state_class=ScatteringPageState,
        )

        self.layout_builder = upload.UploadLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Scattering Upload section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering upload section layout.
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

    def _build_card_title(self) -> dash.html.Div:
        """
        Build the card title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title=f"{self.section_number}. Upload calibration FCS file",
            tooltip_target_id=self.upload_tooltip_target_id,
            tooltip_id=self.upload_tooltip_id,
            tooltip_text=(
                "Upload an FCS file measured from calibration beads. "
                "The bead populations should have known reference values, "
                "so RosettaX can link measured peak positions to physical "
                "calibration standards."
            ),
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the scattering upload section.
        """
        upload.register_upload_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
        )