import argparse
from RosettaX.pages.runtime_config import get_runtime_config

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    from RosettaX.pages.runtime_config import RuntimeConfig

    defaults = RuntimeConfig()
    defaults.apply_policy()

    parser = argparse.ArgumentParser(prog="RosettaX")

    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser tab on startup.",
    )

    # ----------------------------
    # Helpers
    # ----------------------------
    def _add_bool_toggle(*, name: str, dest: str, help_text: str) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            f"--{name}",
            dest=dest,
            action="store_true",
            default=argparse.SUPPRESS,
            help=f"{help_text} (set True)",
        )
        group.add_argument(
            f"--no_{name}",
            dest=dest,
            action="store_false",
            default=argparse.SUPPRESS,
            help=f"{help_text} (set False)",
        )

    # ----------------------------
    # Debug master switch
    # ----------------------------
    _add_bool_toggle(
        name="debug",
        dest="debug",
        help_text="Enable debug policy toggles",
    )

    # ----------------------------
    # Visibility toggles
    # ----------------------------
    _add_bool_toggle(
        name="show_scattering_controls",
        dest="show_scattering_controls",
        help_text="Show scattering controls",
    )
    _add_bool_toggle(
        name="show_threshold_controls",
        dest="show_threshold_controls",
        help_text="Show threshold controls",
    )
    _add_bool_toggle(
        name="show_fluorescence",
        dest="show_fluorescence",
        help_text="Show fluorescence section",
    )
    _add_bool_toggle(
        name="show_beads",
        dest="show_beads",
        help_text="Show beads section",
    )
    _add_bool_toggle(
        name="show_output",
        dest="show_output",
        help_text="Show output section",
    )
    _add_bool_toggle(
        name="show_save",
        dest="show_save",
        help_text="Show save section",
    )

    # ----------------------------
    # Per section debug
    # ----------------------------
    _add_bool_toggle(
        name="debug_scattering",
        dest="debug_scattering",
        help_text="Enable scattering debug outputs",
    )
    _add_bool_toggle(
        name="debug_fluorescence",
        dest="debug_fluorescence",
        help_text="Enable fluorescence debug outputs",
    )

    # ----------------------------
    # General analysis parameters
    # ----------------------------
    parser.add_argument(
        "--max_events_for_analysis",
        type=int,
        default=argparse.SUPPRESS,
        help=f"Max events used in analysis (default: {defaults.max_events_for_analysis})",
    )
    parser.add_argument(
        "--n_bins_for_plots",
        type=int,
        default=argparse.SUPPRESS,
        help=f"Histogram bin count (default: {defaults.n_bins_for_plots})",
    )
    parser.add_argument(
        "--default_peak_count",
        type=int,
        default=argparse.SUPPRESS,
        help=f"Default peak count (default: {defaults.default_peak_count})",
    )

    # ----------------------------
    # Mie defaults (optical properties)
    # ----------------------------
    parser.add_argument(
        "--default_particle_diameter_nm",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default particle diameter in nm (default: {defaults.default_particle_diameter_nm})",
    )
    parser.add_argument(
        "--default_particle_index",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default particle refractive index (default: {defaults.default_particle_index})",
    )
    parser.add_argument(
        "--default_medium_index",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default medium refractive index (default: {defaults.default_medium_index})",
    )
    parser.add_argument(
        "--default_core_index",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default core refractive index (default: {defaults.default_core_index})",
    )
    parser.add_argument(
        "--default_shell_index",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default shell refractive index (default: {defaults.default_shell_index})",
    )
    parser.add_argument(
        "--default_shell_thickness_nm",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default shell thickness in nm (default: {defaults.default_shell_thickness_nm})",
    )
    parser.add_argument(
        "--default_core_diameter_nm",
        type=float,
        default=argparse.SUPPRESS,
        help=f"Default core diameter in nm (default: {defaults.default_core_diameter_nm})",
    )

    parser.add_argument(
        "--fcs_file_path",
        type=str,
        default=argparse.SUPPRESS,
        help="Path to an FCS file to load on startup for the fluorescence page.",
    )

    parser.add_argument(
        "--fluorescence_page_scattering_detector",
        type=str,
        default=argparse.SUPPRESS,
        help="Default scattering detector channel name for the fluorescence page.",
    )

    parser.add_argument(
        "--fluorescence_page_fluorescence_detector",
        type=str,
        default=argparse.SUPPRESS,
        help="Default fluorescence detector channel name for the fluorescence page.",
    )

    return parser.parse_args(argv)


def apply_cli_to_runtime_config(args: argparse.Namespace) -> None:
    runtime_config = get_runtime_config()

    def _set_if_present(*, field_name: str, arg_name: str) -> None:
        if not hasattr(args, arg_name):
            return
        setattr(runtime_config, field_name, getattr(args, arg_name))
        runtime_config.mark_explicit(field_name)

    # Debug master switch
    _set_if_present(field_name="debug", arg_name="debug")

    # Visibility toggles
    _set_if_present(
        field_name="fluorescence_show_scattering_controls",
        arg_name="show_scattering_controls",
    )
    _set_if_present(
        field_name="fluorescence_show_threshold_controls",
        arg_name="show_threshold_controls",
    )
    _set_if_present(
        field_name="fluorescence_show_fluorescence_controls",
        arg_name="show_fluorescence",
    )
    _set_if_present(
        field_name="fluorescence_show_beads_controls",
        arg_name="show_beads",
    )
    _set_if_present(
        field_name="fluorescence_show_output_controls",
        arg_name="show_output",
    )
    _set_if_present(
        field_name="fluorescence_show_save_controls",
        arg_name="show_save",
    )

    # Per section debug
    _set_if_present(
        field_name="fluorescence_debug_scattering",
        arg_name="debug_scattering",
    )
    _set_if_present(
        field_name="fluorescence_debug_fluorescence",
        arg_name="debug_fluorescence",
    )

    _set_if_present(
        field_name="fcs_file_path",
        arg_name="fcs_file_path",
    )
    _set_if_present(
        field_name="fluorescence_page_scattering_detector",
        arg_name="fluorescence_page_scattering_detector",
    )
    _set_if_present(
        field_name="fluorescence_page_fluorescence_detector",
        arg_name="fluorescence_page_fluorescence_detector",
    )

    runtime_config.apply_policy()

    # General analysis parameters
    _set_if_present(field_name="max_events_for_analysis", arg_name="max_events_for_analysis")
    _set_if_present(field_name="n_bins_for_plots", arg_name="n_bins_for_plots")
    _set_if_present(field_name="default_peak_count", arg_name="default_peak_count")

    # Mie defaults (optical properties)
    _set_if_present(field_name="default_particle_diameter_nm", arg_name="default_particle_diameter_nm")
    _set_if_present(field_name="default_particle_index", arg_name="default_particle_index")
    _set_if_present(field_name="default_medium_index", arg_name="default_medium_index")
    _set_if_present(field_name="default_core_index", arg_name="default_core_index")
    _set_if_present(field_name="default_shell_index", arg_name="default_shell_index")
    _set_if_present(field_name="default_shell_thickness_nm", arg_name="default_shell_thickness_nm")
    _set_if_present(field_name="default_core_diameter_nm", arg_name="default_core_diameter_nm")

    runtime_config.apply_policy()