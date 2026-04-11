PAGE_NAME = "scattering_calibration"

class Ids:
    page_name = PAGE_NAME

    # Upload section
    class Upload:
        filename = f"{PAGE_NAME}-upload_filename"
        saved_as = f"{PAGE_NAME}-upload_saved_as"
        fcs_path_store = f"{PAGE_NAME}-uploaded_fcs_path_store"
        upload = f"{PAGE_NAME}-upload"
        filename_store = f"{PAGE_NAME}-filename_store"
        max_events_for_plots_input = f"{PAGE_NAME}-scattering_max_events_for_plots_input"

    # Parameters section
    class Parameters:
        mie_model_parameters_container = f"{PAGE_NAME}-mie_model_parameters_container"
        mie_model = f"{PAGE_NAME}-mie_model"
        particle_diameter = f"{PAGE_NAME}-particle_diameter"
        particle_index = f"{PAGE_NAME}-particle_index"
        medium_refractive_index = f"{PAGE_NAME}-medium_refractive_index"
        custom_medium_refractive_index = f"{PAGE_NAME}-custom_medium_refractive_index"
        core_refractive_index = f"{PAGE_NAME}-core_refractive_index"
        core_diameter = f"{PAGE_NAME}-core_diameter"
        shell_refractive_index = f"{PAGE_NAME}-shell_refractive_index"
        shell_thickness = f"{PAGE_NAME}-shell_thickness"
        particle_refractive_index_source = f"{PAGE_NAME}-particle-refractive-index-source"
        particle_refractive_index_custom = f"{PAGE_NAME}-particle-refractive-index-custom"
        core_refractive_index_source = f"{PAGE_NAME}-core-refractive-index-source"
        core_refractive_index_custom = f"{PAGE_NAME}-core-refractive-index-custom"
        medium_refractive_index_custom = f"{PAGE_NAME}-medium-refractive-index-custom"
        medium_refractive_index_source = f"{PAGE_NAME}-medium-refractive-index-source"
        shell_refractive_index_source = f"{PAGE_NAME}-shell-refractive-index-source"
        shell_refractive_index_custom = f"{PAGE_NAME}-shell-refractive-index-custom"
        collapse_example = f"{PAGE_NAME}-collapse_example"
        solid_sphere_container = f"{PAGE_NAME}-solid_sphere_container"
        core_shell_container = f"{PAGE_NAME}-core_shell_container"

    class Scattering:
        detector_dropdown = f"{PAGE_NAME}-scattering_detector_dropdown"
        debug_container = f"{PAGE_NAME}-scattering_debug_container"
        debug_switch = f"{PAGE_NAME}-scattering_debug_switch"
        nbins_input = f"{PAGE_NAME}-scattering_nbins_input"
        graph_hist = f"{PAGE_NAME}-scattering_graph_hist"
        yscale_switch = f"{PAGE_NAME}-scattering_yscale_switch"

    class Export:
        run_calibration_btn = f"{PAGE_NAME}-run_calibration_btn"
        file_name = f"{PAGE_NAME}-export_file_name"
        result_out = f"{PAGE_NAME}-result_out"
        save_export_btn = f"{PAGE_NAME}-save_export_btn"
        interpolate_method = f"{PAGE_NAME}-interpolate_method"
        interpolate_au = f"{PAGE_NAME}-interpolate_au"
        interpolate_area = f"{PAGE_NAME}-interpolate_area"
        interpolate_btn = f"{PAGE_NAME}-interpolate_btn"
        collapse = f"{PAGE_NAME}-collapse_export"

    class Calibration:
        calibration_store = f"{PAGE_NAME}-calibration_store"
        calibrate_example_btn = f"{PAGE_NAME}-calibrate_example_btn"

    class Save:
        channel_name = f"{PAGE_NAME}-channel-name"
        file_name = f"{PAGE_NAME}-file-name"
        save_btn = f"{PAGE_NAME}-save-btn"
        save_out = f"{PAGE_NAME}-save-out"
        add_mesf_btn = f"{PAGE_NAME}-add-mesf-btn"
        save_calibration_btn = f"{PAGE_NAME}-save-calibration-btn"
        export_mode = f"{PAGE_NAME}-export-mode"
        export_filename = f"{PAGE_NAME}-export-filename"
        export_file_btn = f"{PAGE_NAME}-export-file-btn"
        export_download = f"{PAGE_NAME}-export-download"

    class Sidebar:
        sidebar_store = f"{PAGE_NAME}-sidebar-store"
        sidebar_content = f"{PAGE_NAME}-sidebar-content"