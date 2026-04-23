# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils.plottings import _make_info_figure
from RosettaX.utils import styling
from . import services


logger = logging.getLogger(__name__)


class Calibration:
    bead_table_columns = [
        {"name": "Intensity [calibrated units]", "id": "col1", "editable": True},
        {"name": "Intensity [a.u.]", "id": "col2", "editable": True},
    ]

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized Calibration section with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        """
        Use the default profile only for initial layout construction.

        Live session state must come from runtime-config-store inside callbacks.
        """
        return RuntimeConfig.from_default_profile()

    def _get_default_mesf_values(self) -> Any:
        runtime_config = self._get_default_runtime_config()
        return runtime_config.get_path("calibration.mesf_values", default=[])

    def get_layout(self) -> dbc.Card:
        logger.debug("Building calibration section layout.")
        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("4. Calibration")

    def _build_collapse(self) -> dbc.Collapse:
        return dbc.Collapse(
            self._build_body(),
            id=f"collapse-{self.page.ids.page_name}-calibration",
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_graph_store(),
                self._build_bead_specifications_block(),
                dash.html.Br(),
                self._build_actions_block(),
                dash.html.Hr(),
                self._build_graph_block(),
                dash.html.Br(),
                self._build_fit_outputs_block(),
                dash.html.Br(),
                self._build_status_block(),
            ]
        )

    def _build_graph_store(self) -> dash.dcc.Store:
        return dash.dcc.Store(id=self.page.ids.Calibration.graph_store)

    def _build_bead_specifications_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Bead specifications"),
                self._build_bead_table(),
                self._build_add_row_button_row(),
            ]
        )

    def _build_bead_table(self) -> dash.dash_table.DataTable:
        default_mesf_values = self._get_default_mesf_values()
        bead_rows = services.build_bead_rows_from_mesf_values(default_mesf_values)

        logger.debug(
            "Building bead table with default_mesf_values=%r resulting rows=%r",
            default_mesf_values,
            bead_rows,
        )

        return dash.dash_table.DataTable(
            id=self.page.ids.Calibration.bead_table,
            columns=self.bead_table_columns,
            data=bead_rows,
            **styling.DATATABLE,
        )

    def _build_add_row_button_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Button(
                    "Add Row",
                    id=self.page.ids.Calibration.add_row_btn,
                    n_clicks=0,
                )
            ],
            style={"marginTop": "10px"},
        )

    def _build_actions_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Button(
                    "Create Calibration",
                    id=self.page.ids.Calibration.calibrate_btn,
                    n_clicks=0,
                ),
            ]
        )

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.dcc.Loading(
                            dash.dcc.Graph(
                                id=self.page.ids.Calibration.graph_calibration,
                                style=self.page.style["graph"],
                            ),
                            type="default",
                        ),
                    ],
                    id=self.page.ids.Calibration.graph_toggle_container,
                    style={"display": "block"},
                ),
            ]
        )

    def _build_fit_outputs_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_output_row("Slope:", self.page.ids.Calibration.slope_out),
                self._build_output_row("Intercept:", self.page.ids.Calibration.intercept_out),
                self._build_output_row("R²:", self.page.ids.Calibration.r_squared_out),
            ]
        )

    def _build_output_row(self, label: str, output_id: str) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(label),
                dash.html.Div("", id=output_id),
            ],
            style={"display": "flex", "gap": "8px"},
        )

    def _build_status_block(self) -> dash.html.Div:
        return dash.html.Div(
            id=self.page.ids.Calibration.apply_status,
            style={"marginTop": "8px"},
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering calibration callbacks.")

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_bead_table_from_runtime_store(runtime_config_data: Any) -> list[dict[str, str]]:
            resolved_rows = services.resolve_bead_rows_from_runtime_store(runtime_config_data)

            logger.debug(
                "sync_bead_table_from_runtime_store returning row_count=%r rows=%r",
                len(resolved_rows),
                resolved_rows,
            )
            return resolved_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_calibration, "figure"),
            dash.Input(self.page.ids.Calibration.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_calibration_graph(stored_figure: Any) -> go.Figure:
            logger.debug(
                "update_calibration_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )
            return services.rebuild_calibration_graph(
                stored_figure=stored_figure,
                empty_message="Create a calibration first.",
                failure_message="Failed to render calibration graph.",
                logger=logger,
            )

        @dash.callback(
            dash.Output(self.page.ids.Calibration.bead_table, "data", allow_duplicate=True),
            dash.Input(self.page.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(
            n_clicks: int,
            rows: list[dict[str, Any]],
            columns: list[dict[str, Any]],
        ) -> list[dict[str, str]]:
            logger.debug(
                "add_row called with n_clicks=%r existing_row_count=%r columns=%r",
                n_clicks,
                None if rows is None else len(rows),
                columns,
            )

            next_rows = services.add_empty_row(
                rows=rows,
                columns=columns,
            )

            logger.debug("add_row returning next_row_count=%r", len(next_rows))
            return next_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_store, "data"),
            dash.Output(self.page.ids.Calibration.calibration_store, "data"),
            dash.Output(self.page.ids.Calibration.slope_out, "children"),
            dash.Output(self.page.ids.Calibration.intercept_out, "children"),
            dash.Output(self.page.ids.Calibration.r_squared_out, "children"),
            dash.Output(self.page.ids.Calibration.apply_status, "children"),
            dash.Input(self.page.ids.Calibration.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown, "value"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Scattering.threshold_store, "data"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            bead_file_path: str | None,
            table_data: list[dict[str, Any]] | None,
            detector_column: str | None,
            scattering_detector_column: str | None,
            scattering_threshold: Any,
        ) -> tuple:
            logger.debug(
                "calibrate_and_apply called with n_clicks=%r bead_file_path=%r table_row_count=%r detector_column=%r",
                n_clicks,
                bead_file_path,
                None if table_data is None else len(table_data),
                detector_column,
            )
            del n_clicks

            result = services.run_calibration_workflow(
                bead_file_path=bead_file_path,
                table_data=table_data,
                detector_column=detector_column,
                scattering_detector_column=scattering_detector_column,
                scattering_threshold=scattering_threshold,
                logger=logger,
            )
            return result.to_tuple()