# -*- coding: utf-8 -*-

import logging

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

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Upload

        self.config = upload.UploadConfig(
            card_title="1. Upload calibration FCS file",
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

    def get_layout(self):
        """
        Build the upload section layout.
        """
        return self.layout_builder.get_layout()

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