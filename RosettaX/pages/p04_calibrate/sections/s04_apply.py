# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional
import logging

import dash
import dash_bootstrap_components as dbc

from RosettaX.utils import styling
from RosettaX.utils import ui_forms
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
        section_number: int,
        card_color: str = "green",
    ) -> None:
        self.page = page
        self.section_number = section_number
        self.card_color = card_color

        self.header_tooltip_target_id = f"{self.page.ids.Export.apply_and_export_button}-section-info-target"
        self.header_tooltip_id = f"{self.page.ids.Export.apply_and_export_button}-section-info-tooltip"

        self.export_columns_tooltip_target_id = f"{self.page.ids.Export.export_columns_dropdown}-info-target"
        self.export_columns_tooltip_id = f"{self.page.ids.Export.export_columns_dropdown}-info-tooltip"

        self.apply_button_tooltip_target_id = f"{self.page.ids.Export.apply_and_export_button}-info-target"
        self.apply_button_tooltip_id = f"{self.page.ids.Export.apply_and_export_button}-info-tooltip"

        logger.debug(
            "Initialized Apply section with page=%r",
            page,
        )

    def get_layout(self) -> dbc.Card:
        """
        Build the apply and export layout.
        """
        return dbc.Card(
            [
                self._build_header(),
                self._build_body(),
            ],
            style=ui_forms.build_workflow_section_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_header(self) -> dbc.CardHeader:
        """
        Build the section header.
        """
        return ui_forms.build_card_header_with_info(
            title=f"{self.section_number}. Apply and export",
            tooltip_target_id=self.header_tooltip_target_id,
            tooltip_id=self.header_tooltip_id,
            tooltip_text=(
                "Apply the selected calibration to the uploaded FCS files, "
                "choose optional extra channels to preserve, and export the "
                "calibrated output files."
            ),
            subtitle=(
                "Generate calibrated FCS outputs from the selected calibration "
                "and input files."
            ),
            color_name=self.card_color,
        )

    def _build_body(self) -> dbc.CardBody:
        """
        Build the section body.
        """
        return dbc.CardBody(
            [
                self._build_export_columns_panel(),
                dash.html.Div(
                    style={
                        "height": "18px",
                    },
                ),
                self._build_action_panel(),
                dash.html.Div(
                    style={
                        "height": "12px",
                    },
                ),
                self._build_status_alert(),
                dash.dcc.Download(
                    id=self.page.ids.Export.download,
                ),
            ],
            style=ui_forms.build_workflow_section_body_style(),
        )

    def _build_export_columns_panel(self) -> dbc.Card:
        """
        Build the extra export columns selector panel.
        """
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        ui_forms.build_title_with_info(
                            title="Export columns",
                            tooltip_target_id=self.export_columns_tooltip_target_id,
                            tooltip_id=self.export_columns_tooltip_id,
                            tooltip_text=(
                                "Select optional channels to preserve in the exported "
                                "files. The calibration source channel is always included."
                            ),
                            title_style_overrides={
                                "fontSize": "0.98rem",
                            },
                        ),
                        dash.html.Div(
                            "Choose additional raw channels to copy unchanged into the output files.",
                            style=ui_forms.build_workflow_section_subtitle_style(
                                font_size="0.84rem",
                            ),
                        ),
                    ],
                    style=ui_forms.build_workflow_subpanel_header_style(
                        color_name=self.card_color,
                    ),
                ),
                dbc.CardBody(
                    [
                        dash.dcc.Dropdown(
                            id=self.page.ids.Export.export_columns_dropdown,
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Select extra columns to export",
                            clearable=True,
                            persistence=True,
                            persistence_type="session",
                            style={
                                "width": "100%",
                            },
                        ),
                        dash.html.Div(
                            style={
                                "height": "8px",
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
                    ],
                    style=ui_forms.build_workflow_panel_body_style(),
                ),
            ],
            style=ui_forms.build_workflow_subpanel_card_style(
                color_name=self.card_color,
            ),
        )

    def _build_action_panel(self) -> dbc.Card:
        """
        Build the apply and export action panel.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    dash.html.Div(
                        [
                            dash.html.Div(
                                [
                                    dash.html.Div(
                                        "Calibration export",
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    dash.html.Div(
                                        (
                                            "Apply the selected calibration to every uploaded "
                                            "FCS file and package the calibrated outputs for download."
                                        ),
                                        style=ui_forms.build_workflow_section_subtitle_style(
                                            font_size="0.9rem",
                                            opacity=0.72,
                                            margin_top_px=2,
                                        ),
                                    ),
                                ],
                                style={
                                    "flex": "1 1 auto",
                                },
                            ),
                            dash.html.Div(
                                [
                                    dbc.Button(
                                        "Apply & export",
                                        id=self.page.ids.Export.apply_and_export_button,
                                        n_clicks=0,
                                        color="primary",
                                    ),
                                    ui_forms.build_info_badge(
                                        tooltip_target_id=self.apply_button_tooltip_target_id,
                                    ),
                                    dbc.Tooltip(
                                        (
                                            "Run the calibration on the uploaded FCS files "
                                            "and prepare the exported calibrated files for download."
                                        ),
                                        id=self.apply_button_tooltip_id,
                                        target=self.apply_button_tooltip_target_id,
                                        placement="right",
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "0px",
                                    "flex": "0 0 auto",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "gap": "16px",
                            "flexWrap": "wrap",
                        },
                    ),
                ],
                style={
                    "padding": "14px 16px",
                },
            ),
            style=ui_forms.build_workflow_panel_style(
                color_name=self.card_color,
                background=styling.build_rgba(
                    self.card_color,
                    0.04,
                ),
            ),
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
                "borderRadius": "10px",
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

            if isinstance(
                current_export_columns,
                list,
            ):
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
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_core_refractive_index,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_shell_refractive_index,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_shell_thickness_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count,
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
            target_solid_sphere_diameter_min_nm: Any,
            target_solid_sphere_diameter_max_nm: Any,
            target_solid_sphere_diameter_count: Any,
            target_core_refractive_index: Any,
            target_shell_refractive_index: Any,
            target_shell_thickness_nm: Any,
            target_core_shell_core_diameter_min_nm: Any,
            target_core_shell_core_diameter_max_nm: Any,
            target_core_shell_core_diameter_count: Any,
        ) -> tuple:
            logger.debug(
                "apply_and_export_calibration called with n_clicks=%r "
                "uploaded_fcs_path=%r selected_calibration=%r export_columns=%r "
                "selected_calibration_summary=%r target_mie_model=%r "
                "target_medium_refractive_index=%r target_particle_refractive_index=%r "
                "target_solid_sphere_diameter_min_nm=%r "
                "target_solid_sphere_diameter_max_nm=%r "
                "target_solid_sphere_diameter_count=%r "
                "target_core_refractive_index=%r target_shell_refractive_index=%r "
                "target_shell_thickness_nm=%r "
                "target_core_shell_core_diameter_min_nm=%r "
                "target_core_shell_core_diameter_max_nm=%r "
                "target_core_shell_core_diameter_count=%r",
                n_clicks,
                uploaded_fcs_path,
                selected_calibration,
                export_columns,
                selected_calibration_summary,
                target_mie_model,
                target_medium_refractive_index,
                target_particle_refractive_index,
                target_solid_sphere_diameter_min_nm,
                target_solid_sphere_diameter_max_nm,
                target_solid_sphere_diameter_count,
                target_core_refractive_index,
                target_shell_refractive_index,
                target_shell_thickness_nm,
                target_core_shell_core_diameter_min_nm,
                target_core_shell_core_diameter_max_nm,
                target_core_shell_core_diameter_count,
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
                    target_solid_sphere_diameter_min_nm=target_solid_sphere_diameter_min_nm,
                    target_solid_sphere_diameter_max_nm=target_solid_sphere_diameter_max_nm,
                    target_solid_sphere_diameter_count=target_solid_sphere_diameter_count,
                    target_core_refractive_index=target_core_refractive_index,
                    target_shell_refractive_index=target_shell_refractive_index,
                    target_shell_thickness_nm=target_shell_thickness_nm,
                    target_core_shell_core_diameter_min_nm=target_core_shell_core_diameter_min_nm,
                    target_core_shell_core_diameter_max_nm=target_core_shell_core_diameter_max_nm,
                    target_core_shell_core_diameter_count=target_core_shell_core_diameter_count,
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
                dash.dcc.send_bytes(
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
        target_solid_sphere_diameter_min_nm: Any,
        target_solid_sphere_diameter_max_nm: Any,
        target_solid_sphere_diameter_count: Any,
        target_core_refractive_index: Any,
        target_shell_refractive_index: Any,
        target_shell_thickness_nm: Any,
        target_core_shell_core_diameter_min_nm: Any,
        target_core_shell_core_diameter_max_nm: Any,
        target_core_shell_core_diameter_count: Any,
    ) -> Optional[apply_calibration.ScatteringTargetModelParameters]:
        """
        Build scattering target model parameters when the selected calibration requires them.
        """
        logger.debug(
            "_build_scattering_target_model_parameters_if_required called with "
            "selected_calibration_summary=%r target_mie_model=%r "
            "target_medium_refractive_index=%r target_particle_refractive_index=%r "
            "target_solid_sphere_diameter_min_nm=%r "
            "target_solid_sphere_diameter_max_nm=%r "
            "target_solid_sphere_diameter_count=%r "
            "target_core_refractive_index=%r target_shell_refractive_index=%r "
            "target_shell_thickness_nm=%r "
            "target_core_shell_core_diameter_min_nm=%r "
            "target_core_shell_core_diameter_max_nm=%r "
            "target_core_shell_core_diameter_count=%r",
            selected_calibration_summary,
            target_mie_model,
            target_medium_refractive_index,
            target_particle_refractive_index,
            target_solid_sphere_diameter_min_nm,
            target_solid_sphere_diameter_max_nm,
            target_solid_sphere_diameter_count,
            target_core_refractive_index,
            target_shell_refractive_index,
            target_shell_thickness_nm,
            target_core_shell_core_diameter_min_nm,
            target_core_shell_core_diameter_max_nm,
            target_core_shell_core_diameter_count,
        )

        if not isinstance(
            selected_calibration_summary,
            dict,
        ):
            logger.debug(
                "No scattering target model parameters required because selected_calibration_summary is not a dict."
            )
            return None

        requires_target_model = bool(
            selected_calibration_summary.get(
                "requires_target_model",
                False,
            )
        )

        if not requires_target_model:
            logger.debug(
                "No scattering target model parameters required because requires_target_model=False."
            )
            return None

        resolved_target_mie_model = Apply._resolve_target_mie_model(
            target_mie_model,
        )

        is_core_shell_model = resolved_target_mie_model == "Core/Shell Sphere"

        if is_core_shell_model:
            resolved_target_diameter_min_nm = target_core_shell_core_diameter_min_nm
            resolved_target_diameter_max_nm = target_core_shell_core_diameter_max_nm
            resolved_target_diameter_count = target_core_shell_core_diameter_count

        else:
            resolved_target_diameter_min_nm = target_solid_sphere_diameter_min_nm
            resolved_target_diameter_max_nm = target_solid_sphere_diameter_max_nm
            resolved_target_diameter_count = target_solid_sphere_diameter_count

        logger.debug(
            "Resolved scattering target diameter controls for mie_model=%r "
            "diameter_min_nm=%r diameter_max_nm=%r diameter_count=%r",
            resolved_target_mie_model,
            resolved_target_diameter_min_nm,
            resolved_target_diameter_max_nm,
            resolved_target_diameter_count,
        )

        target_model_parameters = apply_calibration.ScatteringTargetModelParameters.from_raw_values(
            target_mie_model=resolved_target_mie_model,
            target_medium_refractive_index=target_medium_refractive_index,
            target_particle_refractive_index=target_particle_refractive_index,
            target_core_refractive_index=target_core_refractive_index,
            target_shell_refractive_index=target_shell_refractive_index,
            target_shell_thickness_nm=target_shell_thickness_nm,
            target_diameter_min_nm=resolved_target_diameter_min_nm,
            target_diameter_max_nm=resolved_target_diameter_max_nm,
            target_diameter_count=resolved_target_diameter_count,
        )

        logger.debug(
            "Built scattering target model parameters=%r",
            target_model_parameters,
        )

        return target_model_parameters

    @staticmethod
    def _resolve_target_mie_model(
        target_mie_model: Any,
    ) -> str:
        """
        Normalize the target Mie model value.
        """
        target_mie_model_string = str(
            target_mie_model or "Solid Sphere",
        ).strip()

        normalized_target_mie_model = target_mie_model_string.lower()

        if normalized_target_mie_model in {
            "core/shell sphere",
            "core shell sphere",
            "core-shell sphere",
            "coreshell sphere",
            "core_shell_sphere",
        }:
            return "Core/Shell Sphere"

        return "Solid Sphere"