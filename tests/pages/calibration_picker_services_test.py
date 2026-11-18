"""Tests for calibration picker upload services."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import base64
import json
import pytest
from RosettaX.pages.p04_calibrate.sections.s02_calibration_picker import services


def _build_upload_contents(name: str) -> str:
    """Build one minimal valid calibration upload payload."""
    record = {
        "schema": "rosettax_calibration_v1",
        "payload": {"calibration_type": "fluorescence", "name": name},
    }
    encoded = base64.b64encode(json.dumps(record).encode("utf-8")).decode("ascii")
    return f"data:application/json;base64,{encoded}"


def test_parse_uploaded_calibration_summaries_pairs_multiple_uploads() -> None:
    """Build one summary for each uploaded contents and filename pair."""
    summaries = services.parse_uploaded_calibration_summaries(
        contents=[_build_upload_contents("first"), _build_upload_contents("second")],
        filenames=["first.json", "second.json"],
    )

    assert [summary["selected_calibration"] for summary in summaries] == [
        "first.json",
        "second.json",
    ]


def test_parse_uploaded_calibration_summaries_rejects_mismatched_lists() -> None:
    """Reject upload content and filename lists with different lengths."""
    with pytest.raises(ValueError, match="payload is inconsistent"):
        services.parse_uploaded_calibration_summaries(
            contents=[_build_upload_contents("first")],
            filenames=["first.json", "second.json"],
        )
