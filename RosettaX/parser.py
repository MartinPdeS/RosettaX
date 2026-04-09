import argparse
from RosettaX.pages.runtime_config import RuntimeConfig

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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

    parser.add_argument(
        "--fcs_file_path",
        type=str,
        default=argparse.SUPPRESS,
        help="Path to an FCS file to load on startup for the fluorescence page.",
    )


    return parser.parse_args(argv)