import logging
from dataclasses import dataclass
from typing import Any

import dash

from RosettaX.pages.p04_calibrate.state import ApplyCalibrationPageState
from RosettaX.workflow.apply_calibration import report as apply_report

from . import services
from .models import ApplyCalibrationControls

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
        self._register_report_button_state_callback()
        self._register_generate_report_callback()

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
            dash.Output(
                self.page.ids.State.page_state_store,
                "data",
                allow_duplicate=True,
            ),
            dash.Input(
                self.page.ids.Export.apply_and_export_button,
                "n_clicks",
            ),
            dash.State(
                self.page.ids.State.page_state_store,
                "data",
            ),
            dash.State(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
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
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_advanced_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_sigma_points,
                "value",
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
            page_state_data: Any,
            uploaded_fcs_path: Any,
            export_columns: Any,
            selected_calibration_summary: Any,
            target_model_preset: Any,
            advanced_monotonic_mode_enabled: Any,
            use_monotonic_smoothing_kernel: Any,
            monotonic_smoothing_sigma_points: Any,
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
            del n_clicks
            controls = ApplyCalibrationControls(
                uploaded_fcs_path=uploaded_fcs_path,
                export_columns=export_columns,
                selected_calibration_summary=selected_calibration_summary,
                target_model_preset=target_model_preset,
                advanced_monotonic_mode_enabled=advanced_monotonic_mode_enabled,
                use_monotonic_smoothing_kernel=use_monotonic_smoothing_kernel,
                monotonic_smoothing_sigma_points=monotonic_smoothing_sigma_points,
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
            result = services.apply_and_prepare_calibration_export(controls)
            page_state = ApplyCalibrationPageState.from_dict(page_state_data)
            download_data = (
                dash.dcc.send_bytes(result.payload_bytes, result.download_filename)
                if result.payload_bytes is not None
                else dash.no_update
            )
            return (
                result.status,
                download_data,
                page_state.update(
                    apply_result_payload=result.report_payload,
                    status_message=result.status,
                ).to_dict(),
            )

    def _register_report_button_state_callback(self) -> None:
        """
        Keep the report button enabled only for the current successful apply request.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Export.generate_report_button,
                "disabled",
            ),
            dash.Input(
                self.page.ids.State.page_state_store,
                "data",
            ),
            dash.State(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
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
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_advanced_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_sigma_points,
                "value",
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
            prevent_initial_call=False,
        )
        def sync_generate_report_button_disabled(
            page_state_data: Any,
            uploaded_fcs_path: Any,
            export_columns: Any,
            selected_calibration_summary: Any,
            target_model_preset: Any,
            advanced_monotonic_mode_enabled: Any,
            use_monotonic_smoothing_kernel: Any,
            monotonic_smoothing_sigma_points: Any,
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
        ) -> bool:
            page_state = ApplyCalibrationPageState.from_dict(
                page_state_data,
            )

            report_payload = page_state.apply_result_payload

            if not isinstance(report_payload, dict):
                return True

            try:
                request = services.build_apply_calibration_request(
                    uploaded_fcs_path=uploaded_fcs_path,
                    export_columns=export_columns,
                    selected_calibration_summary=selected_calibration_summary,
                    target_model_preset=target_model_preset,
                    advanced_monotonic_mode_enabled=advanced_monotonic_mode_enabled,
                    use_monotonic_smoothing_kernel=use_monotonic_smoothing_kernel,
                    monotonic_smoothing_sigma_points=monotonic_smoothing_sigma_points,
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
            except Exception:
                return True

            return not apply_report.apply_report_matches_request(
                report_payload=report_payload,
                request=request,
            )

    def _register_generate_report_callback(self) -> None:
        """
        Register the PDF report download callback.
        """

        @dash.callback(
            dash.Output(
                self.page.ids.Export.status,
                "children",
                allow_duplicate=True,
            ),
            dash.Output(
                self.page.ids.Export.report_download,
                "data",
            ),
            dash.Input(
                self.page.ids.Export.generate_report_button,
                "n_clicks",
            ),
            dash.State(
                self.page.ids.State.page_state_store,
                "data",
            ),
            dash.State(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
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
                self.page.ids.CalibrationPicker.target_model_preset,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_advanced_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_toggle,
                "value",
            ),
            dash.State(
                self.page.ids.CalibrationPicker.target_monotonic_smoothing_sigma_points,
                "value",
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
        def generate_report_pdf(
            n_clicks: int,
            page_state_data: Any,
            uploaded_fcs_path: Any,
            export_columns: Any,
            selected_calibration_summary: Any,
            target_model_preset: Any,
            advanced_monotonic_mode_enabled: Any,
            use_monotonic_smoothing_kernel: Any,
            monotonic_smoothing_sigma_points: Any,
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
            del n_clicks

            page_state = ApplyCalibrationPageState.from_dict(
                page_state_data,
            )
            report_payload = page_state.apply_result_payload

            if not isinstance(report_payload, dict):
                return (
                    "Run Apply & export successfully before generating a report PDF.",
                    dash.no_update,
                )

            try:
                request = services.build_apply_calibration_request(
                    uploaded_fcs_path=uploaded_fcs_path,
                    export_columns=export_columns,
                    selected_calibration_summary=selected_calibration_summary,
                    target_model_preset=target_model_preset,
                    advanced_monotonic_mode_enabled=advanced_monotonic_mode_enabled,
                    use_monotonic_smoothing_kernel=use_monotonic_smoothing_kernel,
                    monotonic_smoothing_sigma_points=monotonic_smoothing_sigma_points,
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
            except Exception:
                return (
                    "Run Apply & export again after changing inputs before generating the report.",
                    dash.no_update,
                )

            if not apply_report.apply_report_matches_request(
                report_payload=report_payload,
                request=request,
            ):
                return (
                    "Run Apply & export again to refresh the report for the current inputs.",
                    dash.no_update,
                )

            pdf_filename = apply_report.build_apply_report_download_filename(
                report_payload=report_payload,
            )
            pdf_bytes = apply_report.build_apply_report_pdf_bytes(
                report_payload=report_payload,
            )

            return (
                f"Generated report PDF: {pdf_filename}",
                dash.dcc.send_bytes(
                    pdf_bytes,
                    pdf_filename,
                ),
            )
