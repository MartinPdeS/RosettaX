# -*- coding: utf-8 -*-

import logging

from ..state import ScatteringPageState
from RosettaX.workflow import upload


logger = logging.getLogger(__name__)


class Upload:
    """
    Scattering FCS upload section.

    Responsibilities
    ----------------
    - Provide the scattering upload layout.
    - Register the reusable upload workflow callbacks.

    Notes
    -----
    Upload persistence, runtime config synchronization, filename display, and
    page state update behavior are delegated to RosettaX.workflow.upload.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Upload

        self.config = upload.UploadConfig(
            section_title="Scattering calibration",
            card_title="1. Upload Calibration FCS File",
            upload_link_text="Select Bead File",
            description=(
                "Start by uploading the FCS file used for the scattering calibration workflow. "
                "After upload, RosettaX will keep the selected file in session state and use it as "
                "the data source for detector selection, histogram inspection, peak finding, and model fitting."
            ),
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

    def get_layout(self):
        """
        Build the scattering upload section layout.
        """
        return self.layout_builder.get_layout()

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