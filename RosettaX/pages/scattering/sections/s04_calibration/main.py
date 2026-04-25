# -*- coding: utf-8 -*-

from typing import Any

import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages.scattering.state import ScatteringPageState
from RosettaX.utils import plottings, styling, graph_config

from . import services


logger = logging.getLogger(__name__)


class Calibration:
    """
    Scattering calibration section.

    Responsibilities
    ----------------
    - Render the calibration action area.
    - Display the calibration graphs.
    - Delegate the calibration workflow to the service layer.
    - Resolve the calibration detector channel from the selected peak process.

    Notes
    -----
    The scattering peak section no longer owns a static detector dropdown.
    Detector dropdowns are now owned by peak scripts and use pattern matching IDs.

    For calibration:
    - A 1D process uses its ``primary`` detector channel.
    - A 2D process uses its ``x`` detector channel, because the calibration table
      stores the clicked x coordinate.

    State ownership
    ---------------
    Calibration graph payloads and calibration payloads are stored in the page
    state store. This section no longer creates local graph or calibration stores.
    """

    simulated_curve_point_count = 200
    graph_height_px = 420
    graph_min_width_px = 0

    def __init__(self, page) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        logger.debug("Initialized Calibration section with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _build_header(self) -> dbc.CardHeader:
        return dbc.CardHeader("4. Fit calibration")

    def _build_body(self) -> dbc.CardBody:
        return dbc.CardBody(
            [
                self._build_action_block(),
                dash.html.Br(),
                self._build_graph_block(),
                dash.html.Br(),
                self._build_fit_outputs_block(),
                dash.html.Br(),
                dash.html.Div(
                    id=self.ids.apply_status,
                    style={
                        "marginTop": "8px",
                    },
                ),
            ]
        )

    def _graph_style(self) -> dict[str, Any]:
        return {
            **dict(styling.PAGE["graph"]),
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
                    id=self.ids.calibrate_btn,
                    n_clicks=0,
                ),
                dash.html.Div(
                    "This step uses the measured peak positions and expected coupling values currently present in the table.",
                    style={
                        "marginTop": "8px",
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=self.ids.graph_calibration,
                            style=graph_config.PLOTLY_GRAPH_STYLE,
                            config=graph_config.PLOTLY_GRAPH_CONFIG,
                        ),
                    ],
                    style=self._graph_wrapper_style(),
                ),
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=self.ids.graph_model,
                            style=graph_config.PLOTLY_GRAPH_STYLE,
                            config=graph_config.PLOTLY_GRAPH_CONFIG,

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

    def _finalize_figure_size(
        self,
        figure: go.Figure,
    ) -> go.Figure:
        figure.update_layout(
            autosize=False,
            height=self.graph_height_px,
        )

        return figure

    def _resolve_calibration_detector_column(
        self,
        *,
        selected_peak_process_name: Any,
        detector_dropdown_ids: list[dict[str, Any]],
        detector_dropdown_values: list[Any],
    ) -> Any:
        """
        Resolve the detector column used for the calibration payload.

        The detector is selected in the active peak script controls.

        Resolution order
        ----------------
        - primary: used by 1D peak scripts.
        - x: used by 2D peak scripts because the calibration table stores the
          clicked x coordinate.
        """
        selected_peak_process_name_string = (
            ""
            if selected_peak_process_name is None
            else str(selected_peak_process_name)
        )

        channel_values: dict[str, Any] = {}

        for detector_dropdown_id, detector_dropdown_value in zip(
            detector_dropdown_ids or [],
            detector_dropdown_values or [],
            strict=False,
        ):
            if not isinstance(detector_dropdown_id, dict):
                continue

            if detector_dropdown_id.get("process") != selected_peak_process_name_string:
                continue

            channel_name = detector_dropdown_id.get("channel")

            if not channel_name:
                continue

            channel_values[str(channel_name)] = detector_dropdown_value

        logger.debug(
            "Resolved calibration channel_values=%r for selected_peak_process_name=%r",
            channel_values,
            selected_peak_process_name_string,
        )

        if "primary" in channel_values:
            return channel_values["primary"]

        if "x" in channel_values:
            return channel_values["x"]

        return None

    def register_callbacks(self) -> None:
        logger.debug("Registering Calibration callbacks.")

        self._register_fit_calibration_callback()
        self._register_left_graph_callback()
        self._register_right_graph_callback()

    def _register_fit_calibration_callback(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(
                self.ids.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Output(self.ids.slope_out, "children"),
            dash.Output(self.ids.intercept_out, "children"),
            dash.Output(self.ids.r_squared_out, "children"),
            dash.Output(self.ids.apply_status, "children"),
            dash.Input(self.ids.calibrate_btn, "n_clicks"),
            dash.State(self.page.ids.State.page_state_store, "data"),
            dash.State(self.page.ids.Scattering.process_dropdown, "value"),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "id",
            ),
            dash.State(
                self.page.ids.Scattering.process_detector_dropdown_pattern(),
                "value",
            ),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.ids.bead_table, "data"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.blocker_bar_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            dash.State(self.page.ids.Parameters.detector_phi_angle_degree, "value"),
            dash.State(self.page.ids.Parameters.detector_gamma_angle_degree, "value"),
            prevent_initial_call=True,
        )
        def fit_scattering_calibration(
            n_clicks: int,
            page_state_payload: Any,
            selected_peak_process_name: Any,
            detector_dropdown_ids: list[dict[str, Any]],
            detector_dropdown_values: list[Any],
            mie_model: Any,
            bead_table_data: Any,
            medium_refractive_index: Any,
            particle_refractive_index: Any,
            core_refractive_index: Any,
            shell_refractive_index: Any,
            wavelength_nm: Any,
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            blocker_bar_numerical_aperture: Any,
            detector_sampling: Any,
            detector_phi_angle_degree: Any,
            detector_gamma_angle_degree: Any,
        ) -> tuple[Any, Any, Any, Any, Any, Any]:
            del n_clicks

            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            detector_column = self._resolve_calibration_detector_column(
                selected_peak_process_name=selected_peak_process_name,
                detector_dropdown_ids=detector_dropdown_ids,
                detector_dropdown_values=detector_dropdown_values,
            )

            logger.debug(
                "fit_scattering_calibration called with uploaded_fcs_path=%r "
                "selected_peak_process_name=%r detector_dropdown_ids=%r "
                "detector_dropdown_values=%r resolved_detector_column=%r "
                "mie_model=%r table_row_count=%r",
                page_state.uploaded_fcs_path,
                selected_peak_process_name,
                detector_dropdown_ids,
                detector_dropdown_values,
                detector_column,
                mie_model,
                None if bead_table_data is None else len(bead_table_data),
            )

            result = services.run_scattering_calibration(
                uploaded_fcs_path=page_state.uploaded_fcs_path,
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
                blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
                detector_sampling=detector_sampling,
                detector_phi_angle_degree=detector_phi_angle_degree,
                detector_gamma_angle_degree=detector_gamma_angle_degree,
                simulated_curve_point_count=self.simulated_curve_point_count,
                logger=logger,
            )

            (
                calibration_graph_payload,
                calibration_model_graph_payload,
                calibration_payload,
                bead_table_data,
                slope_text,
                intercept_text,
                r_squared_text,
                apply_status,
            ) = result.to_tuple()

            page_state = page_state.update(
                calibration_graph_payload=calibration_graph_payload,
                calibration_model_graph_payload=calibration_model_graph_payload,
                calibration_payload=calibration_payload,
            )

            return (
                page_state.to_dict(),
                bead_table_data,
                slope_text,
                intercept_text,
                r_squared_text,
                apply_status,
            )

    def _register_left_graph_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_calibration, "figure"),
            dash.Input(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=False,
        )
        def update_left_graph(page_state_payload: Any) -> go.Figure:
            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            stored_figure = page_state.calibration_graph_payload

            logger.debug(
                "update_left_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )

            if not stored_figure:
                return self._finalize_figure_size(
                    plottings._make_info_figure(
                        "Click Fit Calibration to generate the comparison graph."
                    )
                )

            try:
                return self._finalize_figure_size(
                    go.Figure(stored_figure)
                )

            except Exception:
                logger.exception(
                    "Failed to reconstruct left graph from stored_figure=%r",
                    stored_figure,
                )

                return self._finalize_figure_size(
                    plottings._make_info_figure(
                        "Failed to render comparison graph."
                    )
                )

    def _register_right_graph_callback(self) -> None:
        @dash.callback(
            dash.Output(self.ids.graph_model, "figure"),
            dash.Input(self.page.ids.State.page_state_store, "data"),
            prevent_initial_call=False,
        )
        def update_right_graph(page_state_payload: Any) -> go.Figure:
            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            stored_figure = page_state.calibration_model_graph_payload

            logger.debug(
                "update_right_graph called with stored_figure_type=%s",
                type(stored_figure).__name__,
            )

            if not stored_figure:
                return self._finalize_figure_size(
                    plottings._make_info_figure(
                        "Click Fit Calibration to generate the simulated coupling graph."
                    )
                )

            try:
                return self._finalize_figure_size(
                    go.Figure(stored_figure)
                )

            except Exception:
                logger.exception(
                    "Failed to reconstruct right graph from stored_figure=%r",
                    stored_figure,
                )

                return self._finalize_figure_size(
                    plottings._make_info_figure(
                        "Failed to render simulated coupling graph."
                    )
                )