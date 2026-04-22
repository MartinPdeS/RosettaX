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
    model_figure_store: Any = dash.no_update
    calibration_store: Any = dash.no_update
    bead_table_data: Any = dash.no_update
    slope_out: str = ""
    intercept_out: str = ""
    r_squared_out: str = ""
    apply_status: str = ""

    def to_tuple(self) -> tuple:
        return (
            self.figure_store,
            self.model_figure_store,
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

    Responsibilities
    ----------------
    - Read the calibration reference table as the source of truth.
    - Compute expected coupling values for the solid sphere model.
    - Write expected coupling values back into the table.
    - Fit the calibration curve and update outputs.
    - Render two graphs side by side:
      1. calibration fit graph
      2. measured peak position versus expected coupling graph

    Notes
    -----
    The calibration table is rendered in the parameter section.
    This section only reads and updates it.
    """

    def __init__(self, page) -> None:
        self.page = page
        logger.debug("Initialized CalibrationSection with page=%r", page)

    def get_layout(self) -> dbc.Card:
        return dbc.Card(
            [
                dbc.CardHeader("4. Calibration results"),
                dbc.CardBody(
                    [
                        dash.dcc.Store(id=self.page.ids.Calibration.graph_store),
                        dash.dcc.Store(
                            id=f"{self.page.ids.Calibration.graph_store}-model",
                        ),
                        dash.dcc.Store(id=self.page.ids.Calibration.calibration_store),
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

    def _build_graph_block(self) -> dash.html.Div:
        return dash.html.Div(
            [
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=self.page.ids.Calibration.graph_calibration,
                            style=self.page.style["graph"],
                        ),
                    ],
                    style={
                        "flex": "1",
                        "minWidth": "0",
                    },
                ),
                dash.html.Div(
                    [
                        dash.dcc.Graph(
                            id=f"{self.page.ids.Calibration.graph_calibration}-model",
                            style=self.page.style["graph"],
                        ),
                    ],
                    style={
                        "flex": "1",
                        "minWidth": "0",
                    },
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
            _n_clicks: int,
            uploaded_fcs_path: Optional[str],
            detector_column: Optional[str],
            mie_model: Any,
            bead_table_data: Optional[list[dict[str, Any]]],
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
                "fit_scattering_calibration called with n_clicks=%r uploaded_fcs_path=%r detector_column=%r mie_model=%r table_row_count=%r bead_table_data=%r",
                _n_clicks,
                uploaded_fcs_path,
                detector_column,
                mie_model,
                0 if bead_table_data is None else len(bead_table_data),
                bead_table_data,
            )
            del _n_clicks

            resolved_mie_model = self._resolve_mie_model(mie_model)
            current_table_rows = [dict(row) for row in (bead_table_data or [])]

            try:
                if not uploaded_fcs_path:
                    calibration_figure = _make_info_figure("Upload an FCS file first.")
                    model_figure = _make_info_figure("Upload an FCS file first.")
                    return CalibrationResult(
                        figure_store=calibration_figure.to_dict(),
                        model_figure_store=model_figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Missing FCS file.",
                    ).to_tuple()

                if not detector_column:
                    calibration_figure = _make_info_figure("Select a scattering detector first.")
                    model_figure = _make_info_figure("Select a scattering detector first.")
                    return CalibrationResult(
                        figure_store=calibration_figure.to_dict(),
                        model_figure_store=model_figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Missing scattering detector.",
                    ).to_tuple()

                resolved_medium_refractive_index = self._as_required_float(
                    medium_refractive_index,
                    "medium_refractive_index",
                )
                resolved_wavelength_nm = self._as_required_float(
                    wavelength_nm,
                    "wavelength_nm",
                )
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

                resolved_optical_power_watt = 1.0
                resolved_source_numerical_aperture = 0.1

                logger.debug(
                    "Resolved optical parameters medium_refractive_index=%r wavelength_nm=%r detector_numerical_aperture=%r detector_cache_numerical_aperture=%r detector_sampling=%r",
                    resolved_medium_refractive_index,
                    resolved_wavelength_nm,
                    resolved_detector_numerical_aperture,
                    resolved_detector_cache_numerical_aperture,
                    resolved_detector_sampling,
                )

                scattering_backend = BackEnd(
                    fcs_file_path=str(uploaded_fcs_path),
                    detector_column=str(detector_column),
                )

                if resolved_mie_model == "Core/Shell Sphere":
                    resolved_core_refractive_index = self._as_required_float(
                        core_refractive_index,
                        "core_refractive_index",
                    )
                    resolved_shell_refractive_index = self._as_required_float(
                        shell_refractive_index,
                        "shell_refractive_index",
                    )

                    parsed_core_shell_rows = self._parse_core_shell_rows_for_fit(
                        rows=current_table_rows,
                    )

                    logger.debug(
                        "Parsed core shell table rows row_count=%r row_indices=%r core_diameters_nm=%r shell_thicknesses_nm=%r outer_diameters_nm=%r measured_peak_positions=%r",
                        parsed_core_shell_rows["row_count"],
                        parsed_core_shell_rows["row_indices"],
                        parsed_core_shell_rows["core_diameters_nm"].tolist(),
                        parsed_core_shell_rows["shell_thicknesses_nm"].tolist(),
                        parsed_core_shell_rows["outer_diameters_nm"].tolist(),
                        parsed_core_shell_rows["measured_peak_positions"].tolist(),
                    )

                    if parsed_core_shell_rows["row_count"] < 2:
                        calibration_figure = _make_info_figure(
                            "Enter at least 2 valid core shell rows with measured peak positions."
                        )
                        model_figure = _make_info_figure(
                            "Enter at least 2 valid core shell rows with measured peak positions."
                        )
                        return CalibrationResult(
                            figure_store=calibration_figure.to_dict(),
                            model_figure_store=model_figure.to_dict(),
                            calibration_store=dash.no_update,
                            bead_table_data=dash.no_update,
                            apply_status="Need at least 2 valid core shell rows.",
                        ).to_tuple()

                    calibration_figure = _make_info_figure(
                        "Core/Shell Sphere coupling is not implemented yet in the scattering backend."
                    )
                    model_figure = self._build_core_shell_placeholder_figure(
                        measured_peak_positions=parsed_core_shell_rows["measured_peak_positions"],
                        outer_diameters_nm=parsed_core_shell_rows["outer_diameters_nm"],
                    )

                    return CalibrationResult(
                        figure_store=calibration_figure.to_dict(),
                        model_figure_store=model_figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=current_table_rows,
                        apply_status=(
                            f"Core/Shell rows parsed successfully with core RI={resolved_core_refractive_index:.6g} "
                            f"and shell RI={resolved_shell_refractive_index:.6g}, but expected coupling computation is not implemented yet."
                        ),
                    ).to_tuple()

                resolved_particle_refractive_index = self._as_required_float(
                    particle_refractive_index,
                    "particle_refractive_index",
                )

                parsed_sphere_rows = self._parse_sphere_rows_for_fit(
                    rows=current_table_rows,
                )

                logger.debug(
                    "Parsed sphere table rows row_count=%r row_indices=%r particle_diameters_nm=%r measured_peak_positions=%r",
                    parsed_sphere_rows["row_count"],
                    parsed_sphere_rows["row_indices"],
                    parsed_sphere_rows["particle_diameters_nm"].tolist(),
                    parsed_sphere_rows["measured_peak_positions"].tolist(),
                )

                if parsed_sphere_rows["row_count"] < 2:
                    calibration_figure = _make_info_figure(
                        "Enter at least 2 valid rows with particle diameter and measured peak position."
                    )
                    model_figure = _make_info_figure(
                        "Enter at least 2 valid rows with particle diameter and measured peak position."
                    )
                    return CalibrationResult(
                        figure_store=calibration_figure.to_dict(),
                        model_figure_store=model_figure.to_dict(),
                        calibration_store=dash.no_update,
                        bead_table_data=dash.no_update,
                        apply_status="Need at least 2 valid calibration rows.",
                    ).to_tuple()

                modeled_coupling_result = scattering_backend.compute_modeled_coupling_from_diameters(
                    particle_diameters_nm=parsed_sphere_rows["particle_diameters_nm"],
                    wavelength_nm=resolved_wavelength_nm,
                    source_numerical_aperture=resolved_source_numerical_aperture,
                    optical_power_watt=resolved_optical_power_watt,
                    detector_numerical_aperture=resolved_detector_numerical_aperture,
                    medium_refractive_index=resolved_medium_refractive_index,
                    particle_refractive_index=resolved_particle_refractive_index,
                    detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
                    detector_phi_offset_degree=0.0,
                    detector_gamma_offset_degree=0.0,
                    polarization_angle_degree=0.0,
                    detector_sampling=resolved_detector_sampling,
                )

                logger.debug(
                    "Modeled coupling values=%r",
                    modeled_coupling_result.expected_coupling_values.tolist(),
                )

                fit_result = scattering_backend.fit_measured_peak_positions_to_modeled_coupling(
                    measured_peak_positions=parsed_sphere_rows["measured_peak_positions"],
                    modeled_coupling_result=modeled_coupling_result,
                )

                logger.debug(
                    "Fit result slope=%r intercept=%r prefactor=%r r_squared=%r",
                    fit_result.slope,
                    fit_result.intercept,
                    fit_result.prefactor,
                    fit_result.r_squared,
                )

                calibration_figure = scattering_backend.build_calibration_figure(
                    fit_result=fit_result,
                )

                model_figure = self._build_model_comparison_figure(
                    measured_peak_positions=np.asarray(
                        parsed_sphere_rows["measured_peak_positions"],
                        dtype=float,
                    ),
                    expected_coupling_values=np.asarray(
                        fit_result.expected_coupling_values,
                        dtype=float,
                    ),
                    particle_diameters_nm=np.asarray(
                        parsed_sphere_rows["particle_diameters_nm"],
                        dtype=float,
                    ),
                )

                calibration_payload = scattering_backend.build_calibration_payload(
                    peak_detection_result=self._build_peak_detection_result_like_object(
                        peak_positions=np.asarray(parsed_sphere_rows["measured_peak_positions"], dtype=float),
                    ),
                    modeled_coupling_result=modeled_coupling_result,
                    fit_result=fit_result,
                    notes="",
                )

                calibration_payload["payload"]["parameters"].update(
                    {
                        "mie_model": resolved_mie_model,
                        "medium_refractive_index": resolved_medium_refractive_index,
                        "particle_refractive_index": resolved_particle_refractive_index,
                        "core_refractive_index": self._as_optional_float(core_refractive_index),
                        "shell_refractive_index": self._as_optional_float(shell_refractive_index),
                        "particle_diameter_nm": fit_result.particle_diameters_nm.tolist(),
                        "wavelength_nm": resolved_wavelength_nm,
                        "optical_power_watt": resolved_optical_power_watt,
                        "source_numerical_aperture": resolved_source_numerical_aperture,
                        "detector_numerical_aperture": resolved_detector_numerical_aperture,
                        "detector_cache_numerical_aperture": resolved_detector_cache_numerical_aperture,
                        "detector_sampling": resolved_detector_sampling,
                    }
                )

                updated_table_rows = self._write_expected_coupling_into_sphere_table(
                    rows=current_table_rows,
                    row_indices=parsed_sphere_rows["row_indices"],
                    expected_coupling_values=fit_result.expected_coupling_values,
                )

                logger.debug(
                    "Updated table rows after fit=%r",
                    updated_table_rows,
                )

                return CalibrationResult(
                    figure_store=calibration_figure.to_dict(),
                    model_figure_store=model_figure.to_dict(),
                    calibration_store=calibration_payload,
                    bead_table_data=updated_table_rows,
                    slope_out=f"{fit_result.slope:.6g}",
                    intercept_out=f"{fit_result.intercept:.6g} (A={fit_result.prefactor:.6g})",
                    r_squared_out=f"{fit_result.r_squared:.6g}",
                    apply_status="Scattering calibration fitted successfully.",
                ).to_tuple()

            except Exception as exc:
                logger.exception("Scattering calibration failed.")
                calibration_figure = _make_info_figure("Scattering calibration failed.")
                model_figure = _make_info_figure("Scattering calibration failed.")
                return CalibrationResult(
                    figure_store=calibration_figure.to_dict(),
                    model_figure_store=model_figure.to_dict(),
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
                return _make_info_figure("Fit a calibration first.")
            return go.Figure(stored_figure)

        @dash.callback(
            dash.Output(f"{self.page.ids.Calibration.graph_calibration}-model", "figure"),
            dash.Input(f"{self.page.ids.Calibration.graph_store}-model", "data"),
            prevent_initial_call=False,
        )
        def update_model_graph(stored_figure: Any) -> go.Figure:
            if not stored_figure:
                return _make_info_figure("Fit a calibration first.")
            return go.Figure(stored_figure)

    def _build_model_comparison_figure(
        self,
        *,
        measured_peak_positions: np.ndarray,
        expected_coupling_values: np.ndarray,
        particle_diameters_nm: np.ndarray,
    ) -> go.Figure:
        figure = go.Figure()

        hover_text = [
            f"Diameter: {float(diameter):.6g} nm"
            for diameter in particle_diameters_nm
        ]

        figure.add_trace(
            go.Scatter(
                x=measured_peak_positions,
                y=expected_coupling_values,
                mode="markers+text",
                text=[f"{float(diameter):.6g} nm" for diameter in particle_diameters_nm],
                textposition="top center",
                hovertext=hover_text,
                hoverinfo="x+y+text",
                name="Reference points",
            )
        )

        figure.update_layout(
            title="Measured peak vs expected coupling",
            xaxis_title="Measured peak position [a.u.]",
            yaxis_title="Expected coupling",
            separators=".,",
            hovermode="closest",
        )
        return figure

    def _build_core_shell_placeholder_figure(
        self,
        *,
        measured_peak_positions: np.ndarray,
        outer_diameters_nm: np.ndarray,
    ) -> go.Figure:
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=measured_peak_positions,
                y=outer_diameters_nm,
                mode="markers+text",
                text=[f"{float(value):.6g} nm" for value in outer_diameters_nm],
                textposition="top center",
                name="Parsed rows",
            )
        )

        figure.update_layout(
            title="Parsed core shell rows",
            xaxis_title="Measured peak position [a.u.]",
            yaxis_title="Outer diameter [nm]",
            separators=".,",
            hovermode="closest",
        )
        return figure

    def _resolve_mie_model(self, mie_model: Any) -> str:
        mie_model_string = "" if mie_model is None else str(mie_model).strip()
        return "Core/Shell Sphere" if mie_model_string == "Core/Shell Sphere" else "Solid Sphere"

    def _parse_sphere_rows_for_fit(
        self,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        row_indices: list[int] = []
        particle_diameters_nm: list[float] = []
        measured_peak_positions: list[float] = []

        for row_index, row in enumerate(rows or []):
            try:
                raw_particle_diameter_nm = row.get("particle_diameter_nm")
                raw_measured_peak_position = row.get("measured_peak_position")

                if raw_particle_diameter_nm in ("", None) or raw_measured_peak_position in ("", None):
                    continue

                particle_diameter_nm = float(raw_particle_diameter_nm)
                measured_peak_position = float(raw_measured_peak_position)
            except Exception:
                logger.debug("Skipping invalid sphere row row_index=%r row=%r", row_index, row)
                continue

            if particle_diameter_nm <= 0.0 or measured_peak_position <= 0.0:
                logger.debug(
                    "Skipping non-positive sphere row row_index=%r particle_diameter_nm=%r measured_peak_position=%r",
                    row_index,
                    particle_diameter_nm,
                    measured_peak_position,
                )
                continue

            row_indices.append(row_index)
            particle_diameters_nm.append(particle_diameter_nm)
            measured_peak_positions.append(measured_peak_position)

        return {
            "row_count": len(row_indices),
            "row_indices": row_indices,
            "particle_diameters_nm": np.asarray(particle_diameters_nm, dtype=float),
            "measured_peak_positions": np.asarray(measured_peak_positions, dtype=float),
        }

    def _parse_core_shell_rows_for_fit(
        self,
        *,
        rows: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        row_indices: list[int] = []
        core_diameters_nm: list[float] = []
        shell_thicknesses_nm: list[float] = []
        outer_diameters_nm: list[float] = []
        measured_peak_positions: list[float] = []

        for row_index, row in enumerate(rows or []):
            try:
                raw_core_diameter_nm = row.get("core_diameter_nm")
                raw_shell_thickness_nm = row.get("shell_thickness_nm")
                raw_measured_peak_position = row.get("measured_peak_position")

                if (
                    raw_core_diameter_nm in ("", None)
                    or raw_shell_thickness_nm in ("", None)
                    or raw_measured_peak_position in ("", None)
                ):
                    continue

                core_diameter_nm = float(raw_core_diameter_nm)
                shell_thickness_nm = float(raw_shell_thickness_nm)
                measured_peak_position = float(raw_measured_peak_position)
            except Exception:
                logger.debug("Skipping invalid core-shell row row_index=%r row=%r", row_index, row)
                continue

            if core_diameter_nm <= 0.0 or shell_thickness_nm < 0.0 or measured_peak_position <= 0.0:
                logger.debug(
                    "Skipping non-positive core-shell row row_index=%r core_diameter_nm=%r shell_thickness_nm=%r measured_peak_position=%r",
                    row_index,
                    core_diameter_nm,
                    shell_thickness_nm,
                    measured_peak_position,
                )
                continue

            outer_diameter_nm = core_diameter_nm + 2.0 * shell_thickness_nm

            row_indices.append(row_index)
            core_diameters_nm.append(core_diameter_nm)
            shell_thicknesses_nm.append(shell_thickness_nm)
            outer_diameters_nm.append(outer_diameter_nm)
            measured_peak_positions.append(measured_peak_position)

        return {
            "row_count": len(row_indices),
            "row_indices": row_indices,
            "core_diameters_nm": np.asarray(core_diameters_nm, dtype=float),
            "shell_thicknesses_nm": np.asarray(shell_thicknesses_nm, dtype=float),
            "outer_diameters_nm": np.asarray(outer_diameters_nm, dtype=float),
            "measured_peak_positions": np.asarray(measured_peak_positions, dtype=float),
        }

    def _write_expected_coupling_into_sphere_table(
        self,
        *,
        rows: list[dict[str, Any]],
        row_indices: list[int],
        expected_coupling_values: np.ndarray,
    ) -> list[dict[str, str]]:
        updated_rows = [dict(row) for row in rows]
        expected_coupling_values = np.asarray(expected_coupling_values, dtype=float).reshape(-1)

        logger.debug(
            "_write_expected_coupling_into_sphere_table called with row_indices=%r expected_coupling_values=%r",
            row_indices,
            expected_coupling_values.tolist(),
        )

        for row in updated_rows:
            row["expected_coupling"] = ""

        for row_index, expected_coupling_value in zip(
            row_indices,
            expected_coupling_values,
            strict=False,
        ):
            if row_index >= len(updated_rows):
                continue

            updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling_value):.6g}"

        return [
            {
                key: "" if value is None else str(value)
                for key, value in row.items()
            }
            for row in updated_rows
        ]

    def _build_peak_detection_result_like_object(self, peak_positions: np.ndarray):
        peak_positions = np.asarray(peak_positions, dtype=float)

        class PeakDetectionResultLike:
            def __init__(self, positions: np.ndarray) -> None:
                self.peak_positions = positions

        return PeakDetectionResultLike(peak_positions)

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

    def _as_optional_float(self, value: Any) -> Optional[float]:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except Exception:
            return None