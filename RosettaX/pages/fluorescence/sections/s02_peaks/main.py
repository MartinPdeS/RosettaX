# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.peak_script.registry import DEFAULT_PROCESS_NAME
from RosettaX.peak_script.registry import get_peak_process_instances
from RosettaX.peak_workflow.callbacks import PeakWorkflowCallbacks
from RosettaX.peak_workflow import layout as peak_layout
from RosettaX.utils.runtime_config import RuntimeConfig

from .adapters import FluorescencePeakWorkflowAdapter


logger = logging.getLogger(__name__)


class Peaks:
    """
    Render and manage fluorescence peak detection.

    This section delegates the generic peak workflow to
    RosettaX.peak_workflow. Fluorescence specific behavior is implemented in
    FluorescencePeakWorkflowAdapter.
    """

    def __init__(self, page) -> None:
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

        Returns
        -------
        RuntimeConfig
            Default runtime config.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_peak_process(self) -> str:
        """
        Return the preferred fluorescence peak process from the default profile.

        Returns
        -------
        str
            Peak process name.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            "calibration.default_fluorescence_peak_process",
            default=DEFAULT_PROCESS_NAME,
        )

    def _get_default_show_graphs(self) -> bool:
        """
        Return whether graphs should be shown by default.

        Returns
        -------
        bool
            True if graphs should be shown.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_show_graphs(
            default=True,
        )

    def _get_default_n_bins_for_plots(self) -> int:
        """
        Return the default number of histogram bins.

        Returns
        -------
        int
            Number of bins.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_int(
            "calibration.n_bins_for_plots",
            default=100,
        )

    def _get_default_histogram_scale(self) -> str:
        """
        Return the default histogram scale.

        Returns
        -------
        str
            Histogram scale.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            "calibration.histogram_scale",
            default="log",
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the fluorescence peak section layout.

        Returns
        -------
        dbc.Card
            Section layout.
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

        Returns
        -------
        dbc.CardHeader
            Header.
        """
        return dbc.CardHeader(
            "3. Fluorescence peak detection",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the card body.

        Returns
        -------
        dbc.CardBody
            Body.
        """
        return dbc.CardBody(
            [
                peak_layout.build_process_selector(
                    ids=self.ids,
                    default_process_name=self._get_default_peak_process(),
                ),
                dash.html.Br(),
                peak_layout.build_process_controls(
                    ids=self.ids,
                    processes=get_peak_process_instances(),
                ),
                dash.html.Br(),
                peak_layout.build_graph_toggle_switch(
                    ids=self.ids,
                    show_graphs=self._get_default_show_graphs(),
                ),
                dash.html.Br(),
                peak_layout.build_graph_controls_container(
                    ids=self.ids,
                    histogram_scale=self._get_default_histogram_scale(),
                    nbins=self._get_default_n_bins_for_plots(),
                ),
            ]
        )

    def register_callbacks(self) -> None:
        """
        Register fluorescence peak workflow callbacks.
        """
        logger.debug("Registering Fluorescence Peaks callbacks through shared workflow.")

        PeakWorkflowCallbacks(
            page=self.page,
            ids=self.ids,
            adapter=self.adapter,
            table_id=self.page.ids.Calibration.bead_table,
            page_state_store_id=self.page.ids.State.page_state_store,
            max_events_input_id=self.page.ids.Upload.max_events_for_plots_input,
            runtime_config_store_id="runtime-config-store",
            mie_model_input_id=None,
        ).register()