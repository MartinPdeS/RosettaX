# -*- coding: utf-8 -*-

import logging

from RosettaX.pages.p03_scattering.state import ScatteringPageState
from RosettaX.workflow import save
from RosettaX.utils import directories


logger = logging.getLogger(__name__)


class Save:
    """
    Scattering calibration save section.

    Responsibilities
    ----------------
    - Provide the scattering save layout.
    - Register the reusable save workflow callbacks.

    Notes
    -----
    The scattering calibration payload is read from the scattering page state
    store. Saving, validation, file creation, and sidebar refresh signaling are
    delegated to RosettaX.workflow.save.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Save

        self.config = save.SaveConfig(
            calibration_kind="scattering",
            output_directory=directories.scattering_calibration,
            header_title="6. Save calibration",
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

    def get_layout(self):
        """
        Create the scattering save section layout.
        """
        return self.layout_builder.get_layout()

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