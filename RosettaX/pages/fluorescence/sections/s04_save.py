# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.save.adapters import CalibrationStoreSaveAdapter
from RosettaX.workflow.save.callbacks import register_save_callbacks
from RosettaX.workflow.save.layout import SaveLayout
from RosettaX.workflow.save.models import SaveConfig
from RosettaX.utils import directories


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

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Save

        self.config = SaveConfig(
            calibration_kind="fluorescence",
            output_directory=directories.fluorescence_calibration,
            header_title="5. Save calibration",
            button_text="Save calibration",
            file_name_placeholder="calibration name",
            saved_message_prefix="Saved calibration",
            failure_message="Failed to save calibration. See terminal logs for details.",
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

    def get_layout(self):
        """
        Create the fluorescence save section layout.
        """
        return self.layout_builder.get_layout()

    def register_callbacks(self) -> None:
        """
        Register callbacks for the fluorescence save section.
        """
        register_save_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
            calibration_store_id=self.page.ids.Calibration.calibration_store,
            page_state_store_id=None,
        )