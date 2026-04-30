# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import ui_forms
from RosettaX.workflow import peak


logger = logging.getLogger(__name__)


class Peaks:
    """
    Scattering peak detection section.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Scattering
        self.adapter = peak.ScatteringPeakWorkflowAdapter()

        self.section_tooltip_target_id = f"{self.ids.process_dropdown}-section-info-target"
        self.section_tooltip_id = f"{self.ids.process_dropdown}-section-info-tooltip"

        self.graph_tooltip_target_id = f"{self.ids.process_dropdown}-graph-info-target"
        self.graph_tooltip_id = f"{self.ids.process_dropdown}-graph-info-tooltip"

        self.config = peak.PeakConfig(
            header_title=self._build_section_title(),
            process_dropdown_label="Peak process",
            graph_title=self._build_graph_title(),
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self._get_max_events_input_id(),
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=self.page.ids.Parameters.mie_model,
            default_process_runtime_config_path="scattering_calibration.default_peak_process",
        )

        self.layout_builder = peak.PeakLayout(
            ids=self.ids,
            config=self.config,
        )

        logger.debug(
            "Initialized Scattering Peaks section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering peak section layout.
        """
        return ui_forms.apply_workflow_section_card_style(
            card=self.layout_builder.get_layout(),
        )

    def _build_section_title(self) -> dash.html.Div:
        """
        Build the section title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title="2. Scattering peak detection",
            tooltip_target_id=self.section_tooltip_target_id,
            tooltip_id=self.section_tooltip_id,
            tooltip_text=(
                "Use this section to detect bead population peaks in the scattering "
                "reference FCS file. The selected peak positions are passed to the "
                "calibration standard table and used later to fit the instrument response."
            ),
        )

    def _build_graph_title(self) -> dash.html.Div:
        """
        Build the graph title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title="Scattering peak detection graph",
            tooltip_target_id=self.graph_tooltip_target_id,
            tooltip_id=self.graph_tooltip_id,
            tooltip_text=(
                "This graph previews the selected scattering signal and overlays the "
                "detected or manually selected peak positions. Use it to verify that "
                "the retained peaks correspond to the expected bead populations."
            ),
        )

    def register_callbacks(self) -> None:
        """
        Register scattering peak workflow callbacks.
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