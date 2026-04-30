# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms
from RosettaX.workflow import peak

from . import layout as _layout
from . import callbacks as _callbacks


logger = logging.getLogger(__name__)


class Peaks:
    """
    Fluorescence peak detection section.

    Responsibilities
    ----------------
    - Provide the fluorescence peak workflow layout.
    - Register the reusable peak workflow callbacks.
    - Write detected peak positions into the fluorescence reference table owned
      by the dedicated table section.

    Notes
    -----
    This section does not render the calibration table. The table is rendered by
    the dedicated fluorescence table section, but the reusable peak workflow
    still receives its component ID so it can write detected peak positions into
    it.
    """

    def __init__(
        self,
        page: Any,
        section_number: int,
        card_color: str = "pink",
    ) -> None:
        self.page = page
        self.ids = page.ids.Fluorescence
        self.section_number = section_number
        self.card_color = card_color
        self.adapter = peak.FluorescencePeakWorkflowAdapter()

        self.section_tooltip_target_id = f"{self.ids.process_dropdown}-section-info-target"
        self.section_tooltip_id = f"{self.ids.process_dropdown}-section-info-tooltip"

        self.graph_tooltip_target_id = f"{self.ids.process_dropdown}-graph-info-target"
        self.graph_tooltip_id = f"{self.ids.process_dropdown}-graph-info-tooltip"

        self.config = peak.PeakConfig(
            header_title=_layout.build_section_title(self),
            process_dropdown_label="Peak process",
            graph_title=_layout.build_graph_title(self),
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=_get_max_events_input_id(self),
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=None,
            default_process_runtime_config_path="calibration.default_fluorescence_peak_process",
        )

        self.layout_builder = peak.PeakLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Fluorescence Peaks section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence peak section layout.
        """
        return _layout.get_layout(self)

    def register_callbacks(self) -> None:
        """
        Register fluorescence peak workflow callbacks.
        """
        _callbacks.register_callbacks(self)


def _get_max_events_input_id(section) -> Any:
    """
    Return the optional max events input ID.
    """
    upload_ids = getattr(
        section.page.ids,
        "Upload",
        None,
    )

    if upload_ids is None:
        return None

    return getattr(
        upload_ids,
        "max_events_for_plots_input",
        None,
    )
