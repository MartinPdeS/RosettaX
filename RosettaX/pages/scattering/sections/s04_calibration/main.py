# -*- coding: utf-8 -*-

from typing import Any
import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.utils.plottings import _make_info_figure
from . import services

logger = logging.getLogger(__name__)


class Calibration:
    """
    Scattering calibration section.

    Responsibilities
    ----------------
    - Render the calibration action area.
    - Display the two calibration graphs.
    - Delegate the calibration workflow to the service layer.

    Workflow
    --------
    1. Compute Expected Coupling in the previous section.
    2. Click Fit Calibration here to generate the graphs and calibration payload.
    """

    simulated_curve_point_count = 200
    graph_height_px = 420
    graph_min_width_px = 0

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized CalibrationSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("4. Fit calibration"),
                dbc.CardBody(
                    [
                        dash.dcc.Store(
                            id=self.page.ids.Calibration.graph_store,
                            storage_type="session",
                        ),
                        dash.dcc.Store(
                            id=f"{self.page.ids.Calibration.graph_store}-model",
                            storage_type="session",
                        ),
                        dash.dcc.Store(
                            id=self.page.ids.Calibration.calibration_store,
                            storage_type="session",
                        ),
                        self._build_action_block(),
                        dash.html.Br(),
                        self._build_graph_block(),
                        dash.html.Br(),
                        self._build_fit_outputs_block(),
                        dash.html.Br(),
                        dash.html.Div(
                            id=self.page.ids.Calibration.apply_status,
                            style={"marginTop": "8px"},
                        ),
                    ]
                ),
            ]
        )

    def _graph_style(self) -> dict[str, Any]:
        return {
            **dict(self.page.style["graph"]),
            "height": f"{self.graph_height_px}px",
            "width": "100%",
        }

    def _graph_wrapper_style(self) -> dict[str, Any]:
        return {
            "flex": "1",
            "minWidth": f"{self.graph_min_width_px}px",
            "height": f"{self.graph_height_px}px",
        }

    def _build_action_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Button(
                    "Fit Calibration",
                    id=self.page.ids.Calibration.calibrate_btn,
                    n_clicks=0,
                ),
                dash.html.Div(
                    "This step uses the measured peak positions and expected coupling values currently present in the table.",
                    style={"marginTop": "8px", "opacity": 0.75},
                ),
            ]
        )

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=self.page.ids.Calibration.graph_calibration,
                            style=self._graph_style(),
                            config={"responsive": True},
                        ),
                    ],
                    style=self._graph_wrapper_style(),
                ),
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=f"{self.page.ids.Calibration.graph_calibration}-model",
                            style=self._graph_style(),
                            config={"responsive": True},
                        ),
                    ],
                    style=self._graph_wrapper_style(),
                ),
            ],
            style={
                "display": "flex",
                "gap": "16px",
                "alignItems": "stretch",
                "width": "100%",
            },
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

    def _finalize_figure_size(self, figure: go.Figure) -> go.Figure:
        figure.update_layout(
            autosize=False,
            height=self.graph_height_px,
        )
        return figure

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_store, "data"),
            dash.Output(f"{self.page.ids.Calibration.graph_store}-model", "data"),
            dash.Output(self.page.ids.Calibration.calibration_store, "data"),
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(self.page.ids.Calibration.slope_out, "children"),
            dash.Output(self.page.ids.Calibration.intercept_out, "children"),
            dash.Output(self.page.ids.Calibration.r_squared_out, "children"),
            dash.Output(self.page.ids.Calibration.apply_status, "children"),
            dash.Input(self.page.ids.Calibration.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.Upload.fcs_path_store, "data"),
            dash.State(self.page.ids.Scattering.detector_dropdown, "value"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            prevent_initial_call=True,
        )
        def fit_scattering_calibration(
            n_clicks: int,
            uploaded_fcs_path: Any,
            detector_column: Any,
            mie_model: Any,
            bead_table_data: Any,
            medium_refractive_index: Any,
            particle_refractive_index: Any,
            core_refractive_index: Any,
            shell_refractive_index: Any,
            wavelength_nm: Any,
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            detector_sampling: Any,
        ) -> tuple:
            logger.debug(
                "fit_scattering_calibration called with n_clicks=%r uploaded_fcs_path=%r detector_column=%r mie_model=%r table_row_count=%r",
                n_clicks,
                uploaded_fcs_path,
                detector_column,
                mie_model,
                None if bead_table_data is None else len(bead_table_data),
            )
            del n_clicks

            result = services.run_scattering_calibration(
                uploaded_fcs_path=uploaded_fcs_path,
                detector_column=detector_column,
                mie_model=mie_model,
                bead_table_data=bead_table_data,
                medium_refractive_index=medium_refractive_index,
                particle_refractive_index=particle_refractive_index,
                core_refractive_index=core_refractive_index,
                shell_refractive_index=shell_refractive_index,
                wavelength_nm=wavelength_nm,
                detector_numerical_aperture=detector_numerical_aperture,
                detector_cache_numerical_aperture=detector_cache_numerical_aperture,
                detector_sampling=detector_sampling,
                simulated_curve_point_count=self.simulated_curve_point_count,
                logger=logger,
            )
            return result.to_tuple()

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_calibration, "figure"),
            dash.Input(self.page.ids.Calibration.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_left_graph(stored_figure: Any) -> go.Figure:
            logger.debug(
                "update_left_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )

            if not stored_figure:
                return self._finalize_figure_size(
                    _make_info_figure("Click Fit Calibration to generate the comparison graph.")
                )

            try:
                return self._finalize_figure_size(go.Figure(stored_figure))
            except Exception:
                logger.exception(
                    "Failed to reconstruct left graph from stored_figure=%r",
                    stored_figure,
                )
                return self._finalize_figure_size(
                    _make_info_figure("Failed to render comparison graph.")
                )

        @dash.callback(
            dash.Output(f"{self.page.ids.Calibration.graph_calibration}-model", "figure"),
            dash.Input(f"{self.page.ids.Calibration.graph_store}-model", "data"),
            prevent_initial_call=False,
        )
        def update_right_graph(stored_figure: Any) -> go.Figure:
            logger.debug(
                "update_right_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )

            if not stored_figure:
                return self._finalize_figure_size(
                    _make_info_figure("Click Fit Calibration to generate the simulated coupling graph.")
                )

            try:
                return self._finalize_figure_size(go.Figure(stored_figure))
            except Exception:
                logger.exception(
                    "Failed to reconstruct right graph from stored_figure=%r",
                    stored_figure,
                )
                return self._finalize_figure_size(
                    _make_info_figure("Failed to render simulated coupling graph.")
                )