class Ids:
    """
    Id namespace for the fluorescent calibration page.

    This object groups ids by UI section to keep ownership clear and reduce clutter.
    """

    page_name = "fluorescent_calibration"

    class Load:
        fcs_path_store = f"fluorescent_calibration-initial-fcs-path-store"
        upload = f"fluorescent_calibration-upload-data"
        upload_filename = f"fluorescent_calibration-upload-file-name"
        upload_saved_as = f"fluorescent_calibration-upload-saved-as"
        uploaded_fcs_path_store = f"fluorescent_calibration-uploaded-fcs-path-store"
        max_events_for_plots_input = f"fluorescent_calibration-max-events-for-plots"

    class Scattering:
        detector_dropdown = f"fluorescent_calibration-scattering-detector-dropdown"
        nbins_input = f"fluorescent_calibration-scattering-nbins"
        find_threshold_btn = f"fluorescent_calibration-find-scattering-threshold-btn"
        threshold_input = f"fluorescent_calibration-scattering-threshold-input"
        threshold_store = f"fluorescent_calibration-scattering-threshold-store"
        yscale_switch = f"fluorescent_calibration-scattering-yscale-switch"
        graph_hist = f"fluorescent_calibration-graph-scattering-hist"

    class Fluorescence:
        detector_dropdown = f"fluorescent_calibration-fluorescence-detector-dropdown"
        nbins_input = f"fluorescent_calibration-fluorescence-nbins"
        peak_count_input = f"fluorescent_calibration-fluorescence-peak-count"
        find_peaks_btn = f"fluorescent_calibration-find-fluorescence-peaks-btn"
        yscale_switch = f"fluorescent_calibration-fluorescence-yscale-switch"
        source_channel_store = f"fluorescent_calibration-fluorescence-source-channel-store"
        graph_hist = f"fluorescent_calibration-graph-fluorescence-hist"
        hist_store = f"fluorescent_calibration-fluorescence-hist-store"
        peak_lines_store = f"fluorescent_calibration-fluorescence-peak-lines-store"

    class Calibration:
        bead_table = f"fluorescent_calibration-bead-spec-table"
        add_row_btn = f"fluorescent_calibration-add-row-btn"
        calibrate_btn = f"fluorescent_calibration-calibrate-btn"



        calibration_store = f"fluorescent_calibration-calibration-store"
        graph_calibration = f"fluorescent_calibration-graph-calibration"

        slope_out = f"fluorescent_calibration-slope-out"
        intercept_out = f"fluorescent_calibration-intercept-out"
        r_squared_out = f"fluorescent_calibration-r-squared-out"
        apply_status = f"fluorescent_calibration-apply-status"

    class Save:
        channel_name = f"fluorescent_calibration-channel-name"
        file_name = f"fluorescent_calibration-file-name"

        save_btn = f"fluorescent_calibration-save-btn"
        save_out = f"fluorescent_calibration-save-out"

        add_mesf_btn = f"fluorescent_calibration-add-mesf-btn"
        save_calibration_btn = f"fluorescent_calibration-save-calibration-btn"

        export_mode = f"fluorescent_calibration-export-mode"
        export_filename = f"fluorescent_calibration-export-filename"

        export_file_btn = f"fluorescent_calibration-export-file-btn"
        export_download = f"fluorescent_calibration-export-download"

    class Sidebar:
        sidebar_store = "apply-calibration-store"
        sidebar_content = "sidebar-content"