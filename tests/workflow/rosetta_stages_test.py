"""Rosetta settings and detection stages can be verified without Dash callbacks."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from RosettaX.workflow.peak.scripts import rosetta_mix


def test_run_settings_validate_numeric_ranges_switches_and_nonfinite_values():
    settings = rosetta_mix.RosettaRunSettings.from_raw_values(
        peak_count=100,
        max_events_for_analysis="invalid",
        process_settings={
            "fit_r2_threshold": float("nan"),
            "fit_cv_threshold": "0.72",
            "baseline_sigma_multiplier": -10,
            "scatter_fit_cv_threshold": 100,
            "table_non_fluorescent_only": [],
            "saturation_guard_enabled": ["enabled"],
            "saturation_guard_fraction": 2,
        },
    )
    assert settings.peak_count == 20
    assert settings.max_events_for_analysis == 10_000
    assert settings.fit_r2_threshold == 0.85
    assert settings.fit_cv_threshold == 0.72
    assert settings.baseline_sigma_multiplier == 0.5
    assert settings.scatter_fit_cv_threshold == 3.0
    assert not settings.table_non_fluorescent_only
    assert settings.saturation_guard_enabled
    assert settings.saturation_guard_fraction == 1.0
    with pytest.raises(FrozenInstanceError):
        settings.fit_cv_threshold = 1.0


@pytest.mark.parametrize("marker_count", [0, 1, 2, 3, 4])
def test_marker_acceptance_requires_one_or_two_populations(marker_count):
    status = rosetta_mix.resolve_marker_stop_status(marker_count, "Fit diagnostic.")
    if marker_count in (1, 2):
        assert status is None
    else:
        assert status == (
            f"{marker_count} fluorescent marker peaks found after removing baseline. "
            "Stopping Rosetta workflow. Fit diagnostic."
        )


@pytest.mark.parametrize("table_non_fluorescent_only", [True, False])
def test_result_assembly_keeps_marker_overlays_separate_from_table_policy(
    table_non_fluorescent_only,
):
    settings = rosetta_mix.RosettaRunSettings.from_raw_values(
        peak_count=6,
        max_events_for_analysis=100,
        process_settings={
            "table_non_fluorescent_only": table_non_fluorescent_only,
            "saturation_guard_enabled": False,
        },
    )
    baseline = {"mean": 100.0, "std": 5.0}
    marker = {"mean": 500.0, "std": 10.0}
    result = rosetta_mix.build_rosetta_detection_result(
        backend=None,
        scattering_column="SSC",
        settings=settings,
        events=rosetta_mix.RosettaEventData(
            np.array([10.0, 220.0]), np.array([100.0, 500.0]), 0
        ),
        fluorescence=rosetta_mix.RosettaFluorescenceAnalysis(
            {"validated_peaks": [baseline, marker]},
            baseline,
            [marker],
            90.0,
            110.0,
            1000.0,
        ),
        markers=rosetta_mix.RosettaMarkerScatter(
            [{"x": 220.0, "y": 500.0, "kind": "marker", "label": "Bright marker"}],
            [220.0],
        ),
        scatter=rosetta_mix.RosettaScatterAnalysis(
            {},
            [{"x": 10.0, "y": 100.0, "kind": "non_fluorescent"}],
            [10.0],
            "Scatter fit accepted.",
        ),
    )
    assert result.peak_lines_payload["positions"] == [10.0, 220.0]
    assert result.peak_lines_payload["labels"] == [
        "Non-fluorescent peak 1",
        "Bright marker",
    ]
    assert result.new_peak_positions == (
        [10.0] if table_non_fluorescent_only else [10.0, 220.0]
    )
    assert [
        row["measured_peak_position"] for row in result.table_prefill_rows
    ] == result.new_peak_positions
    assert result.peak_lines_payload["baseline_cutoff"] == 110.0
