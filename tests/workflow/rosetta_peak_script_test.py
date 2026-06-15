# -*- coding: utf-8 -*-

from types import SimpleNamespace

import numpy as np

from RosettaX.workflow.peak.scripts import rosetta_mix


def _build_synthetic_dataset_with_two_markers() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(123)

    baseline_fluorescence = rng.normal(loc=120.0, scale=10.0, size=9000)
    baseline_fluorescence = np.clip(baseline_fluorescence, 1.0, None)

    marker_dim_fluorescence = rng.normal(loc=900.0, scale=80.0, size=500)
    marker_dim_fluorescence = np.clip(marker_dim_fluorescence, 1.0, None)

    marker_bright_fluorescence = rng.normal(loc=6500.0, scale=500.0, size=450)
    marker_bright_fluorescence = np.clip(marker_bright_fluorescence, 1.0, None)

    non_fluorescent_scatter = np.concatenate(
        [
            rng.lognormal(mean=np.log(700.0), sigma=0.06, size=3000),
            rng.lognormal(mean=np.log(1300.0), sigma=0.06, size=3000),
            rng.lognormal(mean=np.log(2600.0), sigma=0.07, size=3000),
        ]
    )

    marker_dim_scatter = rng.lognormal(mean=np.log(1500.0), sigma=0.05, size=500)
    marker_bright_scatter = rng.lognormal(mean=np.log(3200.0), sigma=0.05, size=450)

    fluorescence = np.concatenate(
        [
            baseline_fluorescence,
            marker_dim_fluorescence,
            marker_bright_fluorescence,
        ]
    )

    scattering = np.concatenate(
        [
            non_fluorescent_scatter,
            marker_dim_scatter,
            marker_bright_scatter,
        ]
    )

    return scattering.astype(float), fluorescence.astype(float)


def _build_dataset_without_markers() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(44)

    fluorescence = rng.normal(loc=120.0, scale=12.0, size=5000)
    fluorescence = np.clip(fluorescence, 1.0, None)

    scattering = np.concatenate(
        [
            rng.lognormal(mean=np.log(700.0), sigma=0.08, size=2500),
            rng.lognormal(mean=np.log(1500.0), sigma=0.08, size=2500),
        ]
    )

    return scattering.astype(float), fluorescence.astype(float)


