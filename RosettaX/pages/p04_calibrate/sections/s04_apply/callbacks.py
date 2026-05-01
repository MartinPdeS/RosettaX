# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any

import dash

from RosettaX.workflow import apply_calibration

from . import services


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


class ApplyCallbacks:
    """
    Callback registrar for the apply and export section.
    """

    def __init__(
        self,
        *,
        page: Any,
    ) -> None:
        self.page = page

    def register_callbacks(self) -> None:
        """
        Register apply and export callbacks.
        """
        logger.debug(
            "Registering Apply callbacks for page=%s",
            self.page.__class__.__name__,
        )

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

            try:
                options, resolved_values = services.build_export_column_options_and_values(
                    uploaded_fcs_path=uploaded_fcs_path,
                    current_export_columns=current_export_columns,
                )

            except Exception:
                logger.exception(
                    "Failed to populate export columns for uploaded_fcs_path=%r",
                    uploaded_fcs_path,
                )

                return ApplySectionResult(
                    export_column_options=[],
                    export_column_values=[],
                ).to_tuple()[1:3]

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

            try:
                request = services.build_apply_calibration_request(
                    uploaded_fcs_path=uploaded_fcs_path,
                    selected_calibration=selected_calibration,
                    export_columns=export_columns,
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