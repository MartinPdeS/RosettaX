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
        dropdown = f"{page_name}-calibration-dropdown"
        refresh_button = f"{page_name}-refresh-button"

        target_mie_relation_axis_scale_toggle = (
            f"{page_name}-calibration-picker-target-mie-relation-axis-scale-toggle"
        )

        scattering_target_model_container = (
            f"{page_name}-calibration-picker-scattering-target-model-container"
        )

        target_mie_model = f"{page_name}-calibration-picker-target-mie-model"
        target_medium_refractive_index = (
            f"{page_name}-calibration-picker-target-medium-refractive-index"
        )
        target_particle_refractive_index = (
            f"{page_name}-calibration-picker-target-particle-refractive-index"
        )
        target_core_refractive_index = (
            f"{page_name}-calibration-picker-target-core-refractive-index"
        )
        target_shell_refractive_index = (
            f"{page_name}-calibration-picker-target-shell-refractive-index"
        )

        target_diameter_min_nm = f"{page_name}-calibration-picker-target-diameter-min-nm"
        target_diameter_max_nm = f"{page_name}-calibration-picker-target-diameter-max-nm"
        target_diameter_count = f"{page_name}-calibration-picker-target-diameter-count"

        target_mie_relation_graph = (
            f"{page_name}-calibration-picker-target-mie-relation-graph"
        )
        target_mie_relation_status = (
            f"{page_name}-calibration-picker-target-mie-relation-status"
        )

    class FilePicker:
        upload = f"{page_name}-upload"
        upload_status = f"{page_name}-upload-status"
        column_consistency_alert = f"{page_name}-column-consistency-alert"

    class Export:
        download = f"{page_name}-download"
        apply_and_export_button = f"{page_name}-apply-and-export-button"
        status = f"{page_name}-status"
        export_button = f"{page_name}-export-button"
        export_columns_dropdown = f"{page_name}-export-columns-dropdown"