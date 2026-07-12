# -*- coding: utf-8 -*-

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import dash

from . import services


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FilePickerResult:
    """
    Container for the Dash outputs of the file upload callback.
    """

    uploaded_fcs_path_store: Any = dash.no_update
    alert_children: Any = dash.no_update
    alert_color: Any = dash.no_update
    alert_is_open: Any = dash.no_update

    def to_tuple(self) -> tuple:
        """
        Convert the result into callback output order.
        """
        return (
            self.uploaded_fcs_path_store,
            self.alert_children,
            self.alert_color,
            self.alert_is_open,
        )


class FilePickerCallbacks:
    """
    Callback registrar for the input FCS file picker section.
    """

    def __init__(
        self,
        *,
        page: Any,
        upload_directory: Path,
    ) -> None:
        self.page = page
        self.upload_directory = upload_directory

    def register_callbacks(self) -> None:
        """
        Register callbacks for the file picker.
        """
        logger.debug(
            "Registering FilePicker callbacks with upload_directory=%r",
            str(self.upload_directory),
        )

        services.validate_checks_contract()

        self._register_upload_callback()
        self._register_preview_control_sync_callback()
        self._register_preview_callbacks()

    def _register_upload_callback(self) -> None:
        """Register upload handling callback."""

        @dash.callback(
            dash.Output(
                self.page.ids.Stores.uploaded_fcs_path_store,
                "data",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "children",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "color",
            ),
            dash.Output(
                self.page.ids.FilePicker.column_consistency_alert,
                "is_open",
            ),
            dash.Input(
                self.page.ids.FilePicker.upload,
                "contents",
            ),
            dash.State(
                self.page.ids.FilePicker.upload,
                "filename",
            ),
            prevent_initial_call=True,
        )
        def handle_upload(
            contents_list: Optional[list[str]],
            filenames: Optional[list[str]],
        ) -> tuple:
            logger.debug(
                "handle_upload called with contents_count=%r filenames=%r",
                None if contents_list is None else len(contents_list),
                filenames,
            )

            if not contents_list or not filenames:
                logger.debug("Upload was cancelled or no files were provided.")

                return FilePickerResult(
                    uploaded_fcs_path_store=None,
                    alert_children=services.build_upload_prompt_text(),
                    alert_color="danger",
                    alert_is_open=True,
                ).to_tuple()

            try:
                services.validate_upload_payload(
                    contents_list=contents_list,
                    filenames=filenames,
                )

                saved_paths = services.save_uploaded_files(
                    upload_directory=self.upload_directory,
                    contents_list=contents_list,
                    filenames=filenames,
                )

                consistency_report = services.check_saved_files_consistency(
                    saved_paths=saved_paths,
                )

                alert_children, alert_color, alert_is_open = services.build_success_alert_payload(
                    saved_paths=saved_paths,
                    consistency_report=consistency_report,
                )

                logger.debug(
                    "Upload handling succeeded with saved_paths=%r alert_color=%r alert_is_open=%r",
                    [
                        str(path)
                        for path in saved_paths
                    ],
                    alert_color,
                    alert_is_open,
                )

                return FilePickerResult(
                    uploaded_fcs_path_store=[
                        str(path)
                        for path in saved_paths
                    ],
                    alert_children=alert_children,
                    alert_color=alert_color,
                    alert_is_open=alert_is_open,
                ).to_tuple()

            except Exception as exc:
                logger.exception(
                    "handle_upload failed for filenames=%r",
                    filenames,
                )

                return FilePickerResult(
                    alert_children=f"Upload failed: {type(exc).__name__}: {exc}",
                    alert_color="danger",
                    alert_is_open=True,
                ).to_tuple()

    def _register_preview_control_sync_callback(self) -> None:
        """Sync preview control defaults from the active runtime profile."""

        @dash.callback(
            dash.Output(self.page.ids.FilePicker.preview_axis_scale_toggle, "value"),
            dash.Output(self.page.ids.FilePicker.preview_nbins_input, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def sync_preview_controls(runtime_config_data: Any) -> tuple[list[str], str]:
            defaults = services.resolve_preview_control_defaults(runtime_config_data)
            axis_toggle_values = (
                defaults["x_log_values"] + defaults["y_log_values"]
            )
            return axis_toggle_values, str(defaults["n_bins_for_plots"])

    def _register_preview_callbacks(self) -> None:
        """Register uploaded-file selection and histogram preview callbacks."""

        @dash.callback(
            dash.Output(self.page.ids.FilePicker.preview_file, "options"),
            dash.Output(self.page.ids.FilePicker.preview_file, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Stores.selected_calibration_summary_store, "data"),
            dash.State(self.page.ids.FilePicker.preview_file, "value"),
            prevent_initial_call=False,
        )
        def sync_preview_file_options(
            uploaded_fcs_paths: Any,
            selected_calibration_summary: Any,
            current_file: Any,
        ) -> tuple[list[dict[str, str]], Optional[str]]:
            return services.build_preview_file_selection(
                uploaded_fcs_paths,
                current_value=current_file,
            )

        @dash.callback(
            dash.Output(self.page.ids.FilePicker.preview_channel, "options"),
            dash.Output(self.page.ids.FilePicker.preview_channel, "value"),
            dash.Input(self.page.ids.FilePicker.preview_file, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Stores.selected_calibration_summary_store, "data"),
            dash.State(self.page.ids.FilePicker.preview_channel, "value"),
            prevent_initial_call=False,
        )
        def sync_preview_channel_options(
            selected_file: Any,
            uploaded_fcs_paths: Any,
            selected_calibration_summary: Any,
            current_channel: Any,
        ) -> tuple[list[dict[str, str]], Optional[str]]:
            return services.build_preview_channel_selection(
                selected_file=selected_file,
                uploaded_fcs_paths=uploaded_fcs_paths,
                selected_calibration_summary=selected_calibration_summary,
                current_value=current_channel,
            )

        @dash.callback(
            dash.Output(self.page.ids.FilePicker.preview_event_count_input, "value"),
            dash.Output(self.page.ids.FilePicker.preview_graph, "figure"),
            dash.Output(self.page.ids.FilePicker.preview_graph, "style"),
            dash.Output(self.page.ids.FilePicker.preview_status, "children"),
            dash.Input(self.page.ids.FilePicker.preview_file, "value"),
            dash.Input(self.page.ids.FilePicker.preview_channel, "value"),
            dash.Input(self.page.ids.Stores.uploaded_fcs_path_store, "data"),
            dash.Input(self.page.ids.Stores.selected_calibration_summary_store, "data"),
            dash.Input(self.page.ids.FilePicker.preview_axis_scale_toggle, "value"),
            dash.Input(self.page.ids.FilePicker.preview_graph_visibility_toggle, "value"),
            dash.Input(self.page.ids.FilePicker.preview_nbins_input, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_mie_model, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_medium_refractive_index, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_particle_refractive_index, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_solid_sphere_diameter_min_nm, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_solid_sphere_diameter_max_nm, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_solid_sphere_diameter_count, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_core_refractive_index, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_shell_refractive_index, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_shell_thickness_nm, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_core_shell_core_diameter_min_nm, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_core_shell_core_diameter_max_nm, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_core_shell_core_diameter_count, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_model_preset, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_monotonic_advanced_toggle, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_monotonic_smoothing_toggle, "value"),
            dash.Input(self.page.ids.CalibrationPicker.target_monotonic_smoothing_sigma_points, "value"),
            dash.Input("runtime-config-store", "data"),
            prevent_initial_call=False,
        )
        def update_preview_histogram(
            selected_file: Any,
            selected_channel: Any,
            uploaded_fcs_paths: Any,
            selected_calibration_summary: Any,
            axis_scale_toggle_values: Any,
            preview_graph_visibility_toggle_values: Any,
            n_bins_for_plots: Any,
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
            target_model_preset: Any,
            advanced_monotonic_mode_enabled: Any,
            use_monotonic_smoothing_kernel: Any,
            monotonic_smoothing_sigma_points: Any,
            runtime_config_data: Any,
        ) -> tuple[str, Any, dict[str, str], str]:
            return services.build_preview_histogram_payload(
                selected_file=selected_file,
                selected_channel=selected_channel,
                uploaded_fcs_paths=uploaded_fcs_paths,
                selected_calibration_summary=selected_calibration_summary,
                runtime_config_data=runtime_config_data,
                axis_scale_toggle_values=axis_scale_toggle_values,
                preview_graph_visibility_toggle_values=preview_graph_visibility_toggle_values,
                n_bins_for_plots=n_bins_for_plots,
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
                target_model_preset=target_model_preset,
                advanced_monotonic_mode_enabled=advanced_monotonic_mode_enabled,
                use_monotonic_smoothing_kernel=use_monotonic_smoothing_kernel,
                monotonic_smoothing_sigma_points=monotonic_smoothing_sigma_points,
            )
