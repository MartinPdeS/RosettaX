page_name = "scattering_calibration"

class Ids:

    # Upload section
    class Upload:
        filename = f"{page_name}-upload_filename"
        saved_as = f"{page_name}-upload_saved_as"
        fcs_path_store = f"{page_name}-uploaded_fcs_path_store"
        upload = f"{page_name}-upload"

    collapse_example = f"{page_name}-collapse_example"

    # Parameters section
    class Parameters:
        mie_model_parameters_container = f"{page_name}-mie_model_parameters_container"
        mie_model = f"{page_name}-mie_model"

        particle_diameter = f"{page_name}-particle_diameter"
        particle_index = f"{page_name}-particle_index"

        medium_index = f"{page_name}-medium_index"
        custom_medium_index = f"{page_name}-custom_medium_index"
        core_index = f"{page_name}-core_index"
        core_diameter = f"{page_name}-core_diameter"
        shell_index = f"{page_name}-shell_index"
        shell_thickness = f"{page_name}-shell_thickness"

        particle_index_source = f"{page_name}-particle-index-source"
        particle_index_custom = f"{page_name}-particle-index-custom"

        core_index_source = f"{page_name}-core-index-source"
        core_index_custom = f"{page_name}-core-index-custom"
        medium_index_custom = f"{page_name}-medium-index-custom"
        medium_index_source = f"{page_name}-medium-index-source"

        shell_index_source = f"{page_name}-shell-index-source"
        shell_index_custom = f"{page_name}-shell-index-custom"


    calibrate_example_btn = f"{page_name}-calibrate_example_btn"
    scattering_detector_dropdown = f"{page_name}-scattering_detector_dropdown"
    fluorescence_detector_dropdown = f"{page_name}-fluorescence_detector_dropdown"

    # Export section
    class Export:
        run_calibration_btn = f"{page_name}-run_calibration_btn"
        file_name = f"{page_name}-export_file_name"
        result_out = f"{page_name}-result_out"
        save_export_btn = f"{page_name}-save_export_btn"
        interpolate_method = f"{page_name}-interpolate_method"
        interpolate_au = f"{page_name}-interpolate_au"
        interpolate_area = f"{page_name}-interpolate_area"
        interpolate_btn = f"{page_name}-interpolate_btn"
        collapse = f"{page_name}-collapse_export"