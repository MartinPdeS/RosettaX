"""Regression tests for workflow peak mutation status."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import sys
import types


class _DashBootstrapComponentsSentinel:
    """Callable component sentinel for lightweight Dash Bootstrap test setup."""

    def __init__(self, *args, **kwargs):
        """Initialize the state required by this test double."""
        self.args = args
        self.kwargs = kwargs
        self.color = kwargs.get("color")

    def __call__(self, *args, **kwargs):
        """Provide the callable behavior required by this test double."""
        return _DashBootstrapComponentsSentinel(*args, **kwargs)

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return self


class _DashBootstrapComponentsStub(types.ModuleType):
    """Minimal Dash Bootstrap components used by the unit tests."""

    def __getattr__(self, name):
        """Handle dynamic attribute lookup for this test double."""
        return _DashBootstrapComponentsSentinel


sys.modules.setdefault(
    "dash_bootstrap_components",
    _DashBootstrapComponentsStub("dash_bootstrap_components"),
)

from RosettaX.workflow.peak.callbacks import mutation
from RosettaX.workflow.peak.callbacks.debug_panel import build_rosetta_result_panel


class Test_PeakMutationStatus:
    """Regression checks for peak mutation status."""

    def test_classify_status_alert_color_returns_success_for_completed_run(self) -> None:
        """Check classify status alert color returns success for completed run."""
        color = mutation.classify_status_alert_color(
            status_text="Fluorescence peaks: 2 total. non-fluorescent scatter peaks: 6.",
        )

        assert color == "success"

    def test_classify_status_alert_color_returns_warning_for_rejections(self) -> None:
        """Check classify status alert color returns warning for rejections."""
        color = mutation.classify_status_alert_color(
            status_text="Scatter analysis: 7 candidate peak(s), 3 validated, 4 rejected: peak at 2.7e3.",
        )

        assert color == "warning"

    def test_classify_status_alert_color_returns_danger_for_failed_run(self) -> None:
        """Check classify status alert color returns danger for failed run."""
        color = mutation.classify_status_alert_color(
            status_text="No validated fluorescence peaks found. Unable to identify fluorescent marker populations.",
        )

        assert color == "danger"

    def test_build_status_alert_renders_error_as_plain_text(self) -> None:
        """Expose the error as text without the Bootstrap alert box."""
        message = "No validated fluorescence peaks found."
        status = mutation.build_status_alert(status=message)
        assert isinstance(status, mutation.html.Div)
        assert status.children == message
        assert status.role == "alert"

    def test_completed_run_has_no_success_box(self) -> None:
        """Suppress success alerts while retaining unresolved sizing and preview feedback."""
        assert mutation.build_status_alert(status="Assigned 147 and 203 nm above the marker.") == ""
        assert mutation.build_status_alert(status="Assigned 147 nm. 2 measured peaks remain unsized.") != ""
        assert mutation.build_status_alert(status="Preview. Click Run to update the peak table.") == ""

    def test_build_status_children_only_populates_matching_process(self) -> None:
        """Check build status children only populates matching process."""
        children = mutation.build_status_children(
            status_component_ids=[
                {"process": "Rosetta Script"},
                {"process": "Manual 1D"},
            ],
            target_process_name="Rosetta Script",
            status="No validated fluorescence peaks found.",
        )

        assert children[0] != ""
        assert children[1] == ""

    def test_rosetta_preview_describes_candidates_without_claiming_table_updates(self) -> None:
        """Distinguish preview candidates from committed calibration rows."""
        panel = build_rosetta_result_panel(
            status="",
            peak_lines_payload={
                "rosetta_settings_preview": True,
                "rosetta_sizing": {"assigned_row_count": 5, "measured_row_count": 6},
                "rosetta_event_counts": {"retained": 24_000},
            },
        )
        assert panel.children[0].children[0].children == "Rosetta preview"
        assert len(panel.children[0].children) == 1
        assert panel.children[2].children[1].children[0].children.startswith("Select Detect peaks to update the calibration table.")
        metrics = {row.children[0].children: row.children[1].children for row in panel.children[1].children}
        assert metrics == {"Sized peaks": "5", "Excluded peaks": "0", "Events analyzed": "24,000", "Fluorescence valley": "—"}

    def test_provisional_sizes_stay_visible_when_detection_completed_without_warning(self) -> None:
        """Show that successful detection may still leave provisional assignments."""
        panel = build_rosetta_result_panel(
            status="",
            peak_lines_payload={
                "rosetta_sizing": {"assigned_row_count": 5, "measured_row_count": 5, "needs_confirmation": True},
                "rosetta_assignment_evidence": {"rows": [{"particle_diameter_nm": 100}]},
                "rosetta_lowest_peak_exclusion": {"position": 2241},
            },
        )
        assert "app-diagnostics-inline" in panel.className
        assert panel.children[0].children[0].children == "Rosetta detection complete · 5 sizes assigned"
        assert len(panel.children[0].children) == 1
        assert panel.children[2].children[1].children[0].children.startswith("Calibration table updated. The assigned diameters are provisional.")

    def test_ambiguous_gate_explanation_stays_in_fit_details(self) -> None:
        """Keep only the outcome outside the collapsed fit information."""
        reason = "The scatter peak assignments are sensitive to the fluorescence gate."
        panel = build_rosetta_result_panel(
            status=reason,
            peak_lines_payload={
                "rosetta_detection_issue": "gate_ambiguous",
                "rosetta_gate_interval": [2500.0, 6600.0],
            },
        )
        assert panel.children[0].children[0].children == "Rosetta detection stopped"
        assert len(panel.children[0].children) == 1
        details = panel.children[2]
        assert details.children[0].children == "Fit details"
        assert details.children[1].children[0].children == f"Table unchanged. {reason}"
        assert panel.children[1].children[-1].children[0].children == "Fluorescence valley"


    def test_rosetta_ready_keeps_all_metric_slots_visible(self) -> None:
        """Reserve four visible metric slots before the first run."""
        panel = build_rosetta_result_panel()
        assert panel.children[0].children[0].children == "Rosetta ready"
        metric_values = [row.children[1].children for row in panel.children[1].children]
        assert metric_values == ["—"] * 4
        assert panel.children[2].children[0].children == "Fit details"
