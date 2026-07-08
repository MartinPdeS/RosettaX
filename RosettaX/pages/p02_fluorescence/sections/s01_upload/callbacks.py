# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.upload.callbacks import register_upload_callbacks


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register callbacks for the fluorescence upload section.
    """
    register_upload_callbacks(
        page=section.page,
        ids=section.ids,
        adapter=section.adapter,
        config=section.config,
        logger=logger,
    )
