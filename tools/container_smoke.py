"""Check the installed container, including state across container recreation."""

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

from RosettaX.utils import directories, usage_metrics
from RosettaX.utils.streamed_uploads import (
    DEFAULT_STREAMED_UPLOAD_DIRECTORY,
    resolve_streamed_upload,
)
from RosettaX.workflow.scattering.backend import BackEnd

CALIBRATION_PAYLOAD = {
    "calibration_type": "fluorescence",
    "source_channel": "FITC-A",
    "slope": 1.0,
    "intercept": 0.0,
}
UPLOAD_BYTES = json.dumps(CALIBRATION_PAYLOAD).encode("utf-8")
CALIBRATION_FILENAME = "container_smoke.json"


def check_application(url: str) -> None:
    """Check actual HTTP responses and resources in the installed wheel."""
    with urlopen(url + "/", timeout=10) as response:
        assert response.status == 200
        assert b"<!DOCTYPE html>" in response.read()
    with urlopen(url + "/assets/logo/favicon.svg", timeout=10) as response:
        assert response.status == 200
        assert b"<svg" in response.read()
    with urlopen(url + "/assets/profiles/default_profile.json", timeout=10) as response:
        assert response.status == 200
        assert isinstance(json.load(response), dict)


def check_scattering_model() -> None:
    """Exercise the native scientific dependency without test stubs."""
    modeled = BackEnd.compute_modeled_coupling_from_diameters(
        particle_diameters_nm=np.asarray([100.0, 200.0]),
        wavelength_nm=488.0, source_numerical_aperture=0.1, optical_power_watt=1.0,
        detector_numerical_aperture=0.4, medium_refractive_index=1.33,
        particle_refractive_index=1.45, detector_cache_numerical_aperture=0.0,
        detector_sampling=100,
    )
    assert modeled.expected_coupling_values.shape == (2,)
    assert np.all(np.isfinite(modeled.expected_coupling_values))
    assert np.all(modeled.expected_coupling_values > 0)


def record_state(url: str, staging_directory: Path) -> None:
    """Write through the upload route and the configured persistent paths."""
    request = Request(
        url + "/api/uploads/stream", data=UPLOAD_BYTES,
        headers={"Content-Type": "application/octet-stream", "X-RosettaX-Filename": CALIBRATION_FILENAME},
    )
    with urlopen(request, timeout=10) as response:
        assert response.status == 200
        upload = json.load(response)
    stored_upload = resolve_streamed_upload(upload["token"], staging_directory=staging_directory)
    assert stored_upload.file_path.read_bytes() == UPLOAD_BYTES

    directories.fluorescence_calibration.mkdir(parents=True, exist_ok=True)
    calibration_path = directories.fluorescence_calibration / CALIBRATION_FILENAME
    calibration_path.write_bytes(UPLOAD_BYTES)
    counters = usage_metrics.record_apply_button_click()
    state = {"token": upload["token"], "apply_button_click_count": counters.apply_button_click_count}
    (staging_directory.parent / "container_smoke_state.json").write_text(json.dumps(state), encoding="utf-8")


def verify_state(url: str, staging_directory: Path) -> None:
    """Verify data created by the previous container remains usable."""
    state = json.loads((staging_directory.parent / "container_smoke_state.json").read_text(encoding="utf-8"))
    upload = resolve_streamed_upload(state["token"], staging_directory=staging_directory)
    assert upload.file_path.read_bytes() == UPLOAD_BYTES
    calibration_path = directories.fluorescence_calibration / CALIBRATION_FILENAME
    assert json.loads(calibration_path.read_bytes()) == CALIBRATION_PAYLOAD
    assert usage_metrics.load_usage_metrics().apply_button_click_count >= state["apply_button_click_count"]
    with urlopen(url + "/calibration-json/fluorescence/" + CALIBRATION_FILENAME, timeout=10) as response:
        assert response.status == 200
        assert b"FITC-A" in response.read()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--staging-directory", type=Path, default=DEFAULT_STREAMED_UPLOAD_DIRECTORY)
    parser.add_argument("--require-non-root", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--record-state", action="store_true")
    mode.add_argument("--verify-state", action="store_true")
    arguments = parser.parse_args()
    if arguments.require_non_root:
        assert os.getuid() != 0, "The application container must run as a non-root user."
    check_application(arguments.url.rstrip("/"))
    check_scattering_model()
    if arguments.record_state:
        record_state(arguments.url.rstrip("/"), arguments.staging_directory)
    if arguments.verify_state:
        verify_state(arguments.url.rstrip("/"), arguments.staging_directory)
    print("HTTP, packaged assets, scientific backend, and requested persistence checks passed.")
