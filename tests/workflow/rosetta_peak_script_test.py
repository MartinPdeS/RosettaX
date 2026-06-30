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
    def test_settings_keep_only_process_specific_rosetta_toggles(self) -> None:
        process = rosetta_mix.FluorescenceGuidedScatterPeakProcess()

        settings = process.get_settings()
        table_non_fluorescent_only_setting = next(
            setting
            for setting in settings
            if setting.get("name") == "table_non_fluorescent_only"
        )
        fit_r2_setting = next(
            setting
            for setting in settings
            if setting.get("name") == "fit_r2_threshold"
        )
        fluorescence_cv_setting = next(
            setting
            for setting in settings
            if setting.get("name") == "fit_cv_threshold"
        )
        scatter_cv_setting = next(
            setting
            for setting in settings
            if setting.get("name") == "scatter_fit_cv_threshold"
        )

        assert all(
            setting.get("name") != "remove_saturated_events"
            for setting in settings
        )
        assert table_non_fluorescent_only_setting["kind"] == "boolean"
        assert table_non_fluorescent_only_setting["default_value"] is False
        assert fit_r2_setting["default_value"] == 0.80
        assert fluorescence_cv_setting["default_value"] == 1.0
        assert scatter_cv_setting["default_value"] == 1.0

    def test_run_automatic_action_uses_configured_fluorescence_cv_threshold(self, monkeypatch) -> None:
        scattering, fluorescence = _build_dataset_without_markers()
        captured_fit_cv_thresholds: list[float] = []

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

        def fake_find_fit_validate_peaks_1d(**kwargs):
            captured_fit_cv_thresholds.append(float(kwargs["fit_cv_threshold"]))
            return {
                "all_peaks": [],
                "validated_peaks": [],
            }

        monkeypatch.setattr(rosetta_mix, "column_copy", fake_column_copy)
        monkeypatch.setattr(
            rosetta_mix,
            "find_fit_validate_peaks_1d",
            fake_find_fit_validate_peaks_1d,
        )

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
            process_settings={
                "fit_cv_threshold": 0.72,
            },
        )

        assert result is not None
        assert captured_fit_cv_thresholds == [0.72]

    def test_run_automatic_action_uses_configured_scatter_cv_threshold(self, monkeypatch) -> None:
        scattering, fluorescence = _build_synthetic_dataset_with_two_markers()
        captured_fit_cv_thresholds: list[float] = []

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

        def fake_find_fit_validate_peaks_1d(**kwargs):
            values = np.asarray(kwargs["values"], dtype=float)
            captured_fit_cv_thresholds.append(float(kwargs["fit_cv_threshold"]))

            if np.max(values) < 20000.0:
                return {
                    "all_peaks": [
                        {"mean": 120.0, "std": 10.0, "count": 9000, "validated": True, "rejection_reasons": []},
                        {"mean": 900.0, "std": 80.0, "count": 500, "validated": True, "rejection_reasons": []},
                    ],
                    "validated_peaks": [
                        {"mean": 120.0, "std": 10.0, "count": 9000, "validated": True, "rejection_reasons": []},
                        {"mean": 900.0, "std": 80.0, "count": 500, "validated": True, "rejection_reasons": []},
                    ],
                }

            return {
                "all_peaks": [
                    {"mean": 700.0, "std": 50.0, "count": 3000, "validated": True, "rejection_reasons": []},
                ],
                "validated_peaks": [
                    {"mean": 700.0, "std": 50.0, "count": 3000, "validated": True, "rejection_reasons": []},
                ],
            }

        monkeypatch.setattr(rosetta_mix, "column_copy", fake_column_copy)
        monkeypatch.setattr(
            rosetta_mix,
            "find_fit_validate_peaks_1d",
            fake_find_fit_validate_peaks_1d,
        )

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
                "fit_cv_threshold": 0.72,
                "scatter_fit_cv_threshold": 1.35,
            },
        )

        assert result is not None
        assert captured_fit_cv_thresholds[0] == 0.72
        assert captured_fit_cv_thresholds[1:] == [1.35, 1.35]

    def test_run_automatic_action_payload_uses_filtered_plot_values_when_saturation_removal_enabled(
        self,
        monkeypatch,
    ) -> None:
        scattering = np.concatenate(
            [
                np.full(40, 3.91e6, dtype=float),
                np.linspace(500.0, 2000.0, 400, dtype=float),
            ]
        )
        fluorescence = np.concatenate(
            [
                np.full(40, 1.0, dtype=float),
                np.linspace(150.0, 900.0, 400, dtype=float),
            ]
        )

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
            process_settings={
                "remove_saturated_events": True,
            },
        )

        plot_x_values = result.peak_lines_payload.get("plot_x_values", [])
        plot_y_values = result.peak_lines_payload.get("plot_y_values", [])

        assert plot_x_values
        assert plot_y_values
        assert len(plot_x_values) < len(scattering)
        assert len(plot_y_values) < len(fluorescence)
        assert max(plot_x_values) < 3.91e6
        assert min(plot_y_values) > 1.0

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
        assert "scatter analysis:" in str(result.status).lower()
        assert isinstance(result.peak_lines_payload, dict)
        assert len(result.peak_lines_payload.get("points", [])) >= len(result.new_peak_positions or [])
        assert len(result.peak_lines_payload.get("scatter_guide_positions", [])) >= len(result.new_peak_positions or [])
        assert len(result.peak_lines_payload.get("fluorescence_guide_positions", [])) >= 1

    def test_run_automatic_action_can_insert_marker_associated_scatter_peaks_into_table(
        self,
        monkeypatch,
    ) -> None:
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
                "table_non_fluorescent_only": False,
            },
        )

        marker_points = [
            point
            for point in result.peak_lines_payload.get("points", [])
            if str(point.get("kind", "")).strip().lower() == "marker"
        ]

        assert result is not None
        assert marker_points
        assert len(result.peak_positions or []) == len(result.peak_lines_payload.get("points", []))
        assert len(result.new_peak_positions or []) == len(result.peak_lines_payload.get("points", []))
        assert "both non-fluorescent scatter peaks and marker-associated scatter peaks are inserted into the table" in str(result.status).lower()

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
        assert "analysis:" in str(result.status).lower()
        assert "candidate peak" in str(result.status).lower()
        assert "validated" in str(result.status).lower()

    def test_build_saturated_event_mask_marks_scatter_and_fluorescence_edge_pileups(self) -> None:
        rng = np.random.default_rng(2027)

        scattering = np.concatenate(
            [
                np.full(40, 1.0),
                rng.lognormal(mean=np.log(5_000.0), sigma=0.20, size=3000),
                np.full(50, 9.9e6),
            ]
        )
        fluorescence = np.concatenate(
            [
                rng.lognormal(mean=np.log(400.0), sigma=0.25, size=3040),
                np.full(50, 1.0),
            ]
        )

        mask = rosetta_mix.build_saturated_event_mask(
            scattering_values=scattering,
            fluorescence_values=fluorescence,
        )

        assert int(np.count_nonzero(mask)) >= 90
        assert np.any(mask[:40])
        assert np.any(mask[-50:])
        assert np.any(mask[3040:3090])

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

    def test_build_peak_analysis_diagnostic_text_includes_rejection_reasons(self) -> None:
        diagnostic_text = rosetta_mix.build_peak_analysis_diagnostic_text(
            analysis={
                "all_peaks": [
                    {
                        "mean": 120.0,
                        "validated": True,
                        "rejection_reasons": [],
                    },
                    {
                        "mean": 9800.0,
                        "validated": False,
                        "rejection_reasons": ["CV 0.73 > 0.55", "R2 0.42 < 0.80"],
                    },
                ],
                "validated_peaks": [
                    {
                        "mean": 120.0,
                        "validated": True,
                        "rejection_reasons": [],
                    }
                ],
            },
            label="fluorescence",
        )

        assert "1 rejected" in diagnostic_text
        assert "peak at 9.8e+03" in diagnostic_text
        assert "CV 0.73 > 0.55" in diagnostic_text
        assert "R2 0.42 < 0.80" in diagnostic_text
