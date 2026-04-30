# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
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
            header_title=self._build_section_title(),
            process_dropdown_label="Peak process",
            graph_title=self._build_graph_title(),
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self._get_max_events_input_id(),
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
        card = self.layout_builder.get_layout()

        section_style = styling.build_workflow_section_legacy_style(
            self.card_color,
        )

        return ui_forms.apply_workflow_section_card_style(
            card=card,
            header_background=section_style["header_background"],
            header_border=section_style["header_border"],
            left_border=section_style["left_border"],
            header_font_weight="750",
            header_font_size="1.02rem",
        )

    def _build_section_title(self) -> dash.html.Div:
        """
        Build the section title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title=f"{self.section_number}. Fluorescence peak detection",
            tooltip_target_id=self.section_tooltip_target_id,
            tooltip_id=self.section_tooltip_id,
            tooltip_text=(
                "Use this section to detect fluorescence bead population peaks "
                "from the calibration FCS file. These measured peak positions are "
                "written into the fluorescence calibration table and paired with "
                "the known MESF values."
            ),
        )

    def _build_graph_title(self) -> dash.html.Div:
        """
        Build the graph title with compact hover help.
        """
        return ui_forms.build_title_with_info(
            title=f"{self.section_number}. Fluorescence peak detection graph",
            tooltip_target_id=self.graph_tooltip_target_id,
            tooltip_id=self.graph_tooltip_id,
            tooltip_text=(
                "This graph previews the selected fluorescence signal and overlays "
                "the detected or manually selected peak positions. Use it to verify "
                "that the retained peaks correspond to the expected calibration bead "
                "populations."
            ),
        )

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