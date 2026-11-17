"""Run the real Rosetta bead calibration regression alongside the unit tests."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import subprocess
import sys
from pathlib import Path


def test_rosetta_calibration_on_real_beads() -> None:
    """Check all Rosetta modes and the real calibration/application baselines."""
    repository = Path(__file__).resolve().parents[2]
    integration_test = repository / "integration_tests" / "scattering_fcs_test.py"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(integration_test),
            str(repository / "integration_tests" / "rosetta_scripts_fcs_test.py"),
            "-o",
            "addopts=",
            "-q",
        ],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        "Real Rosetta bead calibration regression failed in its isolated process:\n"
        f"{result.stdout}\n{result.stderr}"
    )
