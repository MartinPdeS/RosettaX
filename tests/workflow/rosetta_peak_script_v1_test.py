"""Regression tests for workflow Rosetta peak script v1."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import pytest
from .rosetta_peak_script_test import _build_synthetic_dataset_with_two_markers
from RosettaX.workflow.peak.scripts import rosetta_mix, rosetta_mix_v1
from types import SimpleNamespace


class Test_RosettaPeakScriptV1:
    """Regression checks for Rosetta peak script v1."""

    def test_infer_rosetta_mix_particle_diameters_uses_marker_anchors(self) -> None:
        """Check infer Rosetta mix particle diameters uses marker anchors."""
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
        """Check build table prefill blanks scatter peaks beyond size range."""
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
        assert "review the detected peaks" in status_suffix

    def test_bright_marker_scatter_anchor_flags_saturation(self) -> None:
        """Check bright marker scatter anchor flags saturation."""
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

    def test_infer_rejects_unreliable_bright_marker(
        self,
    ) -> None:
        """Check inference rejects an unreliable bright marker."""
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
        assert single_marker_count == 0
        assert single_anchor_diameters == []

    def test_build_table_prefill_reports_saturated_bright_marker(
        self,
    ) -> None:
        """Check build table prefill reports a saturated bright marker."""
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

        assert "both reliable" in status_suffix
        assert all(row["particle_diameter_nm"] == "" for row in resolved_rows)

    def test_run_automatic_action_warns_when_only_one_marker_is_found(
        self,
        monkeypatch,
    ) -> None:
        """Check a single detected marker stops size assignment."""
        scattering, fluorescence = _build_synthetic_dataset_with_two_markers()

        def fake_column_copy(*, fcs_file_path, detector_column, dtype=float, n=None):
            """Return detector values prepared for this peak-detection test."""
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
        assert result.warning is True
        assert result.table_prefill_rows == []
        assert "both reliable" in result.status

    def test_run_automatic_action_warns_with_advanced_mode_disabled(
        self,
        monkeypatch,
    ) -> None:
        """Check the warning is retained when advanced mode is disabled."""
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
            """Return the prepared result of the parent peak process."""
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
        assert result.warning is True
        assert "both reliable" in result.status

    def test_run_automatic_action_warns_without_table_rows(
        self,
        monkeypatch,
    ) -> None:
        """Check a marker-only result raises a warning."""
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
            """Return the prepared result of the parent peak process."""
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
        assert result.warning is True
        assert result.status.startswith("Warning:")


def test_missing_marker_anchors_stop_run_and_show_warning(monkeypatch):
    """Unresolved peaks never become nanometer labels or calibration diameters."""
    result = rosetta_mix_v1.PeakProcessResult(
        peak_positions=[{"x": 1000.0, "y": 100.0}, {"x": 2000.0, "y": 100.0}],
        new_peak_positions=[1000.0, 2000.0],
        peak_lines_payload={
            "points": [
                {"x": 1000.0, "y": 100.0, "kind": "peak"},
                {"x": 2000.0, "y": 100.0, "kind": "peak"},
            ],
            "labels": ["Peak 1", "Peak 2"],
        },
        status="",
        clear_existing_table_peaks=False,
        table_prefill_rows=[
            {"measured_peak_position": 1000.0, "particle_diameter_nm": 1.0},
            {"measured_peak_position": 2000.0, "particle_diameter_nm": 2.0},
        ],
    )
    monkeypatch.setattr(
        rosetta_mix_v1.FluorescenceGuidedScatterPeakProcess,
        "run_automatic_action",
        lambda self, **kwargs: result,
    )

    resolved = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1().run_automatic_action(
        backend=None,
        detector_channels={},
        peak_count=2,
        max_events_for_analysis=100,
        process_settings={"advanced_mode": []},
    )

    assert resolved.warning is True
    assert resolved.table_prefill_rows == []
    assert resolved.peak_lines_payload == {}
    assert "both reliable" in resolved.status


def test_two_reliable_markers_assign_diameters(monkeypatch):
    """Two reliable markers permit the normal size-assignment path."""
    result = rosetta_mix_v1.PeakProcessResult(
        peak_positions=[{"x": 700.0, "y": 100.0}],
        new_peak_positions=[700.0],
        peak_lines_payload={
            "points": [
                {"x": 700.0, "y": 100.0, "kind": "peak"},
                {"x": 1400.0, "y": 200.0, "kind": "marker"},
                {"x": 3800.0, "y": 400.0, "kind": "marker"},
            ],
            "labels": ["Peak 1", "Dim marker", "Bright marker"],
        },
        status="",
        table_prefill_rows=[{"measured_peak_position": 700.0, "particle_diameter_nm": ""}],
    )
    monkeypatch.setattr(
        rosetta_mix_v1.FluorescenceGuidedScatterPeakProcess,
        "run_automatic_action",
        lambda self, **kwargs: result,
    )

    resolved = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1().run_automatic_action(
        backend=None, detector_channels={}, peak_count=1,
        max_events_for_analysis=100, process_settings={},
    )

    assert resolved.warning is False
    assert resolved.table_prefill_rows[0]["particle_diameter_nm"] == 70.0
    assert any(item["label"] == "70 nm" for item in resolved.peak_lines_payload["scatter_guide_annotations"])


def test_rosetta_v1_displays_side_scattering_channel_label():
    """The V1 scattering selector identifies the requested channel role."""
    process = rosetta_mix_v1.FluorescenceGuidedScatterPeakProcessV1()
    assert process.get_detector_channel_labels()["scattering"] == "Side scattering channel"
