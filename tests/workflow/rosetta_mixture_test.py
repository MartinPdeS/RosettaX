"""Numerical recovery and workflow routing for Rosetta mixture detection."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import numpy as np
import pytest
from RosettaX.workflow.peak.scripts import rosetta_mix
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture import (
    MixtureRosettaScatterPeakProcess,
)
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture_fitting import (
    find_mixture_scatter_peaks,
)
from RosettaX.workflow.peak.scripts.rosetta_mix_models import RosettaEventData


def fit_populations(*, values, peak_count=8):
    """Fit synthetic intensities with the new acceptance criteria."""
    return find_mixture_scatter_peaks(
        values=values, peak_count=peak_count, minimum_peak_fraction=0.03,
        minimum_events_per_peak=35, fit_r2_threshold=0.99,
        fit_cv_threshold=1.0, saturation_intensity=float("inf"),
    )


def test_separated_populations_recover_centers_and_memberships():
    """Recover unequal lognormal populations and conserve effective membership."""
    generator = np.random.default_rng(81)
    centers = np.array([3.0, 3.6, 4.2])
    values = np.concatenate([
        10**generator.normal(center, 0.09, count)
        for center, count in zip(centers, [2500, 4000, 1800], strict=True)
    ])
    result = fit_populations(values=values)
    assert len(result["validated_peaks"]) == 3
    np.testing.assert_allclose(
        np.log10([peak["mean"] for peak in result["validated_peaks"]]), centers, atol=0.015,
    )
    assert abs(sum(peak["count"] for peak in result["all_peaks"]) - len(values)) <= 2
    assert all(peak["r2"] is None for peak in result["all_peaks"])


def test_single_population_is_not_split_and_result_is_deterministic():
    """A single known lognormal population remains a single stable detection."""
    values = 10**np.random.default_rng(13).normal(4, 0.18, 4000)
    result = fit_populations(values=values)
    assert len(result["validated_peaks"]) == 1
    assert result == fit_populations(values=values)


@pytest.mark.parametrize("values", [np.array([]), np.array([0, -1, np.nan, np.inf]), np.ones(100)])
def test_degenerate_data_does_not_create_a_peak(values):
    """Empty, invalid and constant intensities cannot produce calibrating peaks."""
    assert not fit_populations(values=values)["validated_peaks"]


def test_flat_log_background_has_no_validated_populations():
    """Mixture components approximating a flat background do not become peaks."""
    values = 10**np.linspace(2, 6, 8000)
    assert not fit_populations(values=values)["validated_peaks"]


def test_mixture_script_routes_both_scatter_stages_through_new_fitter(monkeypatch):
    """Run fluorescence gating, both marker fits and baseline scatter fitting."""
    generator = np.random.default_rng(20)
    fluorescence = np.concatenate([
        10**generator.normal(center, 0.055, count)
        for center, count in [(2, 7000), (4, 2500), (5.5, 2000)]
    ])
    scattering = np.concatenate([
        10**generator.normal(4, 0.07, 3500),
        10**generator.normal(4.6, 0.07, 3500),
        10**generator.normal(4.2, 0.07, 2500),
        10**generator.normal(6, 0.07, 2000),
    ])
    monkeypatch.setattr(rosetta_mix, "load_rosetta_events", lambda **kwargs: RosettaEventData(
        scattering_values=scattering, fluorescence_values=fluorescence,
        removed_saturated_event_count=0,
    ))
    calls = []

    def track_fit(**kwargs):
        """Record actual numeric fits dispatched by each scatter stage."""
        calls.append(len(kwargs["values"]))
        return find_mixture_scatter_peaks(**kwargs)

    process = MixtureRosettaScatterPeakProcess()
    monkeypatch.setattr(process, "scatter_fit_function", track_fit)
    result = process.run_automatic_action(
        backend=object(), detector_channels={"scattering": "SSC", "green_fluorescence": "Green"},
        peak_count=6, max_events_for_analysis=20000,
        process_settings={"fit_r2_threshold": 0.7},
    )
    assert len(calls) == 3
    assert result is not None
    assert not result.warning, result.status
    assert len(result.table_prefill_rows) == 2


def test_overlapping_populations_recover_distinct_observed_modes():
    """Resolve two unequal populations whose tails overlap in log intensity."""
    generator = np.random.default_rng(193)
    values = np.concatenate([
        10**generator.normal(4, 0.12, 6000),
        10**generator.normal(4.34, 0.12, 4000),
    ])
    result = fit_populations(values=values)
    assert len(result["validated_peaks"]) == 2
    np.testing.assert_allclose(
        np.log10([peak["mean"] for peak in result["validated_peaks"]]),
        [4, 4.34], atol=0.03,
    )


def test_weak_population_survives_a_large_population_and_background():
    """Recover a 1.8% narrow population without accepting the broad background."""
    generator = np.random.default_rng(721)
    values = 10**np.r_[
        generator.normal(3.5, 0.10, 9000),
        generator.normal(4.5, 0.07, 180),
        generator.uniform(2, 6, 1000),
    ]
    result = fit_populations(values=values)
    accepted = result["validated_peaks"]
    assert len(accepted) == 2
    np.testing.assert_allclose(
        np.log10([peak["mean"] for peak in accepted]), [3.5, 4.5], atol=0.025,
    )
    assert all(peak["bootstrap_drift_sigma"] < 0.35 for peak in accepted)
    assert accepted[1]["count"] > 100
    assert any(not peak["validated"] for peak in result["all_peaks"])


def test_background_does_not_pull_centers_or_veto_separated_populations():
    """Keep two known centers stable with 35% uniformly distributed contamination."""
    generator = np.random.default_rng(721)
    values = 10**np.r_[
        generator.normal(3.5, 0.12, 4500),
        generator.normal(4.5, 0.07, 2000),
        generator.uniform(2, 6, 3500),
    ]
    result = fit_populations(values=values)
    assert len(result["validated_peaks"]) == 2
    np.testing.assert_allclose(
        np.log10([peak["mean"] for peak in result["validated_peaks"]]),
        [3.5, 4.5], atol=0.02,
    )


@pytest.mark.parametrize("seed", [12, 39, 721])
def test_random_background_ripples_are_not_calibrating_peaks(seed):
    """Sensitive prominence detection must still reject random flat backgrounds."""
    values = 10**np.random.default_rng(seed).uniform(2, 6, 10000)
    assert not fit_populations(values=values)["validated_peaks"]


def test_marker_core_and_broad_tails_are_one_observed_population():
    """A second component modeling marker tails must not reject the narrow core."""
    generator = np.random.default_rng(106)
    values = 10**np.r_[
        generator.normal(6, 0.07, 8000),
        generator.normal(5.97, 0.22, 500),
    ]
    result = fit_populations(values=values, peak_count=1)
    assert len(result["validated_peaks"]) == 1
    assert abs(np.log10(result["validated_peaks"][0]["mean"]) - 6) < 0.015
    assert len(result["all_peaks"]) == 2
    rejected = [peak for peak in result["all_peaks"] if not peak["validated"]]
    assert any("same observed mode" in reason for reason in rejected[0]["rejection_reasons"])
