# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash_bootstrap_components as dbc

from RosettaX.peak_workflow.adapters import FluorescencePeakWorkflowAdapter
from RosettaX.peak_workflow.callbacks import PeakWorkflowCallbacks
from RosettaX.peak_workflow.callbacks import get_peak_processes
from RosettaX.peak_workflow.layouts import build_peak_workflow_layout
from RosettaX.utils.runtime_config import RuntimeConfig


logger = logging.getLogger(__name__)


class Peaks:
    """
    Render and manage fluorescence peak detection.

    This section delegates the generic peak workflow to
    RosettaX.peak_workflow. Fluorescence specific behavior is implemented in
    FluorescencePeakWorkflowAdapter.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Fluorescence
        self.adapter = FluorescencePeakWorkflowAdapter()

        logger.debug(
            "Initialized Fluorescence Peaks section with page=%r",
            page,
        )

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Return the default runtime config used for initial layout values.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_n_bins_for_plots(self) -> int:
        """
        Return the default number of histogram bins.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        )

    def _get_default_xscale(self) -> str:
        """
        Return the default x axis scale.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            "calibration.histogram_xscale",
            default=runtime_config.get_str(
                "calibration.xscale",
                default="linear",
            ),
        )

    def _get_default_yscale(self) -> str:
        """
        Return the default y axis scale.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            "calibration.histogram_yscale",
            default=runtime_config.get_str(
                "calibration.histogram_scale",
                default="log",
            ),
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence peak section layout.
        """
        logger.debug("Building Fluorescence Peaks layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the card header.
        """
        return dbc.CardHeader(
            "3. Fluorescence peak detection",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the card body.
        """
        return dbc.CardBody(
            build_peak_workflow_layout(
                ids=self.ids,
                processes=get_peak_processes(),
                process_dropdown_label="Peak process",
                graph_title="Fluorescence peak detection graph",
                number_of_bins=self._get_default_n_bins_for_plots(),
                xscale=self._get_default_xscale(),
                yscale=self._get_default_yscale(),
            )
        )

    def register_callbacks(self) -> None:
        """
        Register fluorescence peak workflow callbacks.
        """
        logger.debug(
            "Registering Fluorescence Peaks callbacks through shared workflow."
        )

        PeakWorkflowCallbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self._get_max_events_input_id(),
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=None,
        ).register()

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