# -*- coding: utf-8 -*-


PAGE_NAME = "settings"


class Ids:
    """
    ID namespace for the settings page.

    IDs are grouped by UI section so ownership stays explicit and naming remains
    consistent across layout and callback definitions.
    """

    page_name = PAGE_NAME

    @classmethod
    def _build(cls, suffix: str) -> str:
        """
        Build a page scoped component ID.

        Parameters
        ----------
        suffix:
            Component ID suffix.

        Returns
        -------
        str
            Fully scoped component ID.
        """
        return f"{cls.page_name}-{suffix}"

    class State:
        """
        IDs for page level state stores.
        """

        page_state_store = f"{PAGE_NAME}-page-state-store"

    class Default:
        """
        IDs for the default values and profile editing section.

        Every field name here must match a field name in
        settings.sections.s01_default.schema.FIELD_DEFINITIONS.
        """

        values_profile_dropdown = f"{PAGE_NAME}-values-profile-dropdown"
        save_changes_button = f"{PAGE_NAME}-save-changes-button"
        save_confirmation = f"{PAGE_NAME}-save-confirmation"

        mesf_values = f"{PAGE_NAME}-mesf-values"
        peak_count = f"{PAGE_NAME}-peak-count"
        fluorescence_peak_table_sort_order = (
            f"{PAGE_NAME}-fluorescence-peak-table-sort-order"
        )

        histogram_scale = f"{PAGE_NAME}-histogram-scale"
        histogram_xscale = f"{PAGE_NAME}-histogram-xscale"
        histogram_yscale = f"{PAGE_NAME}-histogram-yscale"

        default_fluorescence_peak_process = (
            f"{PAGE_NAME}-default-fluorescence-peak-process"
        )

        default_scatterer_preset = f"{PAGE_NAME}-default-scatterer-preset"
        medium_refractive_index = f"{PAGE_NAME}-medium-refractive-index"
        core_refractive_index = f"{PAGE_NAME}-core-refractive-index"
        shell_refractive_index = f"{PAGE_NAME}-shell-refractive-index"
        particle_refractive_index = f"{PAGE_NAME}-particle-refractive-index"
        wavelength_nm = f"{PAGE_NAME}-wavelength-nm"

        shell_thickness_nm = f"{PAGE_NAME}-shell-thickness-nm"
        core_diameter_nm = f"{PAGE_NAME}-core-diameter-nm"
        particle_diameter_nm = f"{PAGE_NAME}-particle-diameter-nm"
        mie_model = f"{PAGE_NAME}-mie-model"

        default_scattering_peak_process = f"{PAGE_NAME}-default-scattering-peak-process"
        scattering_peak_table_sort_order = (
            f"{PAGE_NAME}-scattering-peak-table-sort-order"
        )
        default_gating_channel = f"{PAGE_NAME}-default-gating-channel"
        default_gating_threshold = f"{PAGE_NAME}-default-gating-threshold"
        default_apply_target_model_preset = (
            f"{PAGE_NAME}-default-apply-target-model-preset"
        )

        max_events_for_analysis = f"{PAGE_NAME}-max-events-for-analysis"
        n_bins = f"{PAGE_NAME}-n-bins-for-plots"
        show_calibration = f"{PAGE_NAME}-show-calibration-plot-by-default"
        default_output_suffix = f"{PAGE_NAME}-default-output-suffix"
        operator_name = f"{PAGE_NAME}-operator-name"
        instrument_name = f"{PAGE_NAME}-instrument-name"

        default_marker_size = f"{PAGE_NAME}-default-marker-size"
        default_line_width = f"{PAGE_NAME}-default-line-width"
        default_font_size = f"{PAGE_NAME}-default-font-size"
        default_tick_size = f"{PAGE_NAME}-default-tick-size"
        show_grid_by_default = f"{PAGE_NAME}-show-grid-by-default"

        fluorescence_fcs_file_path = f"{PAGE_NAME}-fluorescence-fcs-file-path"
        scattering_fcs_file_path = f"{PAGE_NAME}-scattering-fcs-file-path"
        theme_mode = f"{PAGE_NAME}-theme-mode"
        show_graphs = f"{PAGE_NAME}-show-graphs"
        target_mie_relation_xscale = f"{PAGE_NAME}-target-mie-relation-xscale"
        target_mie_relation_yscale = f"{PAGE_NAME}-target-mie-relation-yscale"
        graph_height = f"{PAGE_NAME}-graph-height"

    class NewProfile:
        """
        IDs for the new profile creation section.
        """

        new_profile_name = f"{PAGE_NAME}-new-profile-name"
        save_new_profile_button = f"{PAGE_NAME}-save-new-profile-button"
        new_profile_status = f"{PAGE_NAME}-new-profile-status"

    class DeleteProfile:
        """
        IDs for the profile deletion section.
        """

        delete_profile_name = f"{PAGE_NAME}-delete-profile-name"
        delete_profile_button = f"{PAGE_NAME}-delete-profile-button"
        delete_profile_status = f"{PAGE_NAME}-delete-profile-status"
