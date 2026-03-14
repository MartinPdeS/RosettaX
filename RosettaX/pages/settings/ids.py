class Ids:
    """
    Id namespace for the fluorescent calibration page.

    This object groups ids by UI section to keep ownership clear and reduce clutter.
    """

    page_name = "settings"

    class Default:
        default_fluorescence_page_scattering_detector = "default-fluorescence-page-scattering-detector-input"
        default_fluorescence_page_fluorescence_detector = "default-fluorescence-page-fluorescence-detector-input"
        default_medium_index_input = "default-medium-index-input"
        default_core_index_input = "default-core-index-input"
        default_shell_index_input = "default-shell-index-input"
        default_shell_thickness_input = "default-shell-thickness-input"
        default_core_diameter_input = "default-core-diameter-input"
        default_particle_diameter_input = "default-particle-diameter-input"
        default_particle_index_input = "default-particle-index-input"
        default_max_events_for_analysis_input = "default-max_events-for-analysis-input"
        default_n_bins_for_plots_input = "default-n_bins-for-plots-input"
        default_peak_count_input = "default-peak-count-input"
        default_mesf_values_input = "default-mesf-values-input"
        save_changes_button = "default-save-changes-button"
        default_values_profile_dropdown = "default-values-profile-dropdown"

    class NewProfile:
        profile_name_input = "new-profile-name-input"
        save_new_profile_button = "save-new-profile-button"
        new_profile_status = "new-profile-status"
        new_profile_name_input = "new-profile-name-input"