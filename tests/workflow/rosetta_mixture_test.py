"""Numerical recovery and workflow routing for Rosetta mixture detection."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

import logging
import numpy as np
import pytest
from dataclasses import replace
from types import SimpleNamespace
from RosettaX.workflow.peak.adapters.scattering import ScatteringPeakWorkflowAdapter
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
    """Fit both markers and all three non-fluorescent scatter intervals."""
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
        calls.append(kwargs.get("center_bounds"))
        return find_mixture_scatter_peaks(**kwargs)

    process = MixtureRosettaScatterPeakProcess()
    monkeypatch.setattr(process, "scatter_fit_function", track_fit)
    result = process.run_automatic_action(
        backend=object(), detector_channels={"scattering": "SSC", "green_fluorescence": "Green"},
        peak_count=6, max_events_for_analysis=20000,
        process_settings={"fit_r2_threshold": 0.7},
    )
    assert len(calls) == 5
    assert calls[:2] == [None, None]
    left, middle, right = calls[2:]
    assert left[0] == 0 and left[1] == middle[0]
    assert middle[0] < middle[1] == right[0]
    assert right[1] == np.inf
    assert result is not None
    assert result.warning
    assert [row["particle_diameter_nm"] for row in result.table_prefill_rows] == [""]
    assert result.peak_lines_payload["rosetta_assignment_evidence"]["scatter"]
    assert "Found 1 validated scatter peak between" in result.status
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
def test_incomplete_or_extra_middle_populations_leave_outer_sizes(complete_mixture_detection, middle):
    """An unresolved middle interval leaves the outer assignments available."""
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
    assert [row["particle_diameter_nm"] for row in rows] == [70, 100, 125, "", "", "", 400, 600, 799, 994]
    assert warning.startswith(f"Partial result: Found {len(middle)} validated scatter peak")
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
    assert ("are provisional" in warning) == (0 < below_count < 3 or 0 < above_count < 4)
    expected_below = [70, 100, 125][-below_count:] if below_count else []
    assert [row["particle_diameter_nm"] for row in rows] == [
        *expected_below, 147, 203, 296, *[400, 600, 799, 994][:above_count],
    ]


def test_partial_assignment_preserves_outer_rows_and_annotations(monkeypatch, complete_mixture_detection):
    """An unresolved middle interval retains only the outer size annotations."""
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
    assert [row["particle_diameter_nm"] for row in result.table_prefill_rows] == [100, 125, "", "", "", 400, 600, 799, 994]
    annotations = result.peak_lines_payload["scatter_guide_annotations"]
    assert all(entry["kind"] == "marker" or not 1000 < entry["x"] < 10000 for entry in annotations)
    assert result.status.startswith("Partial result: Found 2")



def test_complete_assignment_publishes_expected_size_annotations(monkeypatch, complete_mixture_detection):
    """Successful complete detections publish all rows and marker-aware labels."""
    monkeypatch.setattr(rosetta_mix.FluorescenceGuidedScatterPeakProcess, "run_automatic_action", lambda *args, **kwargs: complete_mixture_detection)
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=object(), detector_channels={}, peak_count=10,
        max_events_for_analysis=10000, process_settings={},
    )
    assert not result.warning
    assert len(result.table_prefill_rows) == 9
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


def test_mixture_estimates_sizes_assuming_a_single_bright_marker(*, monkeypatch):
    """Publish provisional sizes from a lone fluorescent marker."""
    coupling = dict(zip(
        (70, 100, 125, 140, 147, 203, 296, 380, 400, 600, 799, 994),
        (1, 2.7, 5, 8, 11, 29, 66, 120, 133, 480, 750, 1300),
        strict=True,
    ))
    generator = np.random.default_rng(482)
    diameters = (100, 147, 296, 600, 380)
    scattering = np.concatenate([
        coupling[size] * 1000 * np.exp(generator.normal(0, 0.07, 2000))
        for size in diameters
    ])
    fluorescence = np.concatenate([
        10**generator.normal(center, 0.08, count)
        for center, count in [(2.0, 8000), (4.0, 2000)]
    ])
    monkeypatch.setattr(rosetta_mix, "load_rosetta_events", lambda **kwargs: RosettaEventData(
        scattering_values=scattering, fluorescence_values=fluorescence,
        removed_saturated_event_count=0,
    ))
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=SimpleNamespace(fcs_file_path="synthetic.fcs"),
        detector_channels={"scattering": "SSC", "green_fluorescence": "Green"},
        peak_count=6, max_events_for_analysis=10000,
        process_settings={"saturation_guard_enabled": False},
    )
    assert result is not None and not result.warning, result.status if result else None
    assert [row["particle_diameter_nm"] for row in result.table_prefill_rows] == [203, 296, 400]
    assert [row["measured_peak_position"] for row in result.table_prefill_rows] == pytest.approx(
        [coupling[diameter] * 1000 for diameter in diameters[1:-1]], rel=0.03,
    )
    assert "Assumed the only fluorescent marker is the 380 nm bright marker" in result.status
    assert "Bright marker (assumed)" in result.peak_lines_payload["labels"]
    assert result.peak_lines_payload["rosetta_assignment_evidence"]
    table_rows = ScatteringPeakWorkflowAdapter().apply_peak_process_result_to_table(
        table_data=[{"particle_diameter_nm": 100, "expected_coupling": 2.0}] * 3,
        result=result,
        context={"mie_model": "Solid Sphere", "replace_existing_table_peaks": True},
        logger=logging.getLogger(__name__),
    )
    assert [row["particle_diameter_nm"] for row in table_rows] == [203, 296, 400]
    assert [row["expected_coupling"] for row in table_rows] == [""] * 3
    assert [row["measured_peak_position"] for row in table_rows] == [
        round(row["measured_peak_position"], 1) for row in result.table_prefill_rows
    ]


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        ({}, (0.70, 0.60)),
        ({"marker_fit_strictness": "0"}, (0.35, 1.50)),
        ({"marker_fit_strictness": "0.25"}, (0.525, 1.05)),
        ({"marker_fit_strictness": "1"}, (0.95, 0.30)),
        ({"marker_fit_strictness": "2"}, (0.95, 0.30)),
        ({"marker_fit_strictness": "invalid"}, (0.70, 0.60)),
        ({"fit_r2_threshold": 0.62, "fit_cv_threshold": 0.90}, (0.62, 0.90)),
        ({"marker_fit_strictness": 1, "fit_r2_threshold": 0.62}, (0.95, 0.30)),
    ],
)
def test_marker_fit_strictness_controls_both_fluorescence_thresholds(*, monkeypatch, settings, expected):
    """Resolve the single control without changing scatter thresholds or legacy callers."""
    captured = {}

    def capture_settings(*args, process_settings, **kwargs):
        """Record the thresholds dispatched to the detection pipeline."""
        captured.update(process_settings)
        return None

    monkeypatch.setattr(rosetta_mix.FluorescenceGuidedScatterPeakProcess, "run_automatic_action", capture_settings)
    process = MixtureRosettaScatterPeakProcess()
    process.run_automatic_action(
        backend=object(), detector_channels={}, peak_count=10,
        max_events_for_analysis=10_000, process_settings=settings,
    )
    assert (captured["fit_r2_threshold"], captured["fit_cv_threshold"]) == expected
    assert captured["scatter_fit_cv_threshold"] == 1.0
    controls = {setting["name"] for setting in process.get_settings()}
    assert "marker_fit_strictness" in controls
    assert controls.isdisjoint({"fit_r2_threshold", "fit_cv_threshold"})


@pytest.mark.parametrize("clipped_marker", ["bright", "dim"])
def test_scatter_edge_identifies_marker_without_using_clipped_intensity(*, monkeypatch, clipped_marker):
    """Use an isolated clipped fluorescence gate only as a scatter ordering boundary."""
    generator = np.random.default_rng(871)
    counts = (2400, 2400, 2400, 3200, 3200)
    scatter_centers = (2500, 6000, 13000, 900, 26000)
    fluorescence_centers = (2, 2, 2, 4, 5)
    scatter = np.concatenate([
        center * np.exp(generator.normal(0, 0.075, count))
        for center, count in zip(scatter_centers, counts, strict=True)
    ])
    fluorescence = np.concatenate([
        10 ** generator.normal(center, 0.065, count)
        for center, count in zip(fluorescence_centers, counts, strict=True)
    ])
    if clipped_marker == "bright":
        scatter = np.minimum(scatter, 20000)
    else:
        scatter = np.maximum(scatter, 1400)
    monkeypatch.setattr(
        rosetta_mix, "column_copy",
        lambda **kwargs: scatter if kwargs["detector_column"] == "SSC" else fluorescence,
    )
    result = MixtureRosettaScatterPeakProcess().run_automatic_action(
        backend=SimpleNamespace(fcs_file_path="synthetic.fcs"),
        detector_channels={"scattering": "SSC", "green_fluorescence": "Green"},
        peak_count=8, max_events_for_analysis=20000, process_settings={},
    )
    assert result is not None and not result.warning, result.status if result else None
    assert [row["particle_diameter_nm"] for row in result.table_prefill_rows] == [203, 296], (result.status, result.peak_lines_payload.get("marker_scatter_diagnostics"))
    assert [row["measured_peak_position"] for row in result.table_prefill_rows] == pytest.approx(
        scatter_centers[1:3], rel=0.025,
    )
    assert "marker at the scatter limit" in result.status
    assert {entry["method"] for entry in result.peak_lines_payload["rosetta_size_assignments"]} == {
        "One measured marker and a clipped scatter boundary",
    }


def test_complete_scatter_ladder_identifies_single_marker_by_rank():
    """Recover unique diameters when the complete CAL003 scatter ladder is visible."""
    scatter_positions = [100.0 * index for index in range(1, 11)]
    marker_position = 650.0
    scatter_points = [{"x": position, "y": 20.0, "kind": "non_fluorescent"} for position in scatter_positions]
    detection = PeakProcessResult(
        peak_positions=scatter_points,
        new_peak_positions=scatter_positions,
        status="",
        table_prefill_rows=[{"measured_peak_position": position} for position in scatter_positions],
        peak_lines_payload={
            "points": [*scatter_points, {"x": marker_position, "y": 1500.0, "kind": "marker"}],
            # The fluorescence fit cannot label a single gate by brightness alone.
            "labels": ["Scatter"] * 10 + ["Dim marker"],
            "marker_scatter_diagnostics": [
                {"marker_role": "Dim marker", "validated": True, "selected_peak": {"mean": marker_position}},
            ],
        },
    )
    resolved, rows, status = MixtureRosettaScatterPeakProcess().resolve_particle_sizes(result=detection)
    assert [row["particle_diameter_nm"] for row in rows] == [70, 100, 125, 147, 203, 296, 400, 600, 799, 994]
    assert resolved.peak_lines_payload["labels"][-1] == "Bright marker"
    assert "using the 380 nm marker" in status


@pytest.mark.parametrize(("higher_peaks", "expected"), [(0, []), (2, [147, 203]), (3, [147, 203, 296]), (4, [147, 203, 296, ""])])
def test_confirmed_dim_marker_assigns_nearest_populations_in_both_directions(*, higher_peaks, expected):
    """Assign consecutive middle sizes only when a distinct bright gate identifies the dim gate."""
    scatter_positions = [12.5, 25.0, 50.0, 75.0, *[200.0 + 100.0 * index for index in range(higher_peaks)]]
    scatter_points = [{"x": position, "y": 20.0, "kind": "non_fluorescent"} for position in scatter_positions]
    detection = PeakProcessResult(
        peak_positions=scatter_points,
        new_peak_positions=scatter_positions,
        status="",
        table_prefill_rows=[{"measured_peak_position": position} for position in scatter_positions],
        peak_lines_payload={
            "points": [*scatter_points, {"x": 100.0, "y": 1500.0, "kind": "marker"}],
            "labels": ["Scatter"] * len(scatter_points) + ["Dim marker"],
            "marker_scatter_diagnostics": [
                {
                    "marker_role": "Dim marker", "validated": True,
                    "fluorescence_position": 1500.0, "selected_peak": {"mean": 100.0},
                },
                {"marker_role": "Bright marker", "validated": False, "fluorescence_position": 4000.0},
            ],
        },
    )
    _, rows, status = MixtureRosettaScatterPeakProcess().resolve_particle_sizes(result=detection)
    assert [row["particle_diameter_nm"] for row in rows] == ["", 70, 100, 125, *expected]
    assert "assumes no intermediate populations were missed" in status


@pytest.mark.parametrize(
    ("usable_marker", "removed_positions", "expected_shift"),
    [
        ("Dim marker", {1100}, {3000: (203, 147), 9000: (296, 203), 11000: (400, 296)}),
        ("Bright marker", {9000}, {300: (125, 147), 1100: (147, 203), 3000: (203, 296)}),
        ("Dim marker", {30000}, {}),
        ("Bright marker", {100}, {}),
    ],
)
def test_single_marker_rank_compares_bead_identity_to_two_marker_reference(
    *, complete_mixture_detection, usable_marker, removed_positions, expected_shift,
):
    """Compare assignments by known peak identity with one marker or one bead missing."""
    process = MixtureRosettaScatterPeakProcess()
    reference, reference_rows, _ = process.resolve_particle_sizes(result=complete_mixture_detection)
    reference_by_position = {
        row["measured_peak_position"]: row["particle_diameter_nm"] for row in reference_rows
    }
    assert {entry["method"] for entry in reference.peak_lines_payload["rosetta_size_assignments"]} == {
        "Two measured markers",
    }

    payload = complete_mixture_detection.peak_lines_payload
    points_with_labels = list(zip(payload["points"], payload["labels"], strict=True))
    visible = [
        (point, label)
        for point, label in points_with_labels
        if point["x"] not in removed_positions
        and (point["kind"] != "marker" or label == usable_marker)
    ]
    diagnostics = [
        {
            "marker_role": label,
            "fluorescence_position": point["y"],
            "validated": label == usable_marker,
            "selected_peak": {"mean": point["x"]} if label == usable_marker else None,
            "gated_event_count": 1000,
        }
        for point, label in points_with_labels if point["kind"] == "marker"
    ]
    detection = replace(
        complete_mixture_detection,
        peak_lines_payload=dict(
            payload,
            points=[point for point, label in visible],
            labels=[label for point, label in visible],
            marker_scatter_diagnostics=diagnostics,
        ),
        peak_positions=[
            point for point in complete_mixture_detection.peak_positions
            if point["x"] not in removed_positions
        ],
        table_prefill_rows=[
            row for row in complete_mixture_detection.table_prefill_rows
            if row["measured_peak_position"] not in removed_positions
        ],
    )
    resolved, rows, status = process.resolve_particle_sizes(result=detection)
    assignments = {row["measured_peak_position"]: row["particle_diameter_nm"] for row in rows}
    assigned_sizes = [diameter for diameter in assignments.values() if diameter]
    if usable_marker == "Bright marker" and not expected_shift:
        assert assigned_sizes == [147, 203, 296, 400, 600, 799, 994]
    assert {
        position: (reference_by_position[position], diameter)
        for position, diameter in assignments.items()
        if diameter and diameter != reference_by_position[position]
    } == expected_shift
    provenance = resolved.peak_lines_payload["rosetta_size_assignments"]
    assert len(provenance) == len(assigned_sizes)
    assert {entry["method"] for entry in provenance} == {"Estimated by rank from one marker"}
    assert {tuple(entry["marker_diameters_nm"]) for entry in provenance} == {
        (380.0,) if usable_marker == "Bright marker" else (140.0,),
    }
    assert "assumes no intermediate populations were missed" in status


@pytest.mark.parametrize(("dim_count", "overlap", "retained"), [(300, 0.0, ["Bright marker"]), (850, 0.0, []), (300, 0.7, [])])
def test_reversed_marker_candidates_preserve_measured_peaks(
    *, complete_mixture_detection, dim_count, overlap, retained,
):
    """Keep visible evidence and only carry a distinctly stronger gate to sizing."""
    payload = dict(complete_mixture_detection.peak_lines_payload)
    points = [dict(point) for point in payload["points"]]
    points[-2]["x"], points[-1]["x"] = points[-1]["x"], points[-2]["x"]
    payload["points"] = points
    payload["marker_scatter_diagnostics"] = [
        {
            "marker_role": role, "fluorescence_position": point["y"], "validated": True,
            "selected_peak": {"mean": point["x"], "count": count},
            "gate_overlap": overlap, "above_baseline_fraction": 1.0, "gated_event_count": 1000,
        }
        for role, point, count in zip(
            ("Dim marker", "Bright marker"), points[-2:], (dim_count, 900), strict=True,
        )
    ]
    detection = replace(complete_mixture_detection, peak_lines_payload=payload)
    reviewed, rows, status = MixtureRosettaScatterPeakProcess().resolve_particle_sizes(result=detection)
    assert reviewed.peak_lines_payload["points"] == points
    assert reviewed.peak_lines_payload["labels"][-2:] == ["Fluorescent marker candidate"] * 2
    assert [item["marker_role"] for item in reviewed.peak_lines_payload["marker_scatter_diagnostics"]
            if item["validated"]] == retained
    assert all(row["particle_diameter_nm"] == "" for row in rows)
    assert "1e+04 a.u. scatter" in status and "1000 a.u." in status
    assert "Compute model" in status
