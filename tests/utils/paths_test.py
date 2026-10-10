"""Regression tests for utils paths."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import pytest

from RosettaX.utils.paths import resolve_profile_file_path
from RosettaX.workflow.apply_calibration.io import resolve_calibration_file_path


class Test_Paths:
    """Regression checks for paths."""

    def test_resolve_calibration_file_path_rejects_path_traversal(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """Check resolve calibration file path rejects path traversal."""
        monkeypatch.setattr(
            "RosettaX.utils.directories.fluorescence_calibration",
            tmp_path / "fluorescence",
        )
        monkeypatch.setattr(
            "RosettaX.utils.directories.scattering_calibration",
            tmp_path / "scattering",
        )

        with pytest.raises(ValueError, match="Invalid calibration file path"):
            resolve_calibration_file_path("fluorescence/../../secret.json")

    def test_resolve_profile_file_path_rejects_path_traversal(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
        """Check resolve profile file path rejects path traversal."""
        monkeypatch.setattr(
            "RosettaX.utils.directories.profiles",
            tmp_path / "profiles",
        )

        with pytest.raises(ValueError, match="Invalid profile file path"):
            resolve_profile_file_path("../../profile.json")
