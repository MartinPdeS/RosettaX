# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc

from RosettaX.workflow import apply_calibration


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApplySectionResult:
    """
    Result container for the apply and export section callbacks.
    """

    status: Any = dash.no_update
    export_column_options: Any = dash.no_update
    export_column_values: Any = dash.no_update
    download_data: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert the result into callback output order.
        """
        return (
            self.status,
            self.export_column_options,
            self.export_column_values,
            self.download_data,
        )


class Apply:
    """
    Apply a saved calibration to uploaded FCS files and export calibrated files.

    This Dash section owns only the UI and callback wiring. The calibration
    application logic lives in ``RosettaX.workflow.apply_calibration``.
    """

    def __init__(
        self,
        page: Any,
    ) -> None:
        self.page = page

    def get_layout(self) -> dbc.Card:
        """
        Build the apply and export layout.
        """
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
            "3. Apply and export",
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_export_columns_section(),
                dash.html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._build_action_button_row(),
                dash.html.Div(
                    style={
                        "height": "10px",
                    },
                ),
                self._build_status_alert(),
                dcc.Download(
                    id=self.page.ids.Export.download,
                ),
            ]
        )

    def _build_export_columns_section(self) -> dash.html.Div:
        """
        Build the extra export columns selector.
        """
        return dash.html.Div(
            [
                dash.html.Div(
                    "Additional columns to export",
                    style={
                        "marginBottom": "6px",
                    },
                ),
                dash.dcc.Dropdown(
                    id=self.page.ids.Export.export_columns_dropdown,
                    options=[],
                    value=[],
                    multi=True,
                    placeholder="Select extra columns to export",
                    clearable=True,
                ),
                dash.html.Div(
                    style={
                        "height": "6px",
                    },
                ),
                dash.html.Small(
                    (
                        "The calibration source channel will always be included. "
                        "These extra columns will be exported unchanged."
                    ),
                    style={
                        "opacity": 0.75,
                    },
                ),
            ]
        )

    def _build_action_button_row(self) -> dash.html.Div:
        """
        Build the apply and export action row.
        """
        return dash.html.Div(
            [
                dbc.Button(
                    "Apply & export",
                    id=self.page.ids.Export.apply_and_export_button,
                    n_clicks=0,
                    color="primary",
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
            },
        )

    def _build_status_alert(self) -> dbc.Alert:
        """
        Build the status alert.
        """
        return dbc.Alert(
            "Status will appear here.",
            id=self.page.ids.Export.status,
            color="secondary",
            style={
                "marginBottom": "0px",
            },
        )

    def register_callbacks(self) -> None:
        """
        Register apply and export callbacks.
        """
        self._register_export_column_population_callback()
        self._register_apply_and_export_callback()

    def _register_export_column_population_callback(self) -> None:
        """
        Register extra export column dropdown population callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Export.export_columns_dropdown,
                "options",
            ),
            dash.Output(
                self.page.ids.Export.export_columns_dropdown,
                "value",
            ),
            dash.Input(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
            ),
            dash.State(
                self.page.ids.Export.export_columns_dropdown,
                "value",
            ),
            prevent_initial_call=False,
        )
        def populate_export_columns(
            uploaded_fcs_path: Any,
            current_export_columns: Any,
        ) -> tuple:
            logger.debug(
                "populate_export_columns called with uploaded_fcs_path=%r "
                "current_export_columns=%r",
                uploaded_fcs_path,
                current_export_columns,
            )

            first_uploaded_fcs_path = apply_calibration.io.resolve_first_uploaded_fcs_path(
                uploaded_fcs_path,
            )

            if not first_uploaded_fcs_path:
                logger.debug(
                    "No uploaded FCS path available. Returning empty export dropdown."
                )

                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            try:
                column_names = apply_calibration.io.get_fcs_column_names(
                    uploaded_fcs_path=first_uploaded_fcs_path,
                )

            except Exception:
                logger.exception(
                    "Failed to read column names from uploaded_fcs_path=%r",
                    first_uploaded_fcs_path,
                )

                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

            options = [
                {
                    "label": column_name,
                    "value": column_name,
                }
                for column_name in column_names
            ]

            allowed_values = {
                option["value"]
                for option in options
            }

            if isinstance(current_export_columns, list):
                resolved_values = [
                    str(value)
                    for value in current_export_columns
                    if str(value) in allowed_values
                ]

            else:
                resolved_values = []

            logger.debug(
                "Resolved export columns dropdown with option_count=%r values=%r",
                len(options),
                resolved_values,
            )

            return options, resolved_values

    def _register_apply_and_export_callback(self) -> None:
        """
        Register apply and export callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Export.status,
                "children",
            ),
            dash.Output(
                self.page.ids.Export.download,
                "data",
            ),
            dash.Input(
                self.page.ids.Export.apply_and_export_button,
                "n_clicks",
            ),
            dash.State(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.dropdown,
                "value",
            ),
            dash.State(
                self.page.ids.Export.export_columns_dropdown,
                "value",
            ),
            dash.State(
                self.page.ids.Stores.selected_calibration_summary_store,
                "data",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_mie_model,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_medium_refractive_index,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_particle_refractive_index,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_diameter_min_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_diameter_max_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_diameter_count,
                "value",
            ),
            prevent_initial_call=True,
        )
        def apply_and_export_calibration(
            n_clicks: int,
            uploaded_fcs_path: Any,
            selected_calibration: Any,
            export_columns: Any,
            selected_calibration_summary: Any,
            target_mie_model: Any,
            target_medium_refractive_index: Any,
            target_particle_refractive_index: Any,
            target_diameter_min_nm: Any,
            target_diameter_max_nm: Any,
            target_diameter_count: Any,
        ) -> tuple:
            logger.debug(
                "apply_and_export_calibration called with n_clicks=%r "
                "uploaded_fcs_path=%r selected_calibration=%r export_columns=%r "
                "selected_calibration_summary=%r target_mie_model=%r "
                "target_medium_refractive_index=%r target_particle_refractive_index=%r "
                "target_diameter_min_nm=%r target_diameter_max_nm=%r "
                "target_diameter_count=%r",
                n_clicks,
                uploaded_fcs_path,
                selected_calibration,
                export_columns,
                selected_calibration_summary,
                target_mie_model,
                target_medium_refractive_index,
                target_particle_refractive_index,
                target_diameter_min_nm,
                target_diameter_max_nm,
                target_diameter_count,
            )

            del n_clicks

            resolved_uploaded_fcs_paths = apply_calibration.io.resolve_uploaded_fcs_paths(
                uploaded_fcs_path,
            )

            if not resolved_uploaded_fcs_paths:
                return (
                    "Upload at least one input FCS file first.",
                    dash.no_update,
                )

            if not selected_calibration:
                return (
                    "Select a calibration first.",
                    dash.no_update,
                )

            try:
                resolved_export_columns = apply_calibration.io.normalize_export_columns(
                    export_columns,
                )

                scattering_target_model_parameters = self._build_scattering_target_model_parameters_if_required(
                    selected_calibration_summary=selected_calibration_summary,
                    target_mie_model=target_mie_model,
                    target_medium_refractive_index=target_medium_refractive_index,
                    target_particle_refractive_index=target_particle_refractive_index,
                    target_diameter_min_nm=target_diameter_min_nm,
                    target_diameter_max_nm=target_diameter_max_nm,
                    target_diameter_count=target_diameter_count,
                )

                request = apply_calibration.ApplyCalibrationRequest(
                    uploaded_fcs_paths=resolved_uploaded_fcs_paths,
                    selected_calibration=str(
                        selected_calibration,
                    ),
                    export_columns=resolved_export_columns,
                    scattering_target_model_parameters=scattering_target_model_parameters,
                )

                result = apply_calibration.apply_calibration_to_fcs_files(
                    request=request,
                )

            except Exception as exc:
                logger.exception(
                    "Failed to apply and export calibration for uploaded_fcs_path=%r "
                    "selected_calibration=%r",
                    uploaded_fcs_path,
                    selected_calibration,
                )

                return (
                    f"Failed to apply and export calibration: {type(exc).__name__}: {exc}",
                    dash.no_update,
                )

            logger.debug(
                "Calibration export succeeded with download_filename=%r "
                "file_count=%r source_channel=%r output_channels=%r warnings=%r",
                result.download_filename,
                result.file_count,
                result.source_channel,
                result.output_channels,
                result.warnings,
            )

            return (
                result.status,
                dcc.send_bytes(
                    result.payload_bytes,
                    result.download_filename,
                ),
            )

    @staticmethod
    def _build_scattering_target_model_parameters_if_required(
        *,
        selected_calibration_summary: Any,
        target_mie_model: Any,
        target_medium_refractive_index: Any,
        target_particle_refractive_index: Any,
        target_diameter_min_nm: Any,
        target_diameter_max_nm: Any,
        target_diameter_count: Any,
    ) -> Optional[apply_calibration.ScatteringTargetModelParameters]:
        """
        Build scattering target model parameters when the selected calibration requires them.
        """
        if not isinstance(
            selected_calibration_summary,
            dict,
        ):
            return None

        requires_target_model = bool(
            selected_calibration_summary.get(
                "requires_target_model",
                False,
            )
        )

        if not requires_target_model:
            return None

        return apply_calibration.ScatteringTargetModelParameters.from_raw_values(
            target_mie_model=target_mie_model,
            target_medium_refractive_index=target_medium_refractive_index,
            target_particle_refractive_index=target_particle_refractive_index,
            target_diameter_min_nm=target_diameter_min_nm,
            target_diameter_max_nm=target_diameter_max_nm,
            target_diameter_count=target_diameter_count,
        )