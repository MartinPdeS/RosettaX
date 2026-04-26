# -*- coding: utf-8 -*-

from typing import Any
import logging

from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter
from RosettaX.workflow import peak

logger = logging.getLogger(__name__)


class Peaks:
    """
    Scattering peak detection section.

    Responsibilities
    ----------------
    - Provide the scattering peak workflow layout.
    - Register the reusable peak workflow callbacks.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Scattering
        self.adapter = ScatteringPeakWorkflowAdapter()

        self.config = peak.models.PeakConfig(
            header_title="2. Scattering peak detection",
            process_dropdown_label="Peak process",
            graph_title="Scattering peak detection graph",
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self._get_max_events_input_id(),
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=self.page.ids.Parameters.mie_model,
        )

        self.layout_builder = peak.layout.PeakLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Scattering Peaks section with page=%r",
            page,
        )

    def get_layout(self):
        """
        Build the scattering peak section layout.
        """
        return self.layout_builder.get_layout()

    def register_callbacks(self) -> None:
        """
        Register scattering peak workflow callbacks.
        """
        peak.callbacks.main.register_peak_callbacks(
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