# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from ..state import FluorescencePageState
from RosettaX.utils import styling
from RosettaX.workflow.calibration import fluorescence as services


logger = logging.getLogger(__name__)


class Calibration:
    """
    Fluorescence calibration section.

    Responsibilities
    ----------------
    - Render the fluorescence calibration action controls.
    - Resolve the active fluorescence detector from the selected peak script.
    - Fit the fluorescence calibration from the dedicated reference table.
    - Display the calibration graph and fit coefficients.
    - Store the calibration payload for the save section.

    Table ownership
    ---------------
    This section does not render or mutate the bead table. The bead table is
    owned by the dedicated reference table section. This section only reads
    ``self.ids.bead_table`` during calibration.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        logger.debug(
            "Initialized Calibration section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the calibration section layout.
        """
        logger.debug("Building calibration section layout.")

        return dbc.Card(
            [
                self._build_header(),
                self._build_collapse(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        """
        Compatibility alias for older section loading code.
        """
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the card header.
        """
        return dbc.CardHeader(
            "5. Calibration",
        )

    def _build_collapse(self) -> dbc.Collapse:
        """
        Build the collapsible section body.
        """
        return dbc.Collapse(
            self._build_body(),
            id=self.ids.collapse,
            is_open=True,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the card body.
        """
        return dbc.CardBody(
            [
                self._build_graph_store(),
                self._build_calibration_store(),
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
        """
        Build the graph store.
        """
        return dash.dcc.Store(
            id=self.ids.graph_store,
            storage_type="session",
        )

    def _build_calibration_store(self) -> dash.dcc.Store:
        """
        Build the calibration store.
        """
        return dash.dcc.Store(
            id=self.ids.calibration_store,
            storage_type="session",
        )

    def _build_actions_block(self) -> dash.html.Div:
        """
        Build calibration action controls.
        """
        return dash.html.Div(
            [
                dash.html.Button(
                    "Create Calibration",
                    id=self.ids.calibrate_btn,
                    n_clicks=0,
                ),
                dash.html.Div(
                    (
                        "This step reads the MESF values and measured peak "
                        "positions from the calibration reference table."
                    ),
                    style={
                        "marginTop": "8px",
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_graph_block(self) -> dash.html.Div:
        """
        Build calibration graph block.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.dcc.Loading(
                            dash.dcc.Graph(
                                id=self.ids.graph_calibration,
                                style=styling.PLOTLY_GRAPH_STYLE,
                                config=styling.PLOTLY_GRAPH_CONFIG,
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
        """
        Build fit output display block.
        """
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
        """
        Build one fit output row.
        """
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
        """
        Build the status output.
        """
        return dash.html.Div(
            id=self.ids.apply_status,
            style={
                "marginTop": "8px",
            },
        )

    def _get_fluorescence_detector_dropdown_pattern(self) -> Any:
        """
        Return the pattern matching ID for fluorescence detector dropdowns.

        This supports both the newer reusable peak workflow naming and older
        aliases if they still exist in the page IDs.
        """
        fluorescence_ids = self.page.ids.Fluorescence

        if hasattr(
            fluorescence_ids,
            "process_detector_dropdown_pattern",
        ):
            return fluorescence_ids.process_detector_dropdown_pattern()

        if hasattr(
            fluorescence_ids,
            "detector_dropdown_pattern",
        ):
            return fluorescence_ids.detector_dropdown_pattern()

        raise AttributeError(
            "Fluorescence IDs must expose process_detector_dropdown_pattern() "
            "or detector_dropdown_pattern()."
        )

    def _resolve_active_fluorescence_channel(
        self,
        *,
        selected_process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
    ) -> Optional[str]:
        """
        Resolve the active fluorescence detector channel.

        Resolution order
        ----------------
        - primary, for 1D processes.
        - x_axis, for 2D processes using the newer generic axis naming.
        - x, for older 2D processes.
        - first available channel value.
        """
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

        logger.debug(
            "Resolved fluorescence channel_values=%r for selected_process_name=%r",
            channel_values,
            selected_process_name_clean,
        )

        if "primary" in channel_values:
            return channel_values["primary"]

        if "x_axis" in channel_values:
            return channel_values["x_axis"]

        if "x" in channel_values:
            return channel_values["x"]

        return next(
            iter(channel_values.values()),
            None,
        )

    def register_callbacks(self) -> None:
        """
        Register calibration callbacks.
        """
        logger.debug("Registering calibration callbacks.")

        self._register_graph_render_callback()
        self._register_calibration_workflow_callback()

    def _register_graph_render_callback(self) -> None:
        """
        Register the graph rendering callback.
        """

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

    def _register_calibration_workflow_callback(self) -> None:
        """
        Register the calibration workflow callback.
        """

        @dash.callback(
            dash.Output(self.ids.graph_store, "data"),
            dash.Output(self.ids.calibration_store, "data"),
            dash.Output(self.ids.slope_out, "children"),
            dash.Output(self.ids.intercept_out, "children"),
            dash.Output(self.ids.r_squared_out, "children"),
            dash.Output(self.ids.apply_status, "children"),
            dash.Input(self.ids.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.State.page_state_store, "data"),
            dash.State(self.ids.bead_table, "data"),
            dash.State(self.page.ids.Fluorescence.process_dropdown, "value"),
            dash.State(self._get_fluorescence_detector_dropdown_pattern(), "id"),
            dash.State(self._get_fluorescence_detector_dropdown_pattern(), "value"),
            prevent_initial_call=True,
        )
        def calibrate_and_apply(
            n_clicks: int,
            page_state_payload: Any,
            table_data: list[dict[str, Any]] | None,
            selected_fluorescence_process_name: Any,
            fluorescence_detector_dropdown_ids: list[dict[str, Any]],
            fluorescence_detector_dropdown_values: list[Any],
        ) -> tuple:
            page_state = FluorescencePageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            bead_file_path = page_state.uploaded_fcs_path

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