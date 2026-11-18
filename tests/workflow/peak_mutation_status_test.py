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

    def test_build_status_alert_returns_bootstrap_alert(self) -> None:
        """Check build status alert returns bootstrap alert."""
        alert = mutation.build_status_alert(
            status="Cleared Rosetta fluorescence-guided scatter peaks.",
        )

        assert alert != ""

    def test_build_status_children_only_populates_matching_process(self) -> None:
        """Check build status children only populates matching process."""
        children = mutation.build_status_children(
            status_component_ids=[
                {"process": "Rosetta Script"},
                {"process": "Manual 1D"},
            ],
            target_process_name="Rosetta Script",
            status="Fluorescence peaks: 2 total.",
        )

        assert children[0] != ""
        assert children[1] == ""
