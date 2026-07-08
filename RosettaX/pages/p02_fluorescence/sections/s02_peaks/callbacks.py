# -*- coding: utf-8 -*-

import logging

from RosettaX.workflow.peak.callbacks.main import register_peak_callbacks


logger = logging.getLogger(__name__)


def register_callbacks(section) -> None:
    """
    Register fluorescence peak workflow callbacks.
    """
    register_peak_callbacks(
        page=section.page,
        ids=section.ids,
        adapter=section.adapter,
        config=section.config,
        logger=logger,
    )
