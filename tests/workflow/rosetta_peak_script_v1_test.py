# -*- coding: utf-8 -*-

from types import SimpleNamespace

from RosettaX.workflow.peak.scripts import rosetta_mix, rosetta_mix_v1

from .rosetta_peak_script_test import _build_synthetic_dataset_with_two_markers


class Test_RosettaPeakScriptV1:
    def test_infer_rosetta_mix_particle_diameters_uses_marker_anchors(self) -> None:
        inferred_diameters_nm, used_marker_count = (
            rosetta_mix_v1.infer_rosetta_mix_particle_diameters_nm(
                measured_peak_positions=[
                    700.0,
                    1000.0,
                    1250.0,
                    1940.0,
                    2030.0,
                    2960.0,
                    6000.0,
                    7990.0,
                    9940.0,
                ],
                marker_positions={
                    "Dim marker": 1400.0,
                    "Bright marker": 3800.0,
                },
            )
        )

        assert used_marker_count == 2
        assert inferred_diameters_nm == [
            70.0,
            100.0,
            125.0,
            194.0,
            203.0,
            296.0,
            600.0,
            799.0,
            994.0,
        ]

    def test_run_automatic_action_replaces_placeholder_diameters_with_rosetta_mix_sizes(
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

        process = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1()
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
        assert result.table_prefill_rows
        assert [row["measured_peak_position"] for row in result.table_prefill_rows] == [
            float(value)
            for value in (result.new_peak_positions or [])
        ]
        assert [
            row["particle_diameter_nm"]
            for row in result.table_prefill_rows
        ] == [194.0, 296.0, 600.0]
        assert "single marker anchor" in str(result.status)
