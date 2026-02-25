class Ids:
    page_name = "fluorescent_calibration"

    upload = f"{page_name}-upload-data"
    upload_filename = f"{page_name}-upload-file-name"
    upload_saved_as = f"{page_name}-upload-saved-as"

    max_events_for_plots_input = f"{page_name}-max-events-for-plots"
    upload = f"{page_name}-upload-data"
    upload_filename = f"{page_name}-upload-file-name"
    upload_saved_as = f"{page_name}-upload-saved-as"

    uploaded_fcs_path_store = f"{page_name}-uploaded-fcs-path-store"
    calibration_store = f"{page_name}-calibration-store"
    scattering_threshold_store = f"{page_name}-scattering-threshold-store"

    scattering_detector_dropdown = f"{page_name}-scattering-detector-dropdown"
    scattering_nbins_input = f"{page_name}-scattering-nbins"
    scattering_find_threshold_btn = f"{page_name}-find-scattering-threshold-btn"
    scattering_threshold_input = f"{page_name}-scattering-threshold-input"
    scattering_yscale_switch = f"{page_name}-scattering-yscale-switch"
    graph_scattering_hist = f"{page_name}-graph-scattering-hist"

    fluorescence_detector_dropdown = f"{page_name}-fluorescence-detector-dropdown"
    fluorescence_nbins_input = f"{page_name}-fluorescence-nbins"
    fluorescence_peak_count_input = f"{page_name}-fluorescence-peak-count"
    fluorescence_find_peaks_btn = f"{page_name}-find-fluorescence-peaks-btn"
    fluorescence_yscale_switch = f"{page_name}-fluorescence-yscale-switch"
    fluorescence_source_channel_store = f"{page_name}-fluorescence-source-channel-store"
    graph_fluorescence_hist = f"{page_name}-graph-fluorescence-hist"
    fluorescence_hist_store = f"{page_name}-fluorescence-hist-store"

    bead_table = f"{page_name}-bead-spec-table"
    add_row_btn = f"{page_name}-add-row-btn"
    calibrate_btn = f"{page_name}-calibrate-btn"

    graph_calibration = f"{page_name}-graph-calibration"
    slope_out = f"{page_name}-slope-out"
    intercept_out = f"{page_name}-intercept-out"
    r_squared_out = f"{page_name}-r-squared-out"

    apply_btn = f"{page_name}-apply-btn"

    channel_name = f"{page_name}-channel-name"
    file_name = f"{page_name}-file-name"

    save_btn = f"{page_name}-save-btn"
    save_out = f"{page_name}-save-out"

    export_mode = f"{page_name}-export-mode"
    export_filename = f"{page_name}-export-filename"

    sidebar_store = "apply-calibration-store"
    sidebar_content = "sidebar-content"

    add_mesf_btn = f"{page_name}-add-mesf-btn"
    save_calibration_btn = f"{page_name}-save-calibration-btn"
    export_file_btn = f"{page_name}-export-file-btn"

    export_download = f"{page_name}-export-download"

    upload_path_input = f"{page_name}-upload-path-input"
    upload_path_button = f"{page_name}-upload-path-button"

    fluorescence_peak_lines_store = f"{page_name}-fluorescence-peak-lines-store"

    apply_status = f"{page_name}-apply-status"

# class Ids:
#     page_name = "fluorescent_calibration"

#     def __getattr__(self, name: str) -> str:
#         return f"{self.page_name}-{name.replace('_', '-')}"