class Test_RosettaPeakScript:
    def test_run_automatic_action_detects_non_fluorescent_scatter_peaks(self, monkeypatch) -> None:
        scattering, fluorescence = _build_synthetic_dataset_with_two_markers()

        def fake_column_copy(*, fcs_file_path, detector_column, dtype=float, n=None):
            del fcs_file_path
            del dtype

            if detector_column == "SSC-A":
                values = scattering
            elif detector_column == "FITC-A":
                values = fluorescence
            else:
                raise AssertionError(f"Unexpected detector column: {detector_column}")

            if n is None:
                return values

            return values[: int(n)]

        monkeypatch.setattr(rosetta_mix, "column_copy", fake_column_copy)

        process = rosetta_mix.FluorescenceGuidedScatterPeakProcess()
        backend = SimpleNamespace(fcs_file_path="dummy.fcs")

        result = process.run_automatic_action(
            backend=backend,
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=20000,
            process_settings={
                "fit_r2_threshold": 0.60,
                "baseline_sigma_multiplier": 3.0,
            },
        )

        assert result is not None
        assert len(result.new_peak_positions or []) >= 2
        assert "non-fluorescent scatter peaks" in str(result.status).lower()
        assert isinstance(result.peak_lines_payload, dict)
        assert len(result.peak_lines_payload.get("points", [])) >= len(result.new_peak_positions or [])

    def test_run_automatic_action_stops_when_no_marker_peaks_found(self, monkeypatch) -> None:
        scattering, fluorescence = _build_dataset_without_markers()

        def fake_column_copy(*, fcs_file_path, detector_column, dtype=float, n=None):
            del fcs_file_path
            del dtype

            if detector_column == "SSC-A":
                values = scattering
            elif detector_column == "FITC-A":
                values = fluorescence
            else:
                raise AssertionError(f"Unexpected detector column: {detector_column}")

            if n is None:
                return values

            return values[: int(n)]

        monkeypatch.setattr(rosetta_mix, "column_copy", fake_column_copy)

        process = rosetta_mix.FluorescenceGuidedScatterPeakProcess()
        backend = SimpleNamespace(fcs_file_path="dummy.fcs")

        result = process.run_automatic_action(
            backend=backend,
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=10000,
            process_settings={},
        )

        assert result is not None
        assert result.new_peak_positions == []
        assert isinstance(result.peak_lines_payload, dict)
        assert "y_upper_gate" in result.peak_lines_payload
        assert np.isfinite(float(result.peak_lines_payload["y_upper_gate"]))
        assert (
            "marker" in str(result.status).lower()
            or "fluorescence peaks" in str(result.status).lower()
        )

    def test_baseline_gate_width_changes_payload_y_gate_interval(self, monkeypatch) -> None:
        scattering, fluorescence = _build_synthetic_dataset_with_two_markers()

        def fake_column_copy(*, fcs_file_path, detector_column, dtype=float, n=None):
            del fcs_file_path
            del dtype

            if detector_column == "SSC-A":
                values = scattering
            elif detector_column == "FITC-A":
                values = fluorescence
            else:
                raise AssertionError(f"Unexpected detector column: {detector_column}")

            if n is None:
                return values

            return values[: int(n)]

        monkeypatch.setattr(rosetta_mix, "column_copy", fake_column_copy)

        process = rosetta_mix.FluorescenceGuidedScatterPeakProcess()
        backend = SimpleNamespace(fcs_file_path="dummy.fcs")

        narrow = process.run_automatic_action(
            backend=backend,
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=20000,
            process_settings={
                "fit_r2_threshold": 0.60,
                "baseline_sigma_multiplier": 1.0,
            },
        )

        wide = process.run_automatic_action(
            backend=backend,
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=20000,
            process_settings={
                "fit_r2_threshold": 0.60,
                "baseline_sigma_multiplier": 4.0,
            },
        )

        assert narrow is not None
        assert wide is not None

        narrow_payload = narrow.peak_lines_payload
        wide_payload = wide.peak_lines_payload

        assert isinstance(narrow_payload, dict)
        assert isinstance(wide_payload, dict)
        assert float(wide_payload["y_upper_gate"]) >= float(narrow_payload["y_upper_gate"])

    def test_single_marker_is_classified_as_bright_without_saturated_counts(self) -> None:
        classified = rosetta_mix.classify_marker_peaks(
            marker_peaks=[
                {
                    "mean": 2000.0,
                    "std": 180.0,
                    "count": 120,
                }
            ],
            has_saturated_counts=False,
        )

        assert len(classified) == 1
        assert classified[0]["marker_role"] == "Bright marker"

    def test_single_marker_is_classified_as_dim_with_saturated_counts(self) -> None:
        classified = rosetta_mix.classify_marker_peaks(
            marker_peaks=[
                {
                    "mean": 2000.0,
                    "std": 180.0,
                    "count": 120,
                }
            ],
            has_saturated_counts=True,
        )

        assert len(classified) == 1
        assert classified[0]["marker_role"] == "Dim marker"

    def test_find_fit_validate_peaks_1d_returns_validated_peaks_for_clear_mixture(self) -> None:
        rng = np.random.default_rng(2026)
        values = np.concatenate(
            [
                rng.normal(loc=120.0, scale=8.0, size=5000),
                rng.normal(loc=950.0, scale=70.0, size=400),
                rng.normal(loc=6400.0, scale=450.0, size=350),
            ]
        )
        values = np.clip(values, 1.0, None)

        analysis = rosetta_mix.find_fit_validate_peaks_1d(
            values=values,
            peak_count=3,
            minimum_peak_fraction=0.05,
            minimum_events_per_peak=30,
            fit_r2_threshold=0.70,
            fit_cv_threshold=0.80,
            saturation_intensity=float(np.quantile(values, 0.9999)),
        )

        validated_peaks = analysis["validated_peaks"]

        assert len(validated_peaks) >= 2
        assert all(float(peak["r2"]) >= 0.70 for peak in validated_peaks)
