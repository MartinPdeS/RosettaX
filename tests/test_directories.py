from pathlib import Path

import pytest

from RosettaX.utils import directories


class Test_Directories:
    def test_list_profiles_returns_json_stems_only(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "default_profile.json").write_text("{}", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
        (tmp_path / "nested").mkdir()

        monkeypatch.setattr(directories, "profiles", tmp_path)

        assert sorted(directories.list_profiles()) == ["default_profile"]

    @pytest.mark.parametrize(
        ("calibration_type", "directory_name", "expected_files"),
        [
            ("fluorescence", "fluorescence", ["alpha.json", "beta.json"]),
            ("scattering", "scattering", ["gamma.json"]),
        ],
    )
    def test_list_calibrations_reads_expected_directory(
        self,
        calibration_type: str,
        directory_name: str,
        expected_files: list[str],
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calibration_directory = tmp_path / directory_name
        calibration_directory.mkdir()

        for filename in expected_files:
            (calibration_directory / filename).write_text("{}", encoding="utf-8")
        (calibration_directory / "ignore.txt").write_text("skip", encoding="utf-8")

        monkeypatch.setattr(
            directories,
            f"{calibration_type}_calibration",
            calibration_directory,
        )

        assert sorted(directories.list_calibrations(calibration_type)) == expected_files

    def test_list_calibrations_rejects_unknown_type(self) -> None:
        with pytest.raises(ValueError, match="Invalid calibration type"):
            directories.list_calibrations("unknown")

    @pytest.mark.parametrize(
        ("system_name", "expected_command"),
        [
            ("Darwin", "open"),
            ("Linux", "xdg-open"),
        ],
    )
    def test_open_directory_uses_subprocess_on_supported_unix_platforms(
        self,
        system_name: str,
        expected_command: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        recorded_calls: list[tuple[list[str], bool]] = []

        def fake_run(command: list[str], check: bool) -> None:
            recorded_calls.append((command, check))

        monkeypatch.setattr(directories.platform, "system", lambda: system_name)
        monkeypatch.setattr(directories.subprocess, "run", fake_run)

        directories.open_directory(tmp_path)

        assert recorded_calls == [([expected_command, str(tmp_path.resolve())], True)]

    def test_open_directory_uses_os_startfile_on_windows(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        recorded_paths: list[str] = []

        monkeypatch.setattr(directories.platform, "system", lambda: "Windows")
        monkeypatch.setattr(
            directories.os,
            "startfile",
            lambda path: recorded_paths.append(path),
            raising=False,
        )

        directories.open_directory(tmp_path)

        assert recorded_paths == [str(tmp_path.resolve())]

    def test_open_directory_raises_for_missing_path(self, tmp_path: Path) -> None:
        missing_directory = tmp_path / "missing"

        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            directories.open_directory(missing_directory)

    def test_open_directory_raises_for_unsupported_platform(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(directories.platform, "system", lambda: "Plan9")

        with pytest.raises(RuntimeError, match="Unsupported operating system"):
            directories.open_directory(tmp_path)
