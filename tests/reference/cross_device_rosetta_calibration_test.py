#!/usr/bin/env python
"""Integration tests for Rosetta detection and scattering calibration on bundled cross-device FCS recordings."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v", "-rx", "-s"]))

import hashlib
import json
import logging
import pytest
import subprocess
import sys
from pathlib import Path
from RosettaX.workflow.peak.core.detectors import (
    populate_peak_script_detector_dropdowns,
)
from RosettaX.workflow.recording_validation import check_outcome
from RosettaX.workflow.validation_recordings import reviewed_recordings

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIRECTORY = REPOSITORY_ROOT / "RosettaX" / "assets" / "sample-files" / "cross_device"

# Each reviewed recording contributes a channel-selection test and a sizing test.
RECORDINGS = {Path(path).relative_to("cross_device").as_posix(): record for path, record in reviewed_recordings().items()}
SAMPLES = [(name, record["scatter"], record["fluorescence"]) for name, record in RECORDINGS.items()]


@pytest.mark.parametrize(
    ("filename", "scatter", "fluorescence"),
    SAMPLES,
    ids=[sample[0] for sample in SAMPLES],
)
def test_cross_device_catalog_auto_selects_fcs_channels(*, filename: str, scatter: str, fluorescence: str, request) -> None:
    """Resolve the expected channels from each FCS file through Rosetta auto-select."""
    request.node.user_properties.append(("recording", filename))
    with (SAMPLE_DIRECTORY / filename).open("rb") as recording:
        assert hashlib.file_digest(recording, "sha256").hexdigest() == RECORDINGS[filename]["sha256"]
    _, selected = populate_peak_script_detector_dropdowns(
        uploaded_fcs_path=str(SAMPLE_DIRECTORY / filename),
        detector_dropdown_ids=[
            {"process": "Rosetta Script V1", "channel": "scattering"},
            {"process": "Rosetta Script V1", "channel": "green_fluorescence"},
        ],
        current_detector_values=[None, None],
        auto_select_rosetta_v1=True,
        logger=logging.getLogger(__name__),
    )
    assert selected == [scatter, fluorescence]


def run_sample_in_subprocess(**sample) -> dict:
    """Use real PyMieSim independently of the suite's dependency stubs."""
    process = subprocess.run(
        [
            sys.executable, "-c",
            "import json, sys; from pathlib import Path; "
            "from RosettaX.workflow.recording_validation import run_real_sample; "
            "sample = json.load(sys.stdin); sample['path'] = Path(sample['path']); "
            "print(json.dumps(run_real_sample(**sample)))",
        ],
        cwd=REPOSITORY_ROOT,
        input=json.dumps(sample),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize(("filename", "scatter", "fluorescence"), SAMPLES, ids=[sample[0] for sample in SAMPLES])
def test_rosetta_bead_positions_sizes_and_scattering_fit(
    *, filename: str, scatter: str, fluorescence: str, request,
) -> None:
    """Check assigned sizes, known diagnostic paths, and supported calibrations."""
    request.node.user_properties.append(("recording", filename))
    record = RECORDINGS[filename]
    result = run_sample_in_subprocess(
        path=str(SAMPLE_DIRECTORY / filename), scatter=scatter, fluorescence=record.get("sizing_fluorescence", fluorescence),
        fit_calibration=record["fit_calibration"],
    )
    request.node.user_properties.extend([
        ("diameters_nm", json.dumps([row["particle_diameter_nm"] for row in result["rows"]])),
        ("r_squared", json.dumps(result["r_squared"])),
        ("fit_note", result["fit_note"]),
    ])
    check_outcome(result=result, record=record, fixture_name=filename)
