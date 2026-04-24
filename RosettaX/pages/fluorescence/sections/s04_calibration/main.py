# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils.runtime_config import RuntimeConfig
from RosettaX.utils import styling
from . import services


logger = logging.getLogger(__name__)


class Calibration:
    """
    Fluorescence calibration section.

    Responsibilities
    ----------------
    - Render the bead calibration table.
    - Fit the fluorescence calibration from bead specifications.
    - Resolve the active fluorescence detector from the selected peak script.
    - Display the calibration graph and fit coefficients.
    - Store the calibration payload for the save section.
    """

    bead_table_columns = [
        {
            "name": "Intensity [calibrated units]",
            "id": "col1",
            "editable": True,
        },
        {
            "name": "Intensity [a.u.]",
            "id": "col2",
            "editable": True,
        },
    ]

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        logger.debug("Initialized Calibration section with page=%r", page)

    def _get_default_runtime_config(self) -> RuntimeConfig:
        return RuntimeConfig.from_default_profile()

    def _get_default_mesf_values(self) -> Any:
        runtime_config = self._get_default_runtime_config()

        return runtime_config.get_path(
            "calibration.mesf_values",
            default=[],
        )

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
            id=self.ids.collapse,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_graph_store(),
                self._build_calibration_store(),
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
        return dash.dcc.Store(
            id=self.ids.graph_store,
            storage_type="session",
        )

    def _build_calibration_store(self) -> dash.dcc.Store:
        return dash.dcc.Store(
            id=self.ids.calibration_store,
            storage_type="session",
        )

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
        bead_rows = services.build_bead_rows_from_mesf_values(
            default_mesf_values,
        )

        logger.debug(
            "Building bead table with default_mesf_values=%r resulting rows=%r",
            default_mesf_values,
            bead_rows,
        )

        return dash.dash_table.DataTable(
            id=self.ids.bead_table,
            columns=self.bead_table_columns,
            data=bead_rows,
            **styling.DATATABLE,
        )

    def _build_add_row_button_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Button(
                    "Add Row",
                    id=self.ids.add_row_btn,
                    n_clicks=0,
                )
            ],
            style={
                "marginTop": "10px",
            },
        )

    def _build_actions_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Button(
                    "Create Calibration",
                    id=self.ids.calibrate_btn,
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
                                id=self.ids.graph_calibration,
                                style=styling.PAGE["graph"],
                            ),
                            type="default",
                        ),
                    ],
                    id=self.ids.graph_toggle_container,
                    style={
                        "display": "block",
                    },
                ),
            ]
        )

    def _build_fit_outputs_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                self._build_output_row(
                    "Slope:",
                    self.ids.slope_out,
                ),
                self._build_output_row(
                    "Intercept:",
                    self.ids.intercept_out,
                ),
                self._build_output_row(
                    "R²:",
                    self.ids.r_squared_out,
                ),
            ]
        )

    def _build_output_row(
        self,
        label: str,
        output_id: str,
    ) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(label),
                dash.html.Div(
                    "",
                    id=output_id,
                ),
            ],
            style={
                "display": "flex",
                "gap": "8px",
            },
        )

    def _build_status_block(self) -> dash.html.Div:
        return dash.html.Div(
            id=self.ids.apply_status,
            style={
                "marginTop": "8px",
            },
        )

    def _resolve_active_fluorescence_channel(
        self,
        *,
        selected_process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
    ) -> Optional[str]:
        selected_process_name_clean = (
            ""
            if selected_process_name is None
            else str(selected_process_name)
        )

        channel_values: dict[str, str] = {}

        for dropdown_id, dropdown_value in zip(
            detector_dropdown_ids or [],
            detector_dropdown_values or [],
            strict=False,
        ):
            if not isinstance(dropdown_id, dict):
                continue

            if dropdown_id.get("process") != selected_process_name_clean:
                continue

            channel_name = dropdown_id.get("channel")
            channel_value = "" if dropdown_value is None else str(dropdown_value).strip()

            if not channel_name:
                continue

            if not channel_value or channel_value.lower() == "none":
                continue

            channel_values[str(channel_name)] = channel_value

        if "primary" in channel_values:
            return channel_values["primary"]

        if "x" in channel_values:
            return channel_values["x"]

        return next(
            iter(channel_values.values()),
            None,
        )

    def register_callbacks(self) -> None:
        logger.debug("Registering calibration callbacks.")

        self._register_runtime_table_sync_callback()
        self._register_graph_render_callback()
        self._register_add_row_callback()
        self._register_calibration_workflow_callback()

    def _register_runtime_table_sync_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.bead_table, "data"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_bead_table_from_runtime_store(
            runtime_config_data: Any,
        ) -> list[dict[str, str]]:
            resolved_rows = services.resolve_bead_rows_from_runtime_store(
                runtime_config_data,
            )

            logger.debug(
                "sync_bead_table_from_runtime_store returning row_count=%r rows=%r",
                len(resolved_rows),
                resolved_rows,
            )

            return resolved_rows

    def _register_graph_render_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_calibration, "figure"),
            dash.Input(self.ids.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_calibration_graph(
            stored_figure: Any,
        ) -> go.Figure:
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

    def _register_add_row_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.ids.add_row_btn, "n_clicks"),
            dash.State(self.ids.bead_table, "data"),
            dash.State(self.ids.bead_table, "columns"),
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

            logger.debug(
                "add_row returning next_row_count=%r",
                len(next_rows),
            )

            return next_rows

    def _register_calibration_workflow_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_store, "data"),
            dash.Output(self.ids.calibration_store, "data"),
            dash.Output(self.ids.slope_out, "children"),
            dash.Output(self.ids.intercept_out, "children"),
            dash.Output(self.ids.r_squared_out, "children"),
            dash.Output(self.ids.apply_status, "children"),
            dash.Input(self.ids.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.uploaded_fcs_path_store, "data"),
            dash.State(self.ids.bead_table, "data"),
            dash.State(self.page.ids.Fluorescence.process_dropdown, "value"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown_pattern(), "id"),
            dash.State(self.page.ids.Fluorescence.detector_dropdown_pattern(), "value"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            bead_file_path: str | None,
            table_data: list[dict[str, Any]] | None,
            selected_fluorescence_process_name: Any,
            fluorescence_detector_dropdown_ids: list[dict[str, Any]],
            fluorescence_detector_dropdown_values: list[Any],
        ) -> tuple:
            detector_column = self._resolve_active_fluorescence_channel(
                selected_process_name=selected_fluorescence_process_name,
                detector_dropdown_ids=fluorescence_detector_dropdown_ids,
                detector_dropdown_values=fluorescence_detector_dropdown_values,
            )

            logger.debug(
                "calibrate_and_apply called with n_clicks=%r bead_file_path=%r "
                "table_row_count=%r selected_fluorescence_process_name=%r "
                "detector_column=%r",
                n_clicks,
                bead_file_path,
                None if table_data is None else len(table_data),
                selected_fluorescence_process_name,
                detector_column,
            )

            del n_clicks

            result = services.run_calibration_workflow(
                bead_file_path=bead_file_path,
                table_data=table_data,
                detector_column=detector_column,
                scattering_detector_column=None,
                scattering_threshold=None,
                logger=logger,
            )

            return result.to_tuple()