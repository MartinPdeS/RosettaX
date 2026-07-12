# -*- coding: utf-8 -*-

page_name = "apply_calibration"


class Ids:
    class Page:
        location = f"{page_name}-location"

    class State:
        page_state_store = f"{page_name}-page-state-store"

    class Stores:
        selected_calibration_path_store = f"{page_name}-selected-calibration-path-store"
        selected_calibration_summary_store = f"{page_name}-selected-calibration-summary-store"
        uploaded_fcs_path_store = f"{page_name}-uploaded-fcs-path-store"

    class Header:
        container = f"{page_name}-header-container"

    class CalibrationPicker:
        upload = f"{page_name}-calibration-upload"
        upload_status = f"{page_name}-calibration-upload-status"

        scattering_target_model_container = (
            f"{page_name}-calibration-picker-scattering-target-model-container"
        )

        target_model_preset = (
            f"{page_name}-calibration-picker-target-model-preset"
        )

        target_model_details_container = (
            f"{page_name}-calibration-picker-target-model-details-container"
        )

        target_mie_relation_preview_container = (
            f"{page_name}-calibration-picker-target-mie-relation-preview-container"
        )

        target_monotonic_advanced_toggle = (
            f"{page_name}-calibration-picker-target-monotonic-advanced-toggle"
        )

        target_monotonic_advanced_container = (
            f"{page_name}-calibration-picker-target-monotonic-advanced-container"
        )

        target_monotonic_smoothing_toggle = (
            f"{page_name}-calibration-picker-target-monotonic-smoothing-toggle"
        )

        target_monotonic_smoothing_sigma_points = (
            f"{page_name}-calibration-picker-target-monotonic-smoothing-sigma-points"
        )

        target_solid_sphere_parameter_container = (
            f"{page_name}-calibration-picker-target-solid-sphere-parameter-container"
        )

        target_core_shell_parameter_container = (
            f"{page_name}-calibration-picker-target-core-shell-parameter-container"
        )

        target_mie_model = f"{page_name}-calibration-picker-target-mie-model"

        target_medium_refractive_index = (
            f"{page_name}-calibration-picker-target-medium-refractive-index"
        )

        target_particle_refractive_index = (
            f"{page_name}-calibration-picker-target-particle-refractive-index"
        )

        target_solid_sphere_diameter_min_nm = (
            f"{page_name}-calibration-picker-target-solid-sphere-diameter-min-nm"
        )

        target_solid_sphere_diameter_max_nm = (
            f"{page_name}-calibration-picker-target-solid-sphere-diameter-max-nm"
        )

        target_solid_sphere_diameter_count = (
            f"{page_name}-calibration-picker-target-solid-sphere-diameter-count"
        )

        target_core_refractive_index = (
            f"{page_name}-calibration-picker-target-core-refractive-index"
        )

        target_shell_refractive_index = (
            f"{page_name}-calibration-picker-target-shell-refractive-index"
        )

        target_shell_thickness_nm = (
            f"{page_name}-calibration-picker-target-shell-thickness-nm"
        )

        target_core_shell_core_diameter_min_nm = (
            f"{page_name}-calibration-picker-target-core-shell-core-diameter-min-nm"
        )

        target_core_shell_core_diameter_max_nm = (
            f"{page_name}-calibration-picker-target-core-shell-core-diameter-max-nm"
        )

        target_core_shell_core_diameter_count = (
            f"{page_name}-calibration-picker-target-core-shell-core-diameter-count"
        )

        target_mie_relation_axis_scale_toggle = (
            f"{page_name}-calibration-picker-target-mie-relation-axis-scale-toggle"
        )

        target_mie_relation_graph = (
            f"{page_name}-calibration-picker-target-mie-relation-graph"
        )

        target_mie_relation_status = (
            f"{page_name}-calibration-picker-target-mie-relation-status"
        )

        preview_container = f"{page_name}-calibration-picker-preview-container"
        preview_content = f"{page_name}-calibration-picker-preview-content"

    class FilePicker:
        upload = f"{page_name}-upload"
        upload_status = f"{page_name}-upload-status"
        column_consistency_alert = f"{page_name}-column-consistency-alert"
        preview_file = f"{page_name}-preview-file"
        preview_channel = f"{page_name}-preview-channel"
        preview_graph = f"{page_name}-preview-graph"
        preview_status = f"{page_name}-preview-status"

    class Export:
        download = f"{page_name}-download"
        report_download = f"{page_name}-report-download"
        apply_and_export_button = f"{page_name}-apply-and-export-button"
        generate_report_button = f"{page_name}-generate-report-button"
        status = f"{page_name}-status"
        export_button = f"{page_name}-export-button"
        export_columns_dropdown = f"{page_name}-export-columns-dropdown"
