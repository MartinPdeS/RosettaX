# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc

from . import layout as _layout
from . import callbacks as _callbacks


logger = logging.getLogger(__name__)


class Calibration:
    """
    Fluorescence calibration section.

    Responsibilities
    ----------------
    - Render the fluorescence calibration action controls.
    - Resolve the active fluorescence detector from the selected peak script.
    - Fit the fluorescence calibration from the dedicated reference table.
    - Display the calibration graph and fit coefficients.
    - Store the calibration payload for the save section.

    Table ownership
    ---------------
    This section does not render or mutate the bead table. The bead table is
    owned by the dedicated reference table section. This section only reads
    ``self.ids.bead_table`` during calibration.
    """

    graph_min_width_px = 760

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "pink",
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration
        self.section_number = section_number
        self.card_color = card_color

        self.section_tooltip_target_id = f"{self.ids.calibrate_btn}-section-info-target"
        self.section_tooltip_id = f"{self.ids.calibrate_btn}-section-info-tooltip"

        self.create_calibration_tooltip_target_id = f"{self.ids.calibrate_btn}-create-calibration-info-target"
        self.create_calibration_tooltip_id = f"{self.ids.calibrate_btn}-create-calibration-info-tooltip"

        self.graph_tooltip_target_id = f"{self.ids.graph_calibration}-info-target"
        self.graph_tooltip_id = f"{self.ids.graph_calibration}-info-tooltip"

        logger.debug(
            "Initialized Calibration section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the calibration section layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Register calibration callbacks.
        """
        _callbacks.register_callbacks(self)
