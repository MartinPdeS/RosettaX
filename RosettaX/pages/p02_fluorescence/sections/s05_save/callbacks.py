# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.save.callbacks import register_save_callbacks


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register callbacks for the fluorescence save section.
    """
    register_save_callbacks(
        page=section.page,
        ids=section.ids,
        adapter=section.adapter,
        config=section.config,
        logger=logger,
        calibration_store_id=section.page.ids.Calibration.calibration_store,
        page_state_store_id=None,
    )
