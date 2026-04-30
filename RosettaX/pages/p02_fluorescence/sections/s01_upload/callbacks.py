# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow import upload


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register callbacks for the fluorescence upload section.
    """
    upload.register_upload_callbacks(
        page=section.page,
        ids=section.ids,
        adapter=section.adapter,
        config=section.config,
        logger=logger,
    )
