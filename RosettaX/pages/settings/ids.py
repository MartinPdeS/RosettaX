class Ids:
    """
    Id namespace for the fluorescent calibration page.

    This object groups ids by UI section to keep ownership clear and reduce clutter.
    """

    page_name = "settings"

    class Default:
        default_fluorescence_page_scattering_detector = "default_fluorescence_page_scattering_detector"
        default_fluorescence_page_fluorescence_detector = "default_fluorescence_page_fluorescence_detector"
        default_medium_index = "default_medium_index"
        default_core_index = "default_core_index"
        default_shell_index = "default_shell_index"
        default_shell_thickness = "default_shell_thickness"
        default_core_diameter = "default_core_diameter"
        default_particle_diameter_nm = "default_particle_diameter_nm"
        default_particle_index = "default_particle_index"
        default_max_events_for_analysis = "default_max_events_for_analysis"
        default_n_bins_for_plots = "default_n_bins_for_plots"
        default_peak_count = "default_peak_count"
        default_mesf_values = "default_mesf_values"
        default_save_changes_button = "default_save_changes_button"
        default_values_profile_dropdown = "default_values_profile_dropdown"

        default_fluorescence_show_fluorescence_controls = "default_fluorescence_show_fluorescence_controls"
        default_fluorescence_show_scattering_controls="default_fluorescence_show_scattering_controls"
        default_fluorescence_show_threshold_controls = "default_fluorescence_show_threshold_controls"
        default_fluorescence_debug_scattering = "default_fluorescence_debug_scattering"
        default_fluorescence_debug_fluorescence = "default_fluorescence_debug_fluorescence"
        default_fluorescence_debug_load = "default_fluorescence_debug_load"

        default_n_bins_for_plots = "default_n_bins_for_plots"
        default_fcs_file_path = "default_fcs_file_path"
        default_fluorescence_page_fluorescence_detector = "default_fluorescence_page_fluorescence_detector"

        default_shell_thickness_nm = "default_shell_thickness_nm"
        default_core_diameter_nm = "default_core_diameter_nm"

        default_debug = "default_debug"

        default_save_confirmation = "default_save_confirmation"

    class NewProfile:
        profile_name = "new_profile_name"
        save_new_profile_button = "save_new_profile_button"
        new_profile_status = "new_profile_status"
        new_profile_name = "new_profile_name"

    class DeleteProfile:
        delete_profile_name = "delete_profile_name"
        delete_profile_button = "delete_profile_button"
        delete_profile_status = "delete_profile_status"