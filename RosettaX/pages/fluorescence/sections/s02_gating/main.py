# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils.runtime_config import RuntimeConfig
from . import services


logger = logging.getLogger(__name__)


class Gating:
    """
    Fluorescence calibration scattering gating section.

    Responsibilities
    ----------------
    - Select the scattering detector used for gating.
    - Estimate or manually set the scattering threshold.
    - Render the optional scattering histogram.
    - Store the current scattering threshold.
    """

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Scattering
        logger.debug("Initialized Gating section with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("2. Scattering channel")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_debug_store(),
                dash.html.Br(),
                self._build_detector_row(),
                dash.html.Br(),
                self._build_debug_switch_row(),
                dash.html.Br(),
                self._build_debug_controls_container(),
            ]
        )

    def _build_debug_store(self) -> dash.dcc.Store:
        return dash.dcc.Store(
            id=self.ids.debug_store,
            data={
                "enabled": False,
            },
        )

    def _build_detector_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Scattering detector:"),
                dash.dcc.Dropdown(
                    id=self.ids.detector_dropdown,
                    style={
                        "width": "500px",
                    },
                    optionHeight=50,
                    maxHeight=500,
                    searchable=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_switch_row(self) -> dash.html.Div:
        runtime_config = self._get_default_runtime_config()

        return dash.html.Div(
            [
                dbc.Checklist(
                    id=self.ids.debug_switch,
                    options=[
                        {
                            "label": "Show graph",
                            "value": "enabled",
                        }
                    ],
                    value=[
                        "enabled"
                    ]
                    if runtime_config.get_show_graphs(default=True)
                    else [],
                    switch=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def _build_debug_controls_container(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_estimate_and_threshold_row(),
                dash.html.Br(),
                self._build_histogram_graph(),
                dash.html.Br(),
                self._build_yscale_switch(),
                dash.html.Br(),
                self._build_nbins_row(),
            ],
            id=self.ids.debug_container,
            style={
                "display": "none",
            },
        )

    def _build_nbins_row(self) -> dash.html.Div:
        runtime_config = self._get_default_runtime_config()

        return dash.html.Div(
            [
                dash.html.Div("Number of bins:"),
                dash.dcc.Input(
                    id=self.ids.nbins_input,
                    type="number",
                    min=10,
                    step=10,
                    value=runtime_config.get_int(
                        "calibration.n_bins_for_plots",
                        default=100,
                    ),
                    style={
                        "width": "160px",
                    },
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style=styling.CARD,
        )

    def _build_estimate_and_threshold_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Estimate threshold",
                            id=self.ids.find_threshold_btn,
                            n_clicks=0,
                            style={
                                "display": "inline-block",
                            },
                        )
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
                dash.html.Div(
                    [
                        dash.html.Div(
                            "Threshold:",
                            style={
                                "marginRight": "8px",
                            },
                        ),
                        dash.dcc.Input(
                            id=self.ids.threshold_input,
                            type="text",
                            debounce=True,
                            value="",
                            disabled=False,
                            style={
                                "width": "220px",
                            },
                            persistence=True,
                            persistence_type="session",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginLeft": "16px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
            },
        )

    def _build_yscale_switch(self) -> dbc.Checklist:
        runtime_config = self._get_default_runtime_config()
        histogram_scale = runtime_config.get_str(
            "calibration.histogram_scale",
            default="log",
        )

        return dbc.Checklist(
            id=self.ids.yscale_switch,
            options=[
                {
                    "label": "Log scale (counts)",
                    "value": "log",
                }
            ],
            value=[
                "log"
            ]
            if histogram_scale == "log"
            else [],
            switch=True,
            persistence=True,
            persistence_type="session",
        )

    def _build_histogram_graph(self) -> dash.dcc.Loading:
        return dash.dcc.Loading(
            dash.dcc.Graph(
                id=self.ids.graph_hist,
                style=styling.PAGE["graph"],
            ),
            type="default",
        )

    def register_callbacks(self) -> None:
        """
        Register callbacks for the gating section.
        """
        logger.debug("Registering gating callbacks.")
        self._register_runtime_sync_callback()
        self._register_debug_visibility_callback()
        self._register_threshold_and_histogram_callback()

    def _register_runtime_sync_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.yscale_switch, "value"),
            dash.Output(self.ids.debug_switch, "value"),
            dash.Output(self.ids.nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_controls_from_runtime_store(
            runtime_config_data: Any,
        ) -> tuple[Any, Any, Any]:
            defaults = services.resolve_runtime_defaults(
                runtime_config_data,
            )

            logger.debug(
                "sync_controls_from_runtime_store resolved defaults=%r",
                defaults,
            )

            return (
                defaults.yscale_value,
                defaults.debug_switch_value,
                defaults.nbins_value,
            )

    def _register_debug_visibility_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.debug_container, "style"),
            dash.Input(self.ids.debug_switch, "value"),
            prevent_initial_call=False,
        )
        def toggle_scattering_debug(
            debug_switch_value: Any,
        ) -> dict[str, str]:
            return services.build_debug_container_style(
                debug_switch_value,
                logger=logger,
            )

    def _register_threshold_and_histogram_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_hist, "figure"),
            dash.Output(self.ids.threshold_store, "data"),
            dash.Output(self.ids.threshold_input, "value"),
            dash.Input(self.ids.find_threshold_btn, "n_clicks"),
            dash.Input(self.ids.threshold_input, "value"),
            dash.Input(self.ids.detector_dropdown, "value"),
            dash.Input(self.ids.nbins_input, "value"),
            dash.Input(self.ids.yscale_switch, "value"),
            dash.Input(self.ids.debug_switch, "value"),
            dash.State(
                self.ids.threshold_store,
                "data",
                allow_optional=True,
            ),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def update_scattering_threshold_and_histogram(
            n_clicks_estimate: int,
            threshold_input_value: Any,
            scattering_channel: Any,
            scattering_nbins: Any,
            yscale_selection: Any,
            debug_switch_value: Any,
            scattering_threshold_store_data: Any,
            max_events_for_plots: Any,
            runtime_config_data: Any,
        ) -> tuple:
            del n_clicks_estimate

            callback_inputs = services.parse_callback_inputs(
                threshold_input_value=threshold_input_value,
                scattering_channel=scattering_channel,
                scattering_nbins=scattering_nbins,
                yscale_selection=yscale_selection,
                debug_switch_value=debug_switch_value,
                scattering_threshold_store_data=scattering_threshold_store_data,
                max_events_for_plots=max_events_for_plots,
                runtime_config_data=runtime_config_data,
                find_threshold_button_id=self.ids.find_threshold_btn,
                detector_dropdown_id=self.ids.detector_dropdown,
                nbins_input_id=self.ids.nbins_input,
            )

            result = services.run_gating_callback(
                callback_inputs=callback_inputs,
                page_backend=self.page.backend,
                runtime_config_data=runtime_config_data,
                logger=logger,
            )

            return result.to_tuple()