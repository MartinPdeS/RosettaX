"""Regression tests for utils parser."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import pytest

from RosettaX import __version__
from RosettaX.utils.parser import _parse_args


class Test_Parser:
    """Regression checks for parser."""

    def test_parse_args_uses_expected_defaults(self) -> None:
        """Check parse args uses expected defaults."""
        parsed_arguments = _parse_args([])

        assert parsed_arguments.host == "127.0.0.1"
        assert parsed_arguments.port == 8050
        assert parsed_arguments.no_browser is False

    def test_parse_args_accepts_hyphenated_bool_toggle_names(self) -> None:
        """Check parse args accepts hyphenated bool toggle names."""
        parsed_arguments = _parse_args(
            [
                "--show-scattering-controls",
                "--no-debug-scattering",
            ]
        )

        assert parsed_arguments.show_scattering_controls is True
        assert parsed_arguments.debug_scattering is False

    def test_parse_args_preserves_underscore_toggle_names_for_backward_compatibility(self) -> None:
        """Check parse args preserves underscore toggle names for backward compatibility."""
        parsed_arguments = _parse_args(
            [
                "--show_scattering_controls",
                "--no_debug_scattering",
            ]
        )

        assert parsed_arguments.show_scattering_controls is True
        assert parsed_arguments.debug_scattering is False

    def test_parse_args_accepts_hyphenated_fcs_file_path_option(self) -> None:
        """Check parse args accepts hyphenated FCS file path option."""
        parsed_arguments = _parse_args(
            [
                "--fcs-file-path",
                "/tmp/example.fcs",
            ]
        )

        assert parsed_arguments.fcs_file_path == "/tmp/example.fcs"

    def test_parse_args_version_option_prints_package_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Check parse args version option prints package version."""
        with pytest.raises(SystemExit, match="0"):
            _parse_args(["--version"])

        captured = capsys.readouterr()

        assert captured.out.strip() == f"RosettaX {__version__}"
