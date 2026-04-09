class Ids:
    """
    Id namespace for the fluorescent calibration page.

    This object groups ids by UI section to keep ownership clear and reduce clutter.
    """

    page_name = "settings"

    class Default:
        medium_index = "medium_index"
        core_index = "core_index"
        shell_index = "shell_index"
        shell_thickness = "shell_thickness"
        core_diameter = "core_diameter"
        particle_diameter_nm = "particle_diameter_nm"
        particle_index = "particle_index"
        max_events_for_analysis = "max_events_for_analysis"
        n_bins_for_plots = "n_bins_for_plots"
        peak_count = "peak_count"
        mesf_values = "mesf_values"
        save_changes_button = "save_changes_button"
        values_profile_dropdown = "values_profile_dropdown"

        fluorescence_show_fluorescence_controls = "fluorescence_show_fluorescence_controls"
        fluorescence_show_scattering_controls="fluorescence_show_scattering_controls"
        fluorescence_show_threshold_controls = "fluorescence_show_threshold_controls"
        fluorescence_debug_scattering = "fluorescence_debug_scattering"
        fluorescence_debug_fluorescence = "fluorescence_debug_fluorescence"
        fluorescence_debug_load = "fluorescence_debug_load"

        n_bins_for_plots = "n_bins_for_plots"
        fcs_file_path = "fcs_file_path"

        shell_thickness_nm = "shell_thickness_nm"
        core_diameter_nm = "core_diameter_nm"

        debug = "debug"

        save_confirmation = "save_confirmation"

    class NewProfile:
        profile_name = "new_profile_name"
        save_new_profile_button = "save_new_profile_button"
        new_profile_status = "new_profile_status"
        new_profile_name = "new_profile_name"

    class DeleteProfile:
        delete_profile_name = "delete_profile_name"
        delete_profile_button = "delete_profile_button"
        delete_profile_status = "delete_profile_status"