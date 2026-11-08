"""Behavior checks for the scattering data quality review."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

from pathlib import Path
from RosettaX.pages.p03_scattering.sections.s02_quality.services import (
    count_measured_peaks,
    inspect_channels,
    status_text,
)


def test_inspect_real_fcs_sample() -> None:
    """Read real event values and detector metadata with a bounded sample."""
    path = Path(__file__).resolve().parents[2] / "RosettaX/assets/sample-files/apogee_rosetta_beads_1min.fcs"
    report = inspect_channels(file_path=str(path), channels=["405LALS(Peak)"] * 2, max_events=1000)
    assert int(report["total_events"]) == 168447
    assert len(report["channels"]) == 1
    channel = report["channels"][0]
    assert channel["count"] == 1000
    assert channel["nonfinite"] == 0
    assert channel["range"] == 4194303
    assert 0 <= channel["at_range"] <= channel["count"]


def test_measured_peak_count_and_diagnostics() -> None:
    """Ignore incomplete and invalid table values and preserve peak diagnostics."""
    rows = [{"measured_peak_position": value} for value in (42, "100", "", None, -1, "nan")]
    assert count_measured_peaks(table_data=rows) == 2
    assert status_text(value={"props": {"children": "7 candidates; 3 validated"}}) == "7 candidates; 3 validated"
