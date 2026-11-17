"""Sensitive Rosetta Script settings for scatter-peak validation."""

from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess
from typing import Any

_FIXED_FIT_SETTING_NAMES = {
    "fit_r2_threshold",
    "fit_cv_threshold",
    "scatter_fit_r2_threshold",
    "scatter_fit_cv_threshold",
}


class SensitiveRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Use permissive scatter-fit thresholds with marker-based size assignment."""

    process_name = "Rosetta Script Sensitive"
    process_label = "Rosetta Script — Sensitive"
    description = (
        "Accepts broader scatter-peak fits, so noisier or overlapping peaks may "
        "be included. Bead sizes are estimated from the 140 nm and 380 nm markers."
    )
    sort_order = 2

    fit_thresholds = {
        "fit_r2_threshold": 0.70,
        "fit_cv_threshold": 0.60,
        "scatter_fit_r2_threshold": -0.10,
        "scatter_fit_cv_threshold": 3.50,
    }

    def get_settings(self) -> list[dict[str, Any]]:
        """Return non-fit settings; this mode keeps its fit thresholds fixed."""
        return [
            dict(setting)
            for setting in super().get_settings()
            if setting.get("name") not in _FIXED_FIT_SETTING_NAMES
        ]

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> Any:
        """Run the marker-anchored Rosetta workflow with fixed fit thresholds."""
        resolved_process_settings = dict(process_settings or {})
        resolved_process_settings.update(self.fit_thresholds)
        return super().run_automatic_action(
            backend=backend,
            detector_channels=detector_channels,
            peak_count=peak_count,
            max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_process_settings,
        )
