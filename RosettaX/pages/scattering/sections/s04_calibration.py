# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils.plottings import _make_info_figure


logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    figure_store: Any = dash.no_update
    calibration_store: Any = dash.no_update
    bead_table_data: Any = dash.no_update
    slope_out: str = ""
    intercept_out: str = ""
    r_squared_out: str = ""
    apply_status: str = ""

    def to_tuple(self) -> tuple:
        return (
            self.figure_store,
            self.calibration_store,
            self.bead_table_data,
            self.slope_out,
            self.intercept_out,
            self.r_squared_out,
            self.apply_status,
        )


class Calibration:
    """
    Scattering calibration section.

    Workflow
    --------
    - Build a histogram from the selected scattering detector.
    - Detect peak positions from that histogram.
    - Read the user provided particle diameters from the table.
    - Compute expected coupling values with PyMieSim.
    - Fit measured peak positions to modeled coupling in log10 space.
    - Store the resulting calibration payload and figure.
    """

    bead_table_columns = [
        {"name": "Particle diameter [nm]", "id": "col1", "editable": True},
        {"name": "Measured peak position [a.u.]", "id": "col2", "editable": False},
        {"name": "Expected coupling", "id": "col3", "editable": False},
    ]

    default_bead_rows = [
        {"col1": "", "col2": "", "col3": ""}
        for _ in range(3)
    ]

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized CalibrationSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("4. Calibration"),
                dbc.CardBody(
                    [
                        dash.dcc.Store(id=self.page.ids.Calibration.graph_store),
                        dash.dcc.Store(id=self.page.ids.Calibration.calibration_store),
                        self._build_reference_axis_label_row(),
                        dash.html.Br(),
                        self._build_bead_table_block(),
                        dash.html.Hr(),
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

    def _build_reference_axis_label_row(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div("Reference axis label:"),
                dash.dcc.Input(
                    id=self.page.ids.Calibration.reference_axis_label,
                    type="text",
                    value="Expected coupling",
                    style={"width": "320px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "12px"},
        )

    def _build_bead_table_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.H5("Particle diameter list"),
                dash.dash_table.DataTable(
                    id=self.page.ids.Calibration.bead_table,
                    columns=self.bead_table_columns,
                    data=self.default_bead_rows,
                    editable=True,
                    row_deletable=True,
                    style_table={"overflowX": "auto"},
                ),
                dash.html.Div(
                    [
                        dash.html.Button(
                            "Add Row",
                            id=self.page.ids.Calibration.add_row_btn,
                            n_clicks=0,
                        )
                    ],
                    style={"marginTop": "10px"},
                ),
            ]
        )

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.dcc.Graph(
                    id=self.page.ids.Calibration.graph_calibration,
                    style=self.page.style["graph"],
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

    def register_callbacks(self) -> None:
        @dash.callback(
            dash.Output(
                self.page.ids.Calibration.bead_table,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(self.page.ids.Calibration.add_row_btn, "n_clicks"),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Calibration.bead_table, "columns"),
            prevent_initial_call=True,
        )
        def add_row(
            n_clicks: int,
            rows: list[dict],
            columns: list[dict],
        ) -> list[dict]:
            del n_clicks

            next_rows = list(rows or [])
            next_rows.append({column["id"]: "" for column in columns})
            return next_rows

        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_store, "data"),
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
            dash.State(self.page.ids.Scattering.nbins_input, "value"),
            dash.State(
                self.page.ids.Upload.max_events_for_plots_input,
                "value",
                allow_optional=True,
            ),
            dash.State(self.page.ids.Calibration.bead_table, "data"),
            dash.State(self.page.ids.Calibration.reference_axis_label, "value"),
            dash.State(self.page.ids.Parameters.mie_model, "value"),
            dash.State(self.page.ids.Parameters.medium_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.core_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.shell_refractive_index_custom, "value"),
            dash.State(self.page.ids.Parameters.particle_diameter, "value"),
            dash.State(self.page.ids.Parameters.core_diameter, "value"),
            dash.State(self.page.ids.Parameters.shell_thickness, "value"),
            dash.State(self.page.ids.Parameters.wavelength_nm, "value"),
            dash.State(self.page.ids.Parameters.detector_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_cache_numerical_aperture, "value"),
            dash.State(self.page.ids.Parameters.detector_sampling, "value"),
            dash.State("runtime-config-store", "data"),
            prevent_initial_call=True,
        )
        def calibrate_scattering(
            _n_clicks: int,
            uploaded_fcs_path: Optional[str],
            detector_column: Optional[str],
            n_bins_for_plots: Any,
            max_events_for_plots: Any,
            table_data: Optional[list[dict]],
            reference_axis_label: Optional[str],
            mie_model: Any,
            medium_refractive_index: Any,
            particle_refractive_index: Any,
            core_refractive_index: Any,
            shell_refractive_index: Any,
            particle_diameter: Any,
            core_diameter: Any,
            shell_thickness: Any,
            wavelength_nm: Any,
            detector_numerical_aperture: Any,
            detector_cache_numerical_aperture: Any,
            detector_sampling: Any,
            runtime_config_data: Any,
        ) -> tuple:
            logger.debug(
                "calibrate_scattering called with n_clicks=%r uploaded_fcs_path=%r detector_column=%r",
                _n_clicks,
                uploaded_fcs_path,
                detector_column,
            )
            del _n_clicks

            try:
                logger.debug("Starting scattering calibration validation.")

                if not uploaded_fcs_path:
                    logger.debug("Calibration aborted because uploaded_fcs_path is missing.")
                    figure = _make_info_figure("Upload an FCS file first.")
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Missing FCS file.",
                    ).to_tuple()

                if not detector_column:
                    logger.debug("Calibration aborted because detector_column is missing.")
                    figure = _make_info_figure("Select a scattering detector first.")
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Missing scattering detector.",
                    ).to_tuple()

                logger.debug("Input validation passed.")

                resolved_mie_model = None if mie_model is None else str(mie_model).strip()
                logger.debug("Resolved mie model=%r", resolved_mie_model)

                if resolved_mie_model == "Core/Shell Sphere":
                    logger.debug("Calibration aborted because Core/Shell Sphere is not implemented.")
                    figure = _make_info_figure(
                        "Core/Shell Sphere coupling is not implemented yet in this calibration workflow."
                    )
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Core/Shell Sphere is not implemented yet for scattering calibration.",
                    ).to_tuple()

                resolved_peak_count = self._resolve_peak_count(runtime_config_data)
                resolved_n_bins_for_plots = self._resolve_n_bins_for_plots(
                    n_bins_for_plots=n_bins_for_plots,
                    runtime_config_data=runtime_config_data,
                )
                resolved_max_events_for_plots = self._resolve_max_events_for_plots(
                    max_events_for_plots=max_events_for_plots,
                    runtime_config_data=runtime_config_data,
                )

                logger.debug(
                    "Resolved control values peak_count=%r n_bins=%r max_events=%r",
                    resolved_peak_count,
                    resolved_n_bins_for_plots,
                    resolved_max_events_for_plots,
                )

                resolved_medium_refractive_index = self._as_required_float(
                    medium_refractive_index,
                    "medium_refractive_index",
                )
                resolved_particle_refractive_index = self._as_required_float(
                    particle_refractive_index,
                    "particle_refractive_index",
                )
                resolved_wavelength_nm = self._as_required_float(
                    wavelength_nm,
                    "wavelength_nm",
                )
                resolved_optical_power_watt = 1.0
                resolved_source_numerical_aperture = 0.1
                resolved_detector_numerical_aperture = self._as_required_float(
                    detector_numerical_aperture,
                    "detector_numerical_aperture",
                )
                resolved_detector_cache_numerical_aperture = self._as_required_float(
                    detector_cache_numerical_aperture,
                    "detector_cache_numerical_aperture",
                )
                resolved_detector_sampling = self._as_required_int(
                    detector_sampling,
                    "detector_sampling",
                )

                logger.debug(
                    "Resolved physical parameters medium_refractive_index=%r "
                    "particle_refractive_index=%r wavelength_nm=%r optical_power_watt=%r "
                    "source_numerical_aperture=%r detector_numerical_aperture=%r "
                    "detector_cache_numerical_aperture=%r detector_sampling=%r",
                    resolved_medium_refractive_index,
                    resolved_particle_refractive_index,
                    resolved_wavelength_nm,
                    resolved_optical_power_watt,
                    resolved_source_numerical_aperture,
                    resolved_detector_numerical_aperture,
                    resolved_detector_cache_numerical_aperture,
                    resolved_detector_sampling,
                )

                scattering_backend = BackEnd(
                    fcs_file_path=str(uploaded_fcs_path),
                    detector_column=str(detector_column),
                )
                logger.debug("Scattering backend created successfully.")

                histogram_result = scattering_backend.build_histogram(
                    n_bins_for_plots=resolved_n_bins_for_plots,
                    max_events_for_analysis=resolved_max_events_for_plots,
                )
                logger.debug(
                    "Histogram built successfully with value_count=%r",
                    histogram_result.values.size,
                )

                peak_detection_result = scattering_backend.find_histogram_peaks(
                    histogram_result=histogram_result,
                    peak_count=resolved_peak_count,
                )
                logger.debug(
                    "Peak detection succeeded with peak_positions=%r",
                    peak_detection_result.peak_positions.tolist(),
                )

                particle_diameters_nm = self._extract_particle_diameters_from_table(
                    table_data or []
                )
                logger.debug(
                    "Extracted particle diameters=%r",
                    particle_diameters_nm.tolist(),
                )

                if particle_diameters_nm.size < 2:
                    logger.debug(
                        "Calibration aborted because fewer than 2 valid particle diameters were provided."
                    )
                    figure = _make_info_figure(
                        "Enter at least 2 particle diameters in the first column."
                    )
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Need at least 2 valid particle diameters.",
                    ).to_tuple()

                if particle_diameters_nm.size != peak_detection_result.peak_positions.size:
                    logger.debug(
                        "Calibration aborted because particle diameter count=%r does not match peak count=%r",
                        particle_diameters_nm.size,
                        peak_detection_result.peak_positions.size,
                    )
                    figure = _make_info_figure(
                        "The number of particle diameters must match the number of detected peaks."
                    )
                    return CalibrationResult(
                        figure_store=figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status=(
                            f"Detected {peak_detection_result.peak_positions.size} peaks but "
                            f"received {particle_diameters_nm.size} particle diameters."
                        ),
                    ).to_tuple()

                logger.debug("About to call compute_modeled_coupling_from_diameters.")

                modeled_coupling_result = scattering_backend.compute_modeled_coupling_from_diameters(
                    particle_diameters_nm=particle_diameters_nm,
                    wavelength_nm=resolved_wavelength_nm,
                    source_numerical_aperture=resolved_source_numerical_aperture,
                    optical_power_watt=resolved_optical_power_watt,
                    detector_numerical_aperture=resolved_detector_numerical_aperture,
                    medium_refractive_index=resolved_medium_refractive_index,
                    particle_refractive_index=resolved_particle_refractive_index,
                    detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
                    detector_rotation_degree=0.0,
                    detector_phi_offset_degree=0.0,
                    detector_gamma_offset_degree=0.0,
                    polarization_angle_degree=0.0,
                    detector_sampling=resolved_detector_sampling,
                )

                logger.debug(
                    "Returned from compute_modeled_coupling_from_diameters with expected_coupling_values=%r",
                    modeled_coupling_result.expected_coupling_values.tolist(),
                )

                fit_result = scattering_backend.fit_measured_peak_positions_to_modeled_coupling(
                    measured_peak_positions=peak_detection_result.peak_positions,
                    modeled_coupling_result=modeled_coupling_result,
                )
                logger.debug(
                    "Fit succeeded with slope=%r intercept=%r r_squared=%r",
                    fit_result.slope,
                    fit_result.intercept,
                    fit_result.r_squared,
                )

                figure = scattering_backend.build_calibration_figure(
                    fit_result=fit_result,
                )
                logger.debug("Calibration figure built successfully.")

                calibration_payload = scattering_backend.build_calibration_payload(
                    peak_detection_result=peak_detection_result,
                    modeled_coupling_result=modeled_coupling_result,
                    fit_result=fit_result,
                    notes="",
                )
                logger.debug("Calibration payload built successfully.")

                calibration_payload["payload"]["parameters"].update(
                    {
                        "mie_model": resolved_mie_model,
                        "medium_refractive_index": resolved_medium_refractive_index,
                        "particle_refractive_index": resolved_particle_refractive_index,
                        "core_refractive_index": core_refractive_index,
                        "shell_refractive_index": shell_refractive_index,
                        "particle_diameter_nm": particle_diameter,
                        "core_diameter_nm": core_diameter,
                        "shell_thickness_nm": shell_thickness,
                        "wavelength_nm": resolved_wavelength_nm,
                        "optical_power_watt": resolved_optical_power_watt,
                        "source_numerical_aperture": resolved_source_numerical_aperture,
                        "detector_numerical_aperture": resolved_detector_numerical_aperture,
                        "detector_cache_numerical_aperture": resolved_detector_cache_numerical_aperture,
                        "detector_sampling": resolved_detector_sampling,
                    }
                )

                if reference_axis_label:
                    calibration_payload["payload"]["payload"]["y_definition"] = str(reference_axis_label)

                updated_table_data = self._build_updated_table_data(
                    particle_diameters_nm=fit_result.particle_diameters_nm,
                    measured_peak_positions=fit_result.measured_peak_positions,
                    expected_coupling_values=fit_result.expected_coupling_values,
                )
                logger.debug(
                    "Updated table data prepared with row_count=%r",
                    len(updated_table_data),
                )

                result = CalibrationResult(
                    figure_store=figure.to_dict(),
                    calibration_store=calibration_payload,
                    bead_table_data=updated_table_data,
                    slope_out=f"{fit_result.slope:.6g}",
                    intercept_out=f"{fit_result.intercept:.6g} (A={fit_result.prefactor:.6g})",
                    r_squared_out=f"{fit_result.r_squared:.6g}",
                    apply_status="Scattering calibration created successfully.",
                )

                logger.debug("Scattering calibration completed successfully.")
                return result.to_tuple()

            except Exception as exc:
                logger.exception("Scattering calibration failed.")
                figure = _make_info_figure("Scattering calibration failed.")
                return CalibrationResult(
                    figure_store=figure.to_dict(),
                    calibration_store=dash.no_update,
                    bead_table_data=dash.no_update,
                    slope_out="",
                    intercept_out="",
                    r_squared_out="",
                    apply_status=f"{type(exc).__name__}: {exc}",
                ).to_tuple()



























        @dash.callback(
            dash.Output(self.page.ids.Calibration.graph_calibration, "figure"),
            dash.Input(self.page.ids.Calibration.graph_store, "data"),
            prevent_initial_call=False,
        )
        def update_calibration_graph(stored_figure: Any) -> go.Figure:
            if not stored_figure:
                return _make_info_figure("Create a calibration first.")

            return go.Figure(stored_figure)

    def _resolve_peak_count(self, runtime_config_data: Any) -> int:
        if not isinstance(runtime_config_data, dict):
            return 3

        try:
            return max(1, int(runtime_config_data.get("peak_count", 3)))
        except Exception:
            return 3

    def _resolve_n_bins_for_plots(
        self,
        *,
        n_bins_for_plots: Any,
        runtime_config_data: Any,
    ) -> int:
        if n_bins_for_plots not in (None, ""):
            return max(10, int(n_bins_for_plots))

        if isinstance(runtime_config_data, dict):
            try:
                return max(10, int(runtime_config_data.get("n_bins_for_plots", 100)))
            except Exception:
                pass

        return 100

    def _resolve_max_events_for_plots(
        self,
        *,
        max_events_for_plots: Any,
        runtime_config_data: Any,
    ) -> int:
        if max_events_for_plots not in (None, ""):
            return max(1, int(max_events_for_plots))

        if isinstance(runtime_config_data, dict):
            try:
                return max(1, int(runtime_config_data.get("max_events_for_analysis", 10000)))
            except Exception:
                pass

        return 10000

    def _extract_particle_diameters_from_table(
        self,
        table_data: list[dict[str, Any]],
    ) -> np.ndarray:
        particle_diameters_nm: list[float] = []

        for row in table_data or []:
            raw_particle_diameter = row.get("col1")

            try:
                if raw_particle_diameter in ("", None):
                    continue

                particle_diameter_nm = float(raw_particle_diameter)
            except Exception:
                continue

            if particle_diameter_nm <= 0.0:
                continue

            particle_diameters_nm.append(float(particle_diameter_nm))

        return np.asarray(particle_diameters_nm, dtype=float)

    def _build_updated_table_data(
        self,
        *,
        particle_diameters_nm: np.ndarray,
        measured_peak_positions: np.ndarray,
        expected_coupling_values: np.ndarray,
    ) -> list[dict[str, str]]:
        updated_rows: list[dict[str, str]] = []

        for particle_diameter_nm, measured_peak_position, expected_coupling_value in zip(
            particle_diameters_nm,
            measured_peak_positions,
            expected_coupling_values,
            strict=False,
        ):
            updated_rows.append(
                {
                    "col1": f"{float(particle_diameter_nm):.6g}",
                    "col2": f"{float(measured_peak_position):.6g}",
                    "col3": f"{float(expected_coupling_value):.6g}",
                }
            )

        return updated_rows

    def _as_required_float(self, value: Any, field_name: str) -> float:
        try:
            if value in (None, ""):
                raise ValueError
            return float(value)
        except Exception as exc:
            raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc

    def _as_required_int(self, value: Any, field_name: str) -> int:
        try:
            if value in (None, ""):
                raise ValueError
            return int(value)
        except Exception as exc:
            raise ValueError(f"Invalid value for {field_name}: {value!r}") from exc