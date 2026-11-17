"""Experimental Rosetta mode with prominence and joint scatter mixture fitting."""

from .rosetta_mix_mixture_fitting import find_mixture_scatter_peaks
from .rosetta_mix_modes import RosettaMixSizeAssignmentProcess
from typing import Any


class MixtureRosettaScatterPeakProcess(RosettaMixSizeAssignmentProcess):
    """Identify scatter populations with a joint model in log intensity.

    Fluorescence gates and marker-based sizing follow the existing Rosetta
    workflow. Scatter acceptance uses prominence, separation and bootstrap
    stability; histogram R² is not an acceptance criterion.
    """

    process_name = "Rosetta Script Mixture"
    process_label = "Rosetta — Mixture (Experimental)"
    description = (
        "Uses fluorescence gates and a joint mixture fit of log scatter intensity. "
        "Uses sensitive peak detection with local noise checks and stable fitted centers. "
        "Experimental: compare against known standards before using calibration results."
    )
    sort_order = 3
    scatter_fit_function = staticmethod(find_mixture_scatter_peaks)

    def get_settings(self) -> list[dict[str, Any]]:
        """Return workflow settings excluding the unused scatter R² threshold.

        Returns
        -------
        list[dict[str, Any]]
            Controls supported by the fluorescence and mixture workflow.
        """
        settings = [
            dict(setting) for setting in super().get_settings()
            if setting.get("name") != "scatter_fit_r2_threshold"
        ]
        for setting in settings:
            if setting.get("name") == "fit_r2_threshold":
                setting["default_value"] = 0.70
        return settings

    def run_automatic_action(
        self,
        *,
        backend: Any,
        detector_channels: dict[str, Any],
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> Any:
        """Run mixture detection using this mode's declared default settings.

        Parameters
        ----------
        backend : Any
            Current FCS data backend.
        detector_channels : dict[str, Any]
            Selected scattering and fluorescence channel names.
        peak_count : Any
            Maximum scatter population count.
        max_events_for_analysis : Any
            Maximum number of events to analyze.
        process_settings : dict[str, Any]
            Explicit settings, which override this mode's defaults.

        Returns
        -------
        Any
            Existing Rosetta result with peaks or an explanatory warning.
        """
        resolved_settings = {
            setting["name"]: setting["default_value"]
            for setting in self.get_settings()
        }
        resolved_settings.update(process_settings or {})
        return super().run_automatic_action(
            backend=backend, detector_channels=detector_channels,
            peak_count=peak_count, max_events_for_analysis=max_events_for_analysis,
            process_settings=resolved_settings,
        )
