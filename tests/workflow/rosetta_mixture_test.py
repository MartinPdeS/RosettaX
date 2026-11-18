"""Numerical recovery and workflow routing for Rosetta mixture detection."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import numpy as np
import pytest
from dataclasses import replace
from RosettaX.workflow.peak.scripts import rosetta_mix
from RosettaX.workflow.peak.scripts.base import PeakProcessResult
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture import (
    MixtureRosettaScatterPeakProcess,
)
from RosettaX.workflow.peak.scripts.rosetta_mix_mixture_fitting import (
    centers_in_observed_valleys,
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


def test_resolved_valley_rejects_a_midpoint_but_preserves_population_centers():
    """Use known asymmetric Gaussian densities to distinguish peaks from a blend."""
    centers = np.linspace(3, 5, 401)
    counts = (
        1000 * np.exp(-0.5 * ((centers - 3.7) / 0.14)**2)
        + 700 * np.exp(-0.5 * ((centers - 4.3) / 0.14)**2)
    )
    result = centers_in_observed_valleys(
        fitted_centers=np.array([3.7, 4.0, 4.3, 3.0, 5.0]),
        histogram_centers=centers, smoothed_counts=counts,
        count_variance=counts, observed_modes=np.array([140, 260]),
    )
    assert result.tolist() == [False, True, False, False, False]


def test_shallow_valley_with_counting_noise_does_not_establish_a_blend():
    """Avoid rejecting a center when the dip has insufficient statistical support."""
    result = centers_in_observed_valleys(
        fitted_centers=np.array([4.0]), histogram_centers=np.array([3.7, 4.0, 4.3]),
        smoothed_counts=np.array([100, 90, 100]), count_variance=np.array([100, 90, 100]),
        observed_modes=np.array([0, 2]),
    )
    assert not result.any()


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
    assert result.warning
    assert result.table_prefill_rows == []
    assert "found 1 validated non-fluorescent populations between" in result.status
    assert "expected exactly 3 (147, 203, 296 nm)" in result.status


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


@pytest.fixture
def complete_mixture_detection():
    """Provide a complete ordered mixture without assuming any intensity law."""
    positions = [100, 200, 300, 1100, 3000, 9000, 11000, 15000, 20000, 30000]
    scatter = [{"x": x, "y": 50, "kind": "non_fluorescent"} for x in positions]
    markers = [
        {"x": 1000, "y": 1000, "kind": "marker"},
        {"x": 10000, "y": 2000, "kind": "marker"},
    ]
    return PeakProcessResult(
        peak_positions=scatter,
        new_peak_positions=positions,
        peak_lines_payload={
            "points": [*scatter, *markers],
            "labels": [*[f"Scatter {index}" for index in range(len(scatter))], "Dim marker", "Bright marker"],
            "baseline_cutoff": 100,
        },
        status="Detected populations.",
        table_prefill_rows=[{"measured_peak_position": x} for x in positions],
    )


def test_complete_mixture_is_assigned_by_region_and_order(complete_mixture_detection):
    """Assign all known sizes without moving a 400 nm label below its anchor."""
    rows, warning = MixtureRosettaScatterPeakProcess().assign_particle_sizes(result=complete_mixture_detection)
    assert warning == ""
    assert [row["particle_diameter_nm"] for row in rows] == [70, 100, 125, 147, 203, 296, 400, 600, 799, 994]
    assert rows[6]["measured_peak_position"] > 10000


@pytest.mark.parametrize("middle", [[], [1100], [1100, 9000], [1100, 3000, 5000, 9000]])
def test_incomplete_or_extra_middle_populations_fail(complete_mixture_detection, middle):
    """Any count other than three between the markers must produce no assignments."""
    payload = dict(complete_mixture_detection.peak_lines_payload)
    points = payload["points"]
    labels = payload["labels"]
    retained = [(point, label) for point, label in zip(points, labels, strict=True)
                if point["kind"] == "marker" or not 1000 < point["x"] < 10000]
    payload["points"] = [point for point, _label in retained] + [
        {"x": x, "y": 50, "kind": "non_fluorescent"} for x in middle
    ]
    payload["labels"] = [label for _point, label in retained] + ["Scatter"] * len(middle)
    result = replace(complete_mixture_detection, peak_lines_payload=payload)
    rows, warning = MixtureRosettaScatterPeakProcess().assign_particle_sizes(result=result)
    assert rows == []
    assert f"found {len(middle)} validated non-fluorescent populations between" in warning
    assert "expected exactly 3 (147, 203, 296 nm)" in warning


@pytest.mark.parametrize("below_count,above_count", [(0, 0), (1, 0), (0, 1), (2, 1), (3, 4)])
def test_optional_outer_populations_expand_from_anchors(complete_mixture_detection, below_count, above_count):
    """Missing outer populations must not fail an otherwise complete middle group."""
    below = [100, 200, 300][-below_count:] if below_count else []
    above = [11000, 15000, 20000, 30000][:above_count]
    positions = [*below, 1100, 3000, 9000, *above]
    payload = dict(complete_mixture_detection.peak_lines_payload)
    retained = [(point, label) for point, label in zip(payload["points"], payload["labels"], strict=True)
                if point["kind"] == "marker" or point["x"] in positions]
    payload["points"] = [point for point, _label in retained]
    payload["labels"] = [label for _point, label in retained]
    result = replace(
        complete_mixture_detection, peak_lines_payload=payload,
        peak_positions=[point for point in payload["points"] if point["kind"] == "non_fluorescent"],
        table_prefill_rows=[{"measured_peak_position": x} for x in positions],
    )
    rows, warning = MixtureRosettaScatterPeakProcess().assign_particle_sizes(result=result)
    assert warning == ""
    expected_below = [70, 100, 125][-below_count:] if below_count else []
    assert [row["particle_diameter_nm"] for row in rows] == [
        *expected_below, 147, 203, 296, *[400, 600, 799, 994][:above_count],
    ]


def test_failed_assignment_clears_results_and_annotations(monkeypatch, complete_mixture_detection):
    """An incomplete mixture must not publish table rows or inferred size labels."""
    payload = dict(complete_mixture_detection.peak_lines_payload)
    # Remove the middle 203 nm population from otherwise complete detections.
    payload["points"] = [point for point in payload["points"] if point["x"] != 3000]
    payload["labels"] = [label for index, label in enumerate(payload["labels"]) if index != 4]
    detection = replace(complete_mixture_detection, peak_lines_payload=payload)
    monkeypatch.setattr(rosetta_mix.FluorescenceGuidedScatterPeakProcess, "run_automatic_action", lambda *args, **kwargs: detection)
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=object(), detector_channels={}, peak_count=10,
        max_events_for_analysis=10000, process_settings={},
    )
    assert result.warning
    assert result.table_prefill_rows == []
    assert result.peak_positions == []
    assert result.new_peak_positions == []
    assert "scatter_guide_annotations" not in result.peak_lines_payload
    assert "found 2" in result.status


def test_complete_assignment_publishes_expected_size_annotations(monkeypatch, complete_mixture_detection):
    """Successful complete detections publish all rows and marker-aware labels."""
    monkeypatch.setattr(rosetta_mix.FluorescenceGuidedScatterPeakProcess, "run_automatic_action", lambda *args, **kwargs: complete_mixture_detection)
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=object(), detector_channels={}, peak_count=10,
        max_events_for_analysis=10000, process_settings={},
    )
    assert not result.warning
    assert len(result.table_prefill_rows) == 10
    annotations = result.peak_lines_payload["scatter_guide_annotations"]
    assert [entry["label"] for entry in annotations if 1000 < entry["x"] < 10000] == ["147 nm", "203 nm", "296 nm"]
    assert all(entry["x"] > 10000 for entry in annotations if entry["label"] == "400 nm")


def test_successful_assignment_preserves_saturation_exclusion(monkeypatch, complete_mixture_detection):
    """Retain the exclusion reason and positions after successful size assignment."""
    payload = dict(complete_mixture_detection.peak_lines_payload)
    payload.update(
        saturation_guard_threshold=20000.0,
        saturation_guard_excluded_positions=[30000.0],
        saturation_guard_message="Saturation guard excluded 1 table peak.",
    )
    detection = replace(complete_mixture_detection, peak_lines_payload=payload)
    monkeypatch.setattr(
        rosetta_mix.FluorescenceGuidedScatterPeakProcess, "run_automatic_action",
        lambda *args, **kwargs: detection,
    )
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=object(), detector_channels={}, peak_count=10,
        max_events_for_analysis=10000, process_settings={},
    )
    assert not result.warning
    assert result.status == payload["saturation_guard_message"]
    assert result.peak_lines_payload["saturation_guard_excluded_positions"] == [30000.0]
    assert all(
        entry["kind"] != "excluded"
        for entry in result.peak_lines_payload["scatter_guide_annotations"]
    )
