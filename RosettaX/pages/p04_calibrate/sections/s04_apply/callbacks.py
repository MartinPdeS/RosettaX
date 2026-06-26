# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from typing import Any

import dash

from RosettaX.pages.p04_calibrate.state import ApplyCalibrationPageState
from RosettaX.workflow import apply_calibration
from RosettaX.workflow.apply_calibration import io as apply_calibration_io
from RosettaX.workflow.apply_calibration import report as apply_report
from RosettaX.utils import usage_metrics

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
                "page_state_data=%r "
                "uploaded_fcs_path=%r export_columns=%r "
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
                page_state_data,
                uploaded_fcs_path,
                export_columns,
                selected_calibration_summary,
                target_model_preset,
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
                usage_metrics.record_apply_button_click()
            except Exception:
                logger.exception("Failed to record apply button click usage metric.")

            page_state = ApplyCalibrationPageState.from_dict(
                page_state_data,
            )

            try:
                request = services.build_apply_calibration_request(
                    uploaded_fcs_path=uploaded_fcs_path,
                    export_columns=export_columns,
                    selected_calibration_summary=selected_calibration_summary,
                    target_model_preset=target_model_preset,
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
                error_message = (
                    f"Failed to apply and export calibration: {type(exc).__name__}: {exc}"
                )

                logger.exception(
                    "Failed to apply and export calibration for uploaded_fcs_path=%r",
                    uploaded_fcs_path,
                )

                return (
                    error_message,
                    dash.no_update,
                    page_state.update(
                        apply_result_payload=None,
                        status_message=error_message,
                    ).to_dict(),
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

            try:
                usage_metrics.record_calibrated_files(
                    file_count=result.file_count,
                )
            except Exception:
                logger.exception(
                    "Failed to record calibrated file usage metric for file_count=%r",
                    result.file_count,
                )

            status_message = result.status
            download_bytes = result.payload_bytes
            report_payload = None
            report_pdf_filename = None
            report_pdf_bytes = None

            try:
                report_payload = apply_report.build_apply_report_payload(
                    request=request,
                    result=result,
                    calibration_summary=selected_calibration_summary,
                )
                report_pdf_filename = apply_report.build_apply_report_download_filename(
                    report_payload=report_payload,
                )
                report_pdf_bytes = apply_report.build_apply_report_pdf_bytes(
                    report_payload=report_payload,
                )
            except Exception as exc:
                logger.exception(
                    "Failed to build apply report for download_filename=%r",
                    result.download_filename,
                )
                status_message = (
                    f"{result.status} Report generation failed: {type(exc).__name__}: {exc}"
                )

            if (
                report_pdf_filename is not None
                and report_pdf_bytes is not None
                and str(result.download_filename).lower().endswith(".zip")
            ):
                try:
                    download_bytes = apply_calibration_io.append_files_to_zip_bytes(
                        zip_bytes=result.payload_bytes,
                        extra_files={
                            report_pdf_filename: report_pdf_bytes,
                        },
                    )
                    status_message = (
                        f"{result.status} Bundled report PDF into ZIP export."
                    )
                except Exception as exc:
                    logger.exception(
                        "Failed to bundle report PDF into ZIP download_filename=%r",
                        result.download_filename,
                    )
                    status_message = (
                        f"{result.status} Report PDF is available separately, but ZIP bundling failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

            return (
                status_message,
                dash.dcc.send_bytes(
                    download_bytes,
                    result.download_filename,
                ),
                page_state.update(
                    apply_result_payload=report_payload,
                    status_message=status_message,
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