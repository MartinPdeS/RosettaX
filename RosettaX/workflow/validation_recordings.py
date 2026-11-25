"""Reviewed cross-device recordings shared by the application, tests and README."""

import json
from pathlib import Path

SAMPLE_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "sample-files"


def load_sample_metadata() -> dict:
    """Return metadata keyed by each sample's path relative to the sample directory."""
    return json.loads((SAMPLE_DIRECTORY / "sample_file_metadata.json").read_text(encoding="utf-8"))


def reviewed_recordings() -> dict:
    """Return recorded regression expectations keyed by relative FCS path."""
    return {
        path: metadata["validation"] for path, metadata in load_sample_metadata().items()
        if "validation" in metadata
    }


def representative_recordings(*, metadata: dict) -> list[str]:
    """Select one reviewed download per manufacturer and model.

    Prefer more assigned bead sizes, fewer unassigned peaks, an enabled curve
    fit, then a smaller download. The relative path breaks remaining ties.
    """
    best = {}
    for path, sample in metadata.items():
        record = sample.get("validation")
        if not record:
            continue
        sizes = record["expected_diameters_nm"]
        assigned = sum(bool(size) for size in sizes)
        rank = (-assigned, len(sizes) - assigned, not record["fit_calibration"], sample["size_bytes"], path)
        model = (record["manufacturer"], record["model"])
        if model not in best or rank < best[model]:
            best[model] = rank
    return [best[model][-1] for model in sorted(best)]


def supported_cytometers() -> dict[str, list[str]]:
    """Return the reviewed instrument models grouped by manufacturer for display."""
    brands: dict[str, set[str]] = {}
    for recording in reviewed_recordings().values():
        brands.setdefault(recording["manufacturer"], set()).add(recording["model"])
    return {brand: sorted(models) for brand, models in sorted(brands.items())}
