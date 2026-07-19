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

        default_fluorescence_reference_preset = (
            f"{PAGE_NAME}-default-fluorescence-reference-preset"
        )
        mesf_values = f"{PAGE_NAME}-mesf-values"
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
        detector_configuration_preset = f"{PAGE_NAME}-detector-configuration-preset"
        medium_refractive_index = f"{PAGE_NAME}-medium-refractive-index"
        detector_numerical_aperture = f"{PAGE_NAME}-detector-numerical-aperture"
        detector_cache_numerical_aperture = f"{PAGE_NAME}-detector-cache-numerical-aperture"
        blocker_bar_numerical_aperture = f"{PAGE_NAME}-blocker-bar-numerical-aperture"
        detector_sampling = f"{PAGE_NAME}-detector-sampling"
        detector_phi_angle_degree = f"{PAGE_NAME}-detector-phi-angle-degree"
        detector_gamma_angle_degree = f"{PAGE_NAME}-detector-gamma-angle-degree"
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
        default_apply_target_model_preset = (
            f"{PAGE_NAME}-default-apply-target-model-preset"
        )

        max_events_for_analysis = f"{PAGE_NAME}-max-events-for-analysis"
        max_events_for_plots = f"{PAGE_NAME}-max-events-for-plots"
        n_bins = f"{PAGE_NAME}-n-bins-for-plots"
        operator_name = f"{PAGE_NAME}-operator-name"
        instrument_name = f"{PAGE_NAME}-instrument-name"

        default_marker_size = f"{PAGE_NAME}-default-marker-size"
        default_line_width = f"{PAGE_NAME}-default-line-width"
        default_font_size = f"{PAGE_NAME}-default-font-size"
        default_tick_size = f"{PAGE_NAME}-default-tick-size"
        show_grid_by_default = f"{PAGE_NAME}-show-grid-by-default"
        legend_vertical_anchor = f"{PAGE_NAME}-legend-vertical-anchor"
        annotation_text_position = f"{PAGE_NAME}-annotation-text-position"

        fluorescence_fcs_file_path = f"{PAGE_NAME}-fluorescence-fcs-file-path"
        scattering_fcs_file_path = f"{PAGE_NAME}-scattering-fcs-file-path"
        theme_mode = f"{PAGE_NAME}-theme-mode"
        show_graphs = f"{PAGE_NAME}-show-graphs"
        target_mie_relation_xscale = f"{PAGE_NAME}-target-mie-relation-xscale"
        target_mie_relation_yscale = f"{PAGE_NAME}-target-mie-relation-yscale"
        peak_graph_colormap_log = f"{PAGE_NAME}-peak-graph-colormap-log"
        graph_height = f"{PAGE_NAME}-graph-height"
        default_marker_opacity = f"{PAGE_NAME}-default-marker-opacity"
        show_preset_configuration = f"{PAGE_NAME}-show-preset-configuration"
        collapse_calibration_cards = f"{PAGE_NAME}-collapse-calibration-cards"

        @staticmethod
        def section_toggle_target(section_key: str) -> dict[str, str]:
            return {
                "type": f"{PAGE_NAME}-default-section-toggle-target",
                "section": str(section_key),
            }

        @staticmethod
        def section_collapse(section_key: str) -> dict[str, str]:
            return {
                "type": f"{PAGE_NAME}-default-section-collapse",
                "section": str(section_key),
            }

        @staticmethod
        def section_toggle_label(section_key: str) -> dict[str, str]:
            return {
                "type": f"{PAGE_NAME}-default-section-toggle-label",
                "section": str(section_key),
            }

    class NewProfile:
        """
        IDs for the new profile creation section.
        """

        new_profile_name = f"{PAGE_NAME}-new-profile-name"
        save_new_profile_button = f"{PAGE_NAME}-save-new-profile-button"
        new_profile_status = f"{PAGE_NAME}-new-profile-status"
        collapse = f"{PAGE_NAME}-new-profile-collapse"
        toggle_button = f"{PAGE_NAME}-new-profile-toggle-button"

    class DeleteProfile:
        """
        IDs for the profile deletion section.
        """

        delete_profile_name = f"{PAGE_NAME}-delete-profile-name"
        delete_profile_button = f"{PAGE_NAME}-delete-profile-button"
        delete_profile_status = f"{PAGE_NAME}-delete-profile-status"
        collapse = f"{PAGE_NAME}-delete-profile-collapse"
        toggle_button = f"{PAGE_NAME}-delete-profile-toggle-button"
