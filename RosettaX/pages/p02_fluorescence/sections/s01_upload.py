# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms
from RosettaX.workflow import upload


logger = logging.getLogger(__name__)


class Upload:
    """
    Fluorescence FCS upload section.

    Responsibilities
    ----------------
    - Provide the fluorescence FCS upload card.
    - Register the reusable upload workflow callbacks.

    Notes
    -----
    The page level explanation is handled by ``s00_header.Header``.
    Upload persistence, runtime config synchronization, filename display, and
    page state reset behavior are delegated to ``RosettaX.workflow.upload``.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Upload

        self.upload_tooltip_target_id = f"{self.ids.upload}-calibration-file-info-target"
        self.upload_tooltip_id = f"{self.ids.upload}-calibration-file-info-tooltip"

        self.config = upload.UploadConfig(
            card_title=self._build_card_title(),
            upload_link_text="Select bead FCS file",
            initial_runtime_config_path="files.fluorescence_fcs_file_path",
            runtime_config_output_path="files.fluorescence_fcs_file_path",
            accepted_file_extensions=".fcs",
            runtime_config_store_id="runtime-config-store",
            body_style_key="body_scroll",
        )

        self.adapter = upload.FluorescenceUploadAdapter()

        self.layout_builder = upload.UploadLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Fluorescence Upload section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the upload section layout.
        """
        card = self.layout_builder.get_layout()

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _build_card_title(self) -> dash.html.Div:
        """
        Build the card title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title="1. Upload calibration FCS file",
            tooltip_target_id=self.upload_tooltip_target_id,
            tooltip_id=self.upload_tooltip_id,
            tooltip_text=(
                "Upload an FCS file measured from fluorescence calibration "
                "beads with known MESF values. RosettaX uses the bead peak "
                "positions and the known MESF references to build the "
                "fluorescence calibration."
            ),
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence upload section.
        """
        upload.register_upload_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
        )