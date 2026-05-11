# -*- coding: utf-8 -*-

import pytest

from RosettaX.utils.paths import resolve_profile_file_path
from RosettaX.workflow.apply_calibration.io import resolve_calibration_file_path


class Test_Paths:
    def test_resolve_calibration_file_path_rejects_path_traversal(
        self,
        tmp_path,
        monkeypatch,
    ) -> None:
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
        monkeypatch.setattr(
            "RosettaX.utils.directories.profiles",
            tmp_path / "profiles",
        )

        with pytest.raises(ValueError, match="Invalid profile file path"):
            resolve_profile_file_path("../../profile.json")
