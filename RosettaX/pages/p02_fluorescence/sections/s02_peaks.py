# -*- coding: utf-8 -*-

from typing import Any
import logging

from RosettaX.workflow import peak

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
    ) -> None:
        self.page = page
        self.ids = page.ids.Fluorescence
        self.adapter = peak.FluorescencePeakWorkflowAdapter()

        self.config = peak.PeakConfig(
            header_title="3. Fluorescence peak detection",
            process_dropdown_label="Peak process",
            graph_title="Fluorescence peak detection graph",
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self._get_max_events_input_id(),
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=None,
        )

        self.layout_builder = peak.PeakLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Fluorescence Peaks section with page=%r",
            page,
        )

    def get_layout(self):
        """
        Build the fluorescence peak section layout.
        """
        return self.layout_builder.get_layout()

    def register_callbacks(self) -> None:
        """
        Register fluorescence peak workflow callbacks.
        """
        peak.register_peak_callbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            config=self.config,
            logger=logger,
        )

    def _get_max_events_input_id(self) -> Any:
        """
        Return the optional max events input ID.
        """
        upload_ids = getattr(
            self.page.ids,
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