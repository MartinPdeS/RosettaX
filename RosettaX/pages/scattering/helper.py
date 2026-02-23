class ScatterCalibrationIds:
    """
    Central registry of Dash component ids for the scatter calibration page.
    """

    page_name: str = "scatter_calibration"

    upload: str = "upload-data"
    flow_file_label: str = "flow-cytometry-data-file-output"

    flow_type_dropdown: str = "flow-cytometry-data-file-dropdown"

    fsc_dropdown: str = "forward-scatter-dropdown"
    fsc_wavelength: str = "forward-scatter-wavelength-nm"

    ssc_dropdown: str = "side-scatter-dropdown"
    ssc_wavelength: str = "side-scatter-wavelength-nm"

    green_fluorescence_dropdown: str = "green-fluorescence-dropdown"

    calibrate_flow_btn: str = "calibrate-flow-cytometry-button"

    mie_model: str = "mie-model-input"
    medium_index: str = "refractive-index-input"
    custom_medium_index: str = "custom-refractive-index-input"
    core_index: str = "particle-core-refractive-index-input"
    shell_index: str = "particle-shell-refractive-index-input"
    shell_thickness: str = "particle-shell-thickness-input"
    calibrate_example_btn: str = "calibrate-example-button"

    run_calibration_btn: str = "run-calibration-button"
    export_file_name: str = "file-name"
    save_export_btn: str = "save-export-calibration-button"

    interpolate_method: str = "interpolate-input"
    interpolate_au: str = "interpolate-au"
    interpolate_area: str = "interpolate-area"
    interpolate_btn: str = "interpolate-calibration-button"

    graph_1: str = f"graph-1-{page_name}"
    graph_2: str = f"graph-2-{page_name}"
    slope_out: str = "light-scattering-detector-output-slope"
    intercept_out: str = "light-scattering-detector-output-intercept"

    result_out: str = "calibration-result-output"

    debug_global_switch: str = f"{page_name}-debug-global-switch"
    debug_global_store: str = f"{page_name}-debug-global-store"


