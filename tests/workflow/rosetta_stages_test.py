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


@pytest.mark.parametrize(
    "raw_settings", [{}, {"baseline_sigma_multiplier": float("nan")}]
)
def test_missing_or_invalid_baseline_gate_uses_the_ui_default(
    raw_settings, monkeypatch
):
    process = rosetta_mix.FluorescenceGuidedScatterPeakProcess()
    ui_default = next(
        setting["default_value"]
        for setting in process.get_settings()
        if setting["name"] == "baseline_sigma_multiplier"
    )
    settings = rosetta_mix.RosettaRunSettings.from_raw_values(
        peak_count=6, max_events_for_analysis=100, process_settings=raw_settings
    )
    assert settings.baseline_sigma_multiplier == ui_default == 3.0
    baseline = {"mean": 100.0, "std": 10.0}
    monkeypatch.setattr(
        rosetta_mix,
        "find_fit_validate_peaks_1d",
        lambda **_: {
            "validated_peaks": [baseline, {"mean": 500.0, "std": 20.0}],
            "diagnostic": "accepted",
        },
    )
    analysis = rosetta_mix.analyze_rosetta_fluorescence(
        events=rosetta_mix.RosettaEventData(
            np.array([1.0, 2.0]), np.array([100.0, 500.0]), 0
        ),
        settings=settings,
    )
    assert analysis.baseline_lower_gate == 70.0
    assert analysis.baseline_upper_gate == 130.0


def test_explicit_saved_baseline_gate_remains_authoritative():
    settings = rosetta_mix.RosettaRunSettings.from_raw_values(
        peak_count=6,
        max_events_for_analysis=100,
        process_settings={"baseline_sigma_multiplier": 1.0},
    )
    assert settings.baseline_sigma_multiplier == 1.0
