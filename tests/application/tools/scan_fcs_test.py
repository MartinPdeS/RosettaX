"""Exercise cross-device review lookup through the maintainer CLI."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import importlib.util
import json
import pytest
import shutil
import subprocess
import sys
from pathlib import Path
from RosettaX.workflow import validation_recordings

ROOT = Path(__file__).resolve().parents[3]


def test_scan_uses_file_contents_for_review_status(*, tmp_path):
    """Recognize a renamed recording and reject different bytes under a reviewed name."""
    fixture = ROOT / "RosettaX/assets/sample-files/cross_device/sony_id7000_experiment_2_beads.fcs"
    shutil.copyfile(fixture, tmp_path / "renamed.FCS")
    (tmp_path / fixture.name).write_bytes(b"unreviewed contents")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/scan_fcs.py"), "--check", str(tmp_path)],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert f"REVIEWED   {tmp_path / 'renamed.FCS'}  Sony ID7000" in result.stdout
    assert f"UNREVIEWED {tmp_path / fixture.name}" in result.stdout


def test_registration_rolls_back_and_can_be_retried(*, tmp_path, monkeypatch):
    """A failed README update preserves the inventory and releases the registration lock."""
    specification = importlib.util.spec_from_file_location("scan_fcs", ROOT / "tools/scan_fcs.py")
    scanner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(scanner)
    samples = tmp_path / "samples"
    destination = samples / "cross_device"
    destination.mkdir(parents=True)
    registry = samples / "sample_file_metadata.json"
    registry.write_text("{}")
    source = tmp_path / "example.fcs"
    source.write_bytes(b"fixture contents")
    record = {"sha256": scanner.file_digest(path=source), "manufacturer": "Sony", "model": "ID7000"}
    monkeypatch.setattr(scanner, "ROOT", tmp_path)
    monkeypatch.setattr(scanner, "SAMPLE_DIRECTORY", samples)
    monkeypatch.setattr(validation_recordings, "SAMPLE_DIRECTORY", samples)
    readme = tmp_path / "README.rst"
    readme.write_text("unmarked README")
    with pytest.raises(ValueError, match="marker pair"):
        scanner.register_recording(source=source, record=record, columns=["SSC-H"])
    assert registry.read_text() == "{}"
    assert not (destination / source.name).exists()

    readme.write_text(".. supported-cytometers-start\n.. supported-cytometers-end\n")
    scanner.register_recording(source=source, record=record, columns=["SSC-H"])
    assert json.loads(registry.read_text())["cross_device/example.fcs"]["validation"] == record
    assert (destination / source.name).read_bytes() == source.read_bytes()
    assert "ID7000" in readme.read_text()


def test_check_all_reports_observations_on_one_line_per_recording(*, monkeypatch, capsys, tmp_path):
    """Keep partial assignments, numeric fit quality, and failures from either check."""
    specification = importlib.util.spec_from_file_location("scan_fcs", ROOT / "tools/scan_fcs.py")
    scanner = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(scanner)

    def run_fixture_suite(command, **kwargs):
        report_path = next(value.split("=", 1)[1] for value in command if value.startswith("--junitxml="))
        Path(report_path).write_text("""<testsuite>
          <testcase><properties><property name="recording" value="beads.fcs"/></properties></testcase>
          <testcase><properties><property name="recording" value="beads.fcs"/>
            <property name="model" value="Sony ID7000"/><property name="scatter" value="SSC-H"/>
            <property name="fluorescence" value="FITC-H"/><property name="diameters_nm" value='[147, "", 296]'/><property name="r_squared" value="0.97321"/>
          </properties></testcase>
          <testcase><properties><property name="recording" value="water.fcs"/></properties>
            <failure message="unexpected channel"/></testcase>
          <testcase><properties><property name="recording" value="water.fcs"/>
            <property name="diameters_nm" value="[]"/><property name="r_squared" value="null"/>
          </properties></testcase></testsuite>""")
        return subprocess.CompletedProcess(command, 1, stdout="")

    monkeypatch.setattr(scanner.subprocess, "run", run_fixture_suite)
    markdown = tmp_path / "results.md"
    assert scanner.run_all_checks(markdown=markdown) == 1
    assert "| PASS | beads.fcs | Sony ID7000 | SSC-H | FITC-H | 147, ?, 296 | 0.973210 |" in markdown.read_text()
    assert "| FAIL | water.fcs |" in markdown.read_text()
    header, beads, water, legend, summary = capsys.readouterr().out.splitlines()
    assert header.split() == ["Status", "Recording", "Model", "Scatter", "Fluorescence", "Sizes", "(nm)", "R²", "Notes"]
    assert beads.index("beads.fcs") == water.index("water.fcs") == header.index("Recording")
    assert beads.index("147, ?, 296") == water.index("none") == header.index("Sizes")
    assert beads.endswith("0.973210")
    assert beads.index("0.973210") + 7 == water.rindex("—") == header.index("²")
    assert water[header.index("Notes"):] == "no fit; unexpected channel"
    assert beads.startswith("PASS") and water.startswith("FAIL")
    assert legend == "? = detected peak with no assigned diameter"
    assert summary == "1/2 recordings passed (4 checks)."
