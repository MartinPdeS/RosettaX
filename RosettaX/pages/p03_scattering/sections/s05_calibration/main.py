# -*- coding: utf-8 -*-

from typing import Any

import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from RosettaX.pages.p03_scattering.state import ScatteringPageState
from RosettaX.utils import graph_config
from RosettaX.utils import plottings

from . import services


logger = logging.getLogger(__name__)


class Calibration:
    """
    Scattering instrument response fit section.

    Responsibilities
    ----------------
    - Render the instrument response fit action area.
    - Display the instrument response graph.
    - Display the calibration standard Mie relation graph.
    - Provide independent x and y log scale controls for both graphs.
    - Delegate the scattering calibration workflow to the service layer.
    - Resolve the measured detector channel from the selected peak process.
    - Store graph payloads and calibration payload in page state.

    Table ownership
    ---------------
    This section does not render the calibration standard table and does not
    compute modeled standard coupling. The dedicated table section owns those
    actions. This section reads the table during fitting and converts the
    standard data into a saved scattering calibration object.
    """

    simulated_curve_point_count = 200
    graph_height_px = 520
    graph_min_width_px = 760

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page
        self.ids = page.ids.Calibration

        logger.debug(
            "Initialized Scattering Calibration section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the scattering instrument response calibration layout.
        """
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ]
        )

    def _get_layout(self) -> dbc.Card:
        """
        Compatibility alias for older section loading code.
        """
        return self.get_layout()

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return dbc.CardHeader(
            "5. Fit instrument response",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_action_block(),
                dash.html.Br(),
                self._build_graph_block(),
                dash.html.Br(),
                dash.html.Div(
                    id=self.ids.apply_status,
                    style={
                        "marginTop": "8px",
                    },
                ),
            ]
        )

    def _build_action_block(self) -> dash.html.Div:
        """
        Build the instrument response fit action block.
        """
        return dash.html.Div(
            [
                dash.html.Button(
                    "Fit Instrument Response",
                    id=self.ids.calibrate_btn,
                    n_clicks=0,
                ),
                dash.html.Div(
                    (
                        "This step uses the measured standard peak positions and "
                        "modeled standard coupling values currently present in the "
                        "calibration standard table. The fitted relation maps "
                        "measured instrument signal to modeled optical coupling."
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
        Build the two side by side graph panels.
        """
        return dash.html.Div(
            [
                self._build_graph_panel_card(
                    title="Instrument response calibration",
                    graph_id=self.ids.graph_calibration,
                    x_switch_id=self.ids.instrument_response_x_log_switch,
                    y_switch_id=self.ids.instrument_response_y_log_switch,
                    x_default_enabled=False,
                    y_default_enabled=False,
                    footer_content=self._build_instrument_response_footer(),
                ),
                self._build_graph_panel_card(
                    title="Calibration standard Mie relation",
                    graph_id=self.ids.graph_model,
                    x_switch_id=self.ids.mie_relation_x_log_switch,
                    y_switch_id=self.ids.mie_relation_y_log_switch,
                    x_default_enabled=False,
                    y_default_enabled=True,
                    footer_content=self._build_mie_relation_footer(),
                ),
            ],
            style={
                "display": "flex",
                "gap": "24px",
                "alignItems": "stretch",
                "width": "100%",
                "overflowX": "auto",
            },
        )

    def _build_graph_panel_card(
        self,
        *,
        title: str,
        graph_id: str,
        x_switch_id: str,
        y_switch_id: str,
        x_default_enabled: bool,
        y_default_enabled: bool,
        footer_content: Any,
    ) -> dbc.Card:
        """
        Build one self contained graph panel card.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    title,
                    style={
                        "fontWeight": "600",
                    },
                ),
                dbc.CardBody(
                    [
                        self._build_axis_control_block(
                            x_switch_id=x_switch_id,
                            y_switch_id=y_switch_id,
                            x_default_enabled=x_default_enabled,
                            y_default_enabled=y_default_enabled,
                        ),
                        dash.html.Div(
                            style={
                                "height": "12px",
                            },
                        ),
                        dash.dcc.Graph(
                            id=graph_id,
                            style={
                                **graph_config.PLOTLY_GRAPH_STYLE,
                                "height": f"{self.graph_height_px}px",
                                "width": "100%",
                            },
                            config=graph_config.PLOTLY_GRAPH_CONFIG,
                        ),
                    ]
                ),
                dbc.CardFooter(
                    footer_content,
                    style={
                        "opacity": 0.9,
                    },
                ),
            ],
            style={
                "flex": "1 1 0",
                "minWidth": f"{self.graph_min_width_px}px",
            },
            class_name="h-100",
        )

    def _build_axis_control_block(
        self,
        *,
        x_switch_id: str,
        y_switch_id: str,
        x_default_enabled: bool,
        y_default_enabled: bool,
    ) -> dash.html.Div:
        """
        Build the axis control block placed above a graph.
        """
        return dash.html.Div(
            [
                dbc.Checklist(
                    id=x_switch_id,
                    options=[
                        {
                            "label": "Log x",
                            "value": "log",
                        }
                    ],
                    value=["log"] if x_default_enabled else [],
                    switch=True,
                    inline=True,
                    persistence=True,
                    persistence_type="session",
                ),
                dbc.Checklist(
                    id=y_switch_id,
                    options=[
                        {
                            "label": "Log y",
                            "value": "log",
                        }
                    ],
                    value=["log"] if y_default_enabled else [],
                    switch=True,
                    inline=True,
                    persistence=True,
                    persistence_type="session",
                ),
            ],
            style={
                "display": "flex",
                "gap": "18px",
                "alignItems": "center",
                "flexWrap": "wrap",
            },
        )

    def _build_instrument_response_footer(self) -> dash.html.Div:
        """
        Build the instrument response card footer with fit outputs.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    (
                        "This graph shows the fitted relation between measured "
                        "standard peak intensity and modeled optical coupling. "
                        "The fitted slope is the instrument gain."
                    ),
                    style={
                        "marginBottom": "10px",
                    },
                ),
                dash.html.Div(
                    [
                        self._build_fit_metric(
                            "Gain",
                            self.ids.slope_out,
                        ),
                        self._build_fit_metric(
                            "Offset",
                            self.ids.intercept_out,
                        ),
                        self._build_fit_metric(
                            "R²",
                            self.ids.r_squared_out,
                        ),
                    ],
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(3, minmax(120px, 1fr))",
                        "gap": "10px",
                        "alignItems": "stretch",
                    },
                ),
            ]
        )

    def _build_mie_relation_footer(self) -> dash.html.Div:
        """
        Build the calibration standard Mie relation card footer.
        """
        return dash.html.Div(
            (
                "This graph shows the modeled relation between standard particle "
                "diameter and modeled optical coupling for the calibration standard."
            )
        )

    def _build_fit_metric(
        self,
        label: str,
        output_id: str,
    ) -> dash.html.Div:
        """
        Build one compact fit metric box.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    label,
                    style={
                        "fontWeight": "600",
                        "fontSize": "0.9rem",
                        "opacity": 0.85,
                    },
                ),
                dash.html.Div(
                    "",
                    id=output_id,
                    style={
                        "fontFamily": "monospace",
                        "fontSize": "0.95rem",
                        "marginTop": "2px",
                    },
                ),
            ],
            style={
                "padding": "8px 10px",
                "border": "1px solid rgba(128,128,128,0.25)",
                "borderRadius": "8px",
                "background": "rgba(128,128,128,0.08)",
            },
        )

    def _finalize_figure_size(
        self,
        figure: go.Figure,
    ) -> go.Figure:
        """
        Apply the section graph size and legend placement.
        """
        figure.update_layout(
            autosize=True,
            height=self.graph_height_px,
            margin={
                "l": 70,
                "r": 24,
                "t": 70,
                "b": 70,
            },
            legend={
                "x": 0.98,
                "y": 0.98,
                "xanchor": "right",
                "yanchor": "top",
                "bgcolor": "rgba(255,255,255,0.65)",
                "bordercolor": "rgba(0,0,0,0.15)",
                "borderwidth": 1,
            },
        )

        return figure

    def _axis_type_from_toggle(
        self,
        value: Any,
    ) -> str:
        """
        Resolve Plotly axis type from a Dash checklist value.
        """
        if isinstance(value, list) and "log" in value:
            return "log"

        return "linear"

    def _apply_axis_scales(
        self,
        *,
        figure: go.Figure,
        x_log_value: Any,
        y_log_value: Any,
    ) -> go.Figure:
        """
        Apply x and y axis scale controls to a figure.
        """
        figure.update_xaxes(
            type=self._axis_type_from_toggle(
                x_log_value,
            )
        )

        figure.update_yaxes(
            type=self._axis_type_from_toggle(
                y_log_value,
            )
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
        Resolve the measured detector column used for the instrument response.

        Resolution order
        ----------------
        - primary: used by 1D peak scripts.
        - scattering_axis: used by newer 2D scripts with semantic channel names.
        - x_axis: used by newer generic 2D scripts.
        - x: used by older 2D scripts.
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
            "Resolved scattering instrument response channel_values=%r "
            "for selected_peak_process_name=%r",
            channel_values,
            selected_peak_process_name_string,
        )

        if "primary" in channel_values:
            return channel_values["primary"]

        if "scattering_axis" in channel_values:
            return channel_values["scattering_axis"]

        if "x_axis" in channel_values:
            return channel_values["x_axis"]

        if "x" in channel_values:
            return channel_values["x"]

        return None

    def register_callbacks(self) -> None:
        """
        Register calibration callbacks.
        """
        logger.debug("Registering Scattering Calibration callbacks.")

        self._register_fit_calibration_callback()
        self._register_left_graph_callback()
        self._register_right_graph_callback()

    def _register_fit_calibration_callback(self) -> None:
        """
        Register the scattering instrument response fit callback.
        """

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
        def fit_scattering_instrument_response(
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
                "fit_scattering_instrument_response called with uploaded_fcs_path=%r "
                "selected_peak_process_name=%r resolved_detector_column=%r "
                "mie_model=%r table_row_count=%r",
                page_state.uploaded_fcs_path,
                selected_peak_process_name,
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
                instrument_response_graph_payload,
                calibration_standard_mie_graph_payload,
                calibration_payload,
                next_bead_table_data,
                slope_text,
                intercept_text,
                r_squared_text,
                apply_status,
            ) = result.to_tuple()

            page_state = page_state.update(
                calibration_graph_payload=instrument_response_graph_payload,
                calibration_model_graph_payload=calibration_standard_mie_graph_payload,
                calibration_payload=calibration_payload,
            )

            logger.debug(
                "fit_scattering_instrument_response stored calibration payload keys=%r",
                (
                    list(calibration_payload.keys())
                    if isinstance(calibration_payload, dict)
                    else type(calibration_payload).__name__
                ),
            )

            return (
                page_state.to_dict(),
                next_bead_table_data,
                slope_text,
                intercept_text,
                r_squared_text,
                apply_status,
            )

    def _register_left_graph_callback(self) -> None:
        """
        Register instrument response graph reconstruction callback.
        """

        @dash.callback(
            dash.Output(self.ids.graph_calibration, "figure"),
            dash.Input(self.page.ids.State.page_state_store, "data"),
            dash.Input(self.ids.instrument_response_x_log_switch, "value"),
            dash.Input(self.ids.instrument_response_y_log_switch, "value"),
            prevent_initial_call=False,
        )
        def update_left_graph(
            page_state_payload: Any,
            x_log_value: Any,
            y_log_value: Any,
        ) -> go.Figure:
            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            stored_figure = page_state.calibration_graph_payload

            logger.debug(
                "update_left_graph called with stored_figure_type=%s x_log_value=%r y_log_value=%r",
                type(stored_figure).__name__,
                x_log_value,
                y_log_value,
            )

            if not stored_figure:
                figure = plottings._make_info_figure(
                    "Click Fit Instrument Response to generate the instrument response graph."
                )

            else:
                try:
                    figure = go.Figure(
                        stored_figure,
                    )

                except Exception:
                    logger.exception(
                        "Failed to reconstruct instrument response graph from stored_figure=%r",
                        stored_figure,
                    )

                    figure = plottings._make_info_figure(
                        "Failed to render instrument response graph."
                    )

            figure = self._apply_axis_scales(
                figure=figure,
                x_log_value=x_log_value,
                y_log_value=y_log_value,
            )

            return self._finalize_figure_size(
                figure,
            )

    def _register_right_graph_callback(self) -> None:
        """
        Register calibration standard Mie relation graph reconstruction callback.
        """

        @dash.callback(
            dash.Output(self.ids.graph_model, "figure"),
            dash.Input(self.page.ids.State.page_state_store, "data"),
            dash.Input(self.ids.mie_relation_x_log_switch, "value"),
            dash.Input(self.ids.mie_relation_y_log_switch, "value"),
            prevent_initial_call=False,
        )
        def update_right_graph(
            page_state_payload: Any,
            x_log_value: Any,
            y_log_value: Any,
        ) -> go.Figure:
            page_state = ScatteringPageState.from_dict(
                page_state_payload if isinstance(page_state_payload, dict) else None
            )

            stored_figure = page_state.calibration_model_graph_payload

            logger.debug(
                "update_right_graph called with stored_figure_type=%s x_log_value=%r y_log_value=%r",
                type(stored_figure).__name__,
                x_log_value,
                y_log_value,
            )

            if not stored_figure:
                figure = plottings._make_info_figure(
                    "Click Fit Instrument Response to generate the calibration standard Mie relation graph."
                )

            else:
                try:
                    figure = go.Figure(
                        stored_figure,
                    )

                except Exception:
                    logger.exception(
                        "Failed to reconstruct calibration standard Mie relation graph "
                        "from stored_figure=%r",
                        stored_figure,
                    )

                    figure = plottings._make_info_figure(
                        "Failed to render calibration standard Mie relation graph."
                    )

            figure = self._apply_axis_scales(
                figure=figure,
                x_log_value=x_log_value,
                y_log_value=y_log_value,
            )

            return self._finalize_figure_size(
                figure,
            )