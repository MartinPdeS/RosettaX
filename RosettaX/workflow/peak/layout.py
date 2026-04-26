# -*- coding: utf-8 -*-

import logging
from typing import Any

import dash
import dash_bootstrap_components as dbc

from RosettaX.workflow.peak_workflow.callbacks import get_peak_processes
from RosettaX.workflow.peak_workflow.layouts import build_peak_workflow_layout
from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.workflow.peak_workflow.models import PeakConfig


logger = logging.getLogger(__name__)


class PeakLayout:
    """
    Reusable layout builder for fluorescence and scattering peak sections.

    This class wraps the existing generic peak workflow layout in a page section
    card and ensures the required stores/status components exist.
    """

    def __init__(
        self,
        *,
        ids: Any,
        config: PeakConfig,
    ) -> None:
        self.ids = ids
        self.config = config

    def get_layout(self) -> dbc.Card:
        """
        Build the peak section layout.
        """
        logger.debug(
            "Building peak layout with header_title=%r",
            self.config.header_title,
        )

        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            self.config.header_title,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        workflow_layout = build_peak_workflow_layout(
            ids=self.ids,
            processes=get_peak_processes(),
            process_dropdown_label=self.config.process_dropdown_label,
            graph_title=self.config.graph_title,
            number_of_bins=self._get_default_number_of_bins(),
            xscale=self._get_default_xscale(),
            yscale=self._get_default_yscale(),
        )

        workflow_children = self._normalize_children(
            workflow_layout,
        )

        return dbc.CardBody(
            [
                *self._build_state_stores(),
                *workflow_children,
                self._build_script_status(),
            ]
        )

    def _build_state_stores(self) -> list[dash.dcc.Store]:
        """
        Build the stores required by the peak workflow callbacks.
        """
        return [
            dash.dcc.Store(
                id=self.ids.peak_lines_store,
                storage_type="session",
            ),
            dash.dcc.Store(
                id=self.ids.hist_store,
                storage_type="session",
            ),
            dash.dcc.Store(
                id=self.ids.source_channel_store,
                storage_type="session",
            ),
        ]

    def _build_script_status(self) -> dash.html.Div:
        """
        Build the shared peak script status output.
        """
        return dash.html.Div(
            id=self.ids.script_status,
            style={
                "marginTop": "8px",
            },
        )

    def _normalize_children(
        self,
        children: Any,
    ) -> list[Any]:
        """
        Normalize layout output into a flat list of Dash children.
        """
        if children is None:
            return []

        if isinstance(children, tuple):
            normalized_children: list[Any] = []

            for child in children:
                normalized_children.extend(
                    self._normalize_children(
                        child,
                    )
                )

            return normalized_children

        if isinstance(children, list):
            normalized_children = []

            for child in children:
                normalized_children.extend(
                    self._normalize_children(
                        child,
                    )
                )

            return normalized_children

        return [
            children,
        ]

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Return the default runtime configuration.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_number_of_bins(self) -> int:
        """
        Return the default number of histogram bins.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_int(
            self.config.number_of_bins_runtime_config_path,
            default=self.config.default_number_of_bins,
        )

    def _get_default_xscale(self) -> str:
        """
        Return the default x axis scale.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            self.config.xscale_runtime_config_path,
            default=runtime_config.get_str(
                self.config.xscale_fallback_runtime_config_path,
                default=self.config.default_xscale,
            ),
        )

    def _get_default_yscale(self) -> str:
        """
        Return the default y axis scale.
        """
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_str(
            self.config.yscale_runtime_config_path,
            default=runtime_config.get_str(
                self.config.yscale_fallback_runtime_config_path,
                default=self.config.default_yscale,
            ),
        )