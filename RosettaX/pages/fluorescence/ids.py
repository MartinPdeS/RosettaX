PAGE_NAME = "fluorescent_calibration"


class Ids:
    page_name = PAGE_NAME

    class Load:
        fcs_path_store = f"{PAGE_NAME}-initial-fcs-path-store"
        upload = f"{PAGE_NAME}-upload-data"
        upload_filename = f"{PAGE_NAME}-upload-file-name"
        upload_saved_as = f"{PAGE_NAME}-upload-saved-as"
        uploaded_fcs_path_store = f"{PAGE_NAME}-uploaded-fcs-path-store"
        max_events_for_plots_input = f"{PAGE_NAME}-max-events-for-plots"
        upload_filename_store = f"{PAGE_NAME}-upload-filename-store"

    class Scattering:
        detector_dropdown = f"{PAGE_NAME}-scattering-detector-dropdown"
        nbins_input = f"{PAGE_NAME}-scattering-nbins"
        find_threshold_btn = f"{PAGE_NAME}-find-scattering-threshold-btn"
        threshold_input = f"{PAGE_NAME}-scattering-threshold-input"
        threshold_store = f"{PAGE_NAME}-scattering-threshold-store"
        yscale_switch = f"{PAGE_NAME}-scattering-yscale-switch"
        graph_hist = f"{PAGE_NAME}-graph-scattering-hist"
        debug_switch = f"{PAGE_NAME}-debug-switch"
        debug_store = f"{PAGE_NAME}-debug-store"
        debug_container = f"{PAGE_NAME}-debug-container"

    class Fluorescence:
        detector_dropdown = f"{PAGE_NAME}-fluorescence-detector-dropdown"
        nbins_input = f"{PAGE_NAME}-fluorescence-nbins"
        peak_count_input = f"{PAGE_NAME}-fluorescence-peak-count"
        find_peaks_btn = f"{PAGE_NAME}-find-fluorescence-peaks-btn"
        yscale_switch = f"{PAGE_NAME}-fluorescence-yscale-switch"
        source_channel_store = f"{PAGE_NAME}-fluorescence-source-channel-store"
        graph_hist = f"{PAGE_NAME}-graph-fluorescence-hist"
        hist_store = f"{PAGE_NAME}-fluorescence-hist-store"
        peak_lines_store = f"{PAGE_NAME}-fluorescence-peak-lines-store"
        graph_toggle_switch = f"{PAGE_NAME}-fluorescence-graph-toggle-switch"
        graph_toggle_container = f"{PAGE_NAME}-fluorescence-graph-toggle-container"
        graph_toggle_store = f"{PAGE_NAME}-fluorescence-graph-toggle-store"

    class Calibration:
        bead_table = f"{PAGE_NAME}-bead-spec-table"
        add_row_btn = f"{PAGE_NAME}-add-row-btn"
        calibrate_btn = f"{PAGE_NAME}-calibrate-btn"
        calibration_store = f"{PAGE_NAME}-calibration-store"
        graph_calibration = f"{PAGE_NAME}-graph-calibration"
        slope_out = f"{PAGE_NAME}-slope-out"
        intercept_out = f"{PAGE_NAME}-intercept-out"
        r_squared_out = f"{PAGE_NAME}-r-squared-out"
        apply_status = f"{PAGE_NAME}-apply-status"
        graph_toggle_switch = f"{PAGE_NAME}-graph-toggle-switch"
        graph_toggle_container = f"{PAGE_NAME}-graph-toggle-container"
        graph_store = f"{PAGE_NAME}-graph-store"

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
