# -*- coding: utf-8 -*-

from types import SimpleNamespace

import pytest

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
                    1470.0,
                    2030.0,
                    2960.0,
                    4000.0,
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
            147.0,
            203.0,
            296.0,
            400.0,
            600.0,
            799.0,
            994.0,
        ]

    def test_build_table_prefill_blanks_scatter_peaks_beyond_size_range(self) -> None:
        scatter_peak_positions = [700.0, 1000.0, 2030.0, 4000.0, 9940.0, 30000.0]

        synthetic_result = rosetta_mix_v1.PeakProcessResult(
            peak_positions=[
                {"x": position, "y": 100.0}
                for position in scatter_peak_positions
            ],
            new_peak_positions=list(scatter_peak_positions),
            peak_lines_payload={
                "points": [
                    {"x": 1400.0, "y": 200.0, "kind": "marker"},
                    {"x": 3800.0, "y": 400.0, "kind": "marker"},
                ],
                "labels": [
                    "Dim marker",
                    "Bright marker",
                ],
            },
            status="",
            clear_existing_table_peaks=False,
            table_prefill_rows=[
                {
                    "measured_peak_position": position,
                    "particle_diameter_nm": float(index),
                }
                for index, position in enumerate(scatter_peak_positions, start=1)
            ],
        )

        resolved_rows, status_suffix = (
            rosetta_mix_v1.build_rosetta_mix_v1_table_prefill_rows(
                result=synthetic_result,
            )
        )

        assert [row["particle_diameter_nm"] for row in resolved_rows] == [
            70.0,
            100.0,
            203.0,
            400.0,
            994.0,
            "",
        ]
        assert "left blank for manual review" in status_suffix

    def test_bright_marker_scatter_anchor_flags_saturation(self) -> None:
        peak_metadata = [
            {"x": 1400.0, "y": 200.0, "label": "Dim marker"},
            {"x": 3800.0, "y": 990.0, "label": "Bright marker"},
        ]

        assert (
            rosetta_mix_v1.bright_marker_scatter_anchor_is_reliable(
                peak_metadata=peak_metadata,
                peak_lines_payload={
                    "fluorescence_saturation_intensity": 1000.0,
                },
            )
            is False
        )
        assert (
            rosetta_mix_v1.bright_marker_scatter_anchor_is_reliable(
                peak_metadata=peak_metadata,
                peak_lines_payload={
                    "fluorescence_saturation_intensity": 2000.0,
                },
            )
            is True
        )

    def test_infer_falls_back_to_single_anchor_when_bright_marker_unreliable(
        self,
    ) -> None:
        measured_peak_positions = [700.0, 1000.0, 1470.0, 2960.0, 6000.0, 9940.0]
        marker_positions = {"Dim marker": 1400.0, "Bright marker": 3800.0}

        two_marker_diameters, two_marker_count = (
            rosetta_mix_v1.infer_rosetta_mix_particle_diameters_nm(
                measured_peak_positions=measured_peak_positions,
                marker_positions=marker_positions,
                bright_marker_is_reliable=True,
            )
        )
        single_anchor_diameters, single_marker_count = (
            rosetta_mix_v1.infer_rosetta_mix_particle_diameters_nm(
                measured_peak_positions=measured_peak_positions,
                marker_positions=marker_positions,
                bright_marker_is_reliable=False,
            )
        )

        assert two_marker_count == 2
        assert single_marker_count == 1
        assert single_anchor_diameters != two_marker_diameters

    def test_build_table_prefill_reports_saturated_bright_marker_fallback(
        self,
    ) -> None:
        scatter_peak_positions = [700.0, 1000.0, 2030.0]

        synthetic_result = rosetta_mix_v1.PeakProcessResult(
            peak_positions=[
                {"x": position, "y": 100.0}
                for position in scatter_peak_positions
            ],
            new_peak_positions=list(scatter_peak_positions),
            peak_lines_payload={
                "points": [
                    {"x": 1400.0, "y": 200.0, "kind": "marker"},
                    {"x": 3800.0, "y": 990.0, "kind": "marker"},
                ],
                "labels": [
                    "Dim marker",
                    "Bright marker",
                ],
                "fluorescence_saturation_intensity": 1000.0,
            },
            status="",
            clear_existing_table_peaks=False,
            table_prefill_rows=[
                {
                    "measured_peak_position": position,
                    "particle_diameter_nm": float(index),
                }
                for index, position in enumerate(scatter_peak_positions, start=1)
            ],
        )

        resolved_rows, status_suffix = (
            rosetta_mix_v1.build_rosetta_mix_v1_table_prefill_rows(
                result=synthetic_result,
            )
        )

        assert "fluorescence-saturated" in status_suffix
        assert all(
            isinstance(row["particle_diameter_nm"], float)
            and row["particle_diameter_nm"] > 0.0
            for row in resolved_rows
        )

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
                "advanced_mode": ["enabled"],
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
        ] == [125.0, 147.0, 203.0]
        scatter_guide_annotations = result.peak_lines_payload.get(
            "scatter_guide_annotations",
        )

        assert isinstance(scatter_guide_annotations, list)
        assert [
            entry["label"]
            for entry in scatter_guide_annotations
        ] == [
            "125 nm",
            "147 nm",
            "140 nm",
            "203 nm",
        ]
        assert [
            entry["x"]
            for entry in scatter_guide_annotations
        ] == [
            pytest.approx(value)
            for value in result.peak_lines_payload.get("scatter_guide_positions", [])
        ]
        assert "single marker anchor" in str(result.status)

    def test_run_automatic_action_hides_status_when_advanced_mode_disabled(
        self,
        monkeypatch,
    ) -> None:
        synthetic_result = rosetta_mix_v1.PeakProcessResult(
            peak_positions=[1000.0],
            new_peak_positions=[1000.0],
            peak_lines_payload={
                "points": [
                    {"x": 1000.0, "y": 100.0, "kind": "peak"},
                    {"x": 1400.0, "y": 200.0, "kind": "marker"},
                ],
                "labels": [
                    "Peak 1",
                    "Dim marker",
                ],
                "scatter_guide_positions": [1000.0, 1400.0],
                "fluorescence_guide_positions": [100.0, 200.0],
            },
            status="Base status",
            clear_existing_table_peaks=False,
            table_prefill_rows=[
                {
                    "label": "Peak 1",
                    "measured_peak_position": 1000.0,
                    "particle_diameter_nm": "",
                }
            ],
        )

        def fake_super_run(self, **kwargs):
            del self
            del kwargs
            return synthetic_result

        monkeypatch.setattr(
            rosetta_mix_v1.FluorescenceGuidedScatterPeakProcess,
            "run_automatic_action",
            fake_super_run,
        )

        process = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1()

        result = process.run_automatic_action(
            backend=SimpleNamespace(fcs_file_path="dummy.fcs"),
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=20000,
            process_settings={"advanced_mode": []},
        )

        assert result is not None
        assert result.status == ""

    def test_run_automatic_action_adds_marker_size_annotations_without_table_rows(
        self,
        monkeypatch,
    ) -> None:
        synthetic_result = rosetta_mix_v1.PeakProcessResult(
            peak_positions=[],
            new_peak_positions=[],
            peak_lines_payload={
                "points": [
                    {"x": 1400.0, "y": 200.0, "kind": "marker"},
                    {"x": 3800.0, "y": 400.0, "kind": "marker"},
                ],
                "labels": [
                    "Dim marker",
                    "Bright marker",
                ],
                "scatter_guide_positions": [1400.0, 3800.0],
                "fluorescence_guide_positions": [200.0, 400.0],
            },
            status="Marker-only payload",
            clear_existing_table_peaks=False,
            table_prefill_rows=[],
        )

        def fake_super_run(self, **kwargs):
            del self
            del kwargs
            return synthetic_result

        monkeypatch.setattr(
            rosetta_mix_v1.FluorescenceGuidedScatterPeakProcess,
            "run_automatic_action",
            fake_super_run,
        )

        process = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1()

        result = process.run_automatic_action(
            backend=SimpleNamespace(fcs_file_path="dummy.fcs"),
            detector_channels={
                "scattering": "SSC-A",
                "green_fluorescence": "FITC-A",
            },
            peak_count=6,
            max_events_for_analysis=20000,
            process_settings={},
        )

        assert result is not None
        assert result.table_prefill_rows == []
        scatter_guide_annotations = result.peak_lines_payload.get(
            "scatter_guide_annotations",
        )
        assert isinstance(scatter_guide_annotations, list)
        assert [
            entry["label"]
            for entry in scatter_guide_annotations
        ] == [
            "140 nm",
            "380 nm",
        ]
