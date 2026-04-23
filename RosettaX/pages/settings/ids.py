# -*- coding: utf-8 -*-


class Ids:
    """
    ID namespace for the settings page.

    IDs are grouped by UI section so ownership stays explicit and naming remains
    consistent across layout and callback definitions.
    """

    page_name = "settings"

    @classmethod
    def _build(cls, suffix: str) -> str:
        return f"{cls.page_name}-{suffix}"

    class Default:
        """
        IDs for the default values and profile editing section.
        """

        form_store = "settings-default-form-store"

        mie_model = "settings-mie-model"

        medium_refractive_index = "settings-medium-refractive-index"
        core_refractive_index = "settings-core-refractive-index"
        shell_refractive_index = "settings-shell-refractive-index"

        shell_thickness_nm = "settings-shell-thickness-nm"
        core_diameter_nm = "settings-core-diameter-nm"
        particle_diameter_nm = "settings-particle-diameter-nm"

        particle_refractive_index = "settings-particle-refractive-index"

        max_events_for_analysis = "settings-max-events-for-analysis"
        n_bins_for_plots = "settings-n-bins-for-plots"
        peak_count = "settings-peak-count"

        mesf_values = "settings-mesf-values"

        fluorescence_fcs_file_path = "settings-fluorescence-fcs-file-path"
        scattering_fcs_file_path = "settings-scattering-fcs-file-path"

        save_changes_button = "settings-save-changes-button"
        save_confirmation = "settings-save-confirmation"
        values_profile_dropdown = "settings-values-profile-dropdown"

        default_gating_channel = "settings-default-gating-channel"
        default_gating_threshold = "settings-default-gating-threshold"
        show_calibration_plot_by_default = "settings-show-calibration-plot-by-default"
        histogram_scale = "settings-histogram-scale"
        default_output_suffix = "settings-default-output-suffix"
        operator_name = "settings-operator-name"
        instrument_name = "settings-instrument-name"
        theme_mode = "settings-theme-mode"
        wavelength_nm = "settings-wavelength-nm"
        show_graphs = "settings-show-graphs"

        default_marker_size = "settings-default-marker-size"
        default_line_width = "settings-default-line-width"
        default_font_size = "settings-default-font-size"
        default_tick_size = "settings-default-tick-size"
        show_grid_by_default = "settings-show-grid-by-default"

    class NewProfile:
        """
        IDs for the new profile creation section.
        """

        new_profile_name = "settings-new-profile-name"
        save_new_profile_button = "settings-save-new-profile-button"
        new_profile_status = "settings-new-profile-status"

    class DeleteProfile:
        """
        IDs for the profile deletion section.
        """

        delete_profile_name = "settings-delete-profile-name"
        delete_profile_button = "settings-delete-profile-button"
        delete_profile_status = "settings-delete-profile-status"