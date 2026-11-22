"""Check peak process invocation with different supported signatures."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

from RosettaX.workflow.peak.core import process_calls
from RosettaX.workflow.peak.core.process_calls import (
    call_add_clicked_peak_with_supported_arguments,
    call_run_automatic_action_with_supported_arguments,
)
from RosettaX.workflow.peak.scripts.automatic_1d_peaks import Automatic1DPeaksProcess
from RosettaX.workflow.peak.scripts.manual_1d_click import Manual1DClickProcess
from types import SimpleNamespace


def test_automatic_method_receives_only_its_supported_arguments():
    """Older processes with narrow signatures can still run."""
    process = SimpleNamespace(run_automatic_action=lambda *, peak_count: peak_count)
    result = call_run_automatic_action_with_supported_arguments(
        process=process, backend=None, detector_channels={}, process_settings={},
        peak_count=7, max_events_for_analysis=100, max_events_for_plots=50,
        runtime_config_data=None,
    )
    assert result == 7


def test_click_method_with_keyword_arguments_receives_full_context():
    """Flexible process signatures receive every available click argument."""
    process = SimpleNamespace(add_clicked_peak=lambda **kwargs: kwargs)
    result = call_add_clicked_peak_with_supported_arguments(
        process=process, click_data={"x": 1}, selected_data=None,
        existing_peak_lines_payload={}, backend=None, detector_channels={},
        process_settings={}, runtime_config_data=None, axis_scale_toggle_values=[],
    )
    assert result["click_data"] == {"x": 1}
    assert set(result) == {
        "click_data", "selected_data", "existing_peak_lines_payload", "backend",
        "detector_channels", "process_settings", "runtime_config_data", "axis_scale_toggle_values",
    }


def test_missing_process_method_returns_none():
    """An optional method that is not callable produces no result."""
    assert call_add_clicked_peak_with_supported_arguments(
        process=SimpleNamespace(add_clicked_peak=None), click_data=None,
        selected_data=None, existing_peak_lines_payload={}, backend=None,
        detector_channels={}, process_settings={}, runtime_config_data=None,
        axis_scale_toggle_values=[],
    ) is None


def test_builtin_peak_actions_skip_legacy_signature_inspection(monkeypatch):
    """Dispatch built-in automatic and manual actions through the standard interface."""
    monkeypatch.setattr(process_calls, "inspect", None)

    automatic = call_run_automatic_action_with_supported_arguments(
        process=Automatic1DPeaksProcess(), backend=None, detector_channels={}, process_settings={},
        peak_count=3, max_events_for_analysis=100, max_events_for_plots=50, runtime_config_data=None,
    )
    manual = call_add_clicked_peak_with_supported_arguments(
        process=Manual1DClickProcess(), click_data={"points": [{"x": 42.0}]},
        selected_data=None, existing_peak_lines_payload={}, backend=None, detector_channels={},
        process_settings={}, runtime_config_data=None, axis_scale_toggle_values=[],
    )

    assert automatic.peak_positions == []
    assert manual.new_peak_positions == [42.0]
