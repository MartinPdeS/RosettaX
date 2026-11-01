"""Settings and structured results for the Rosetta bead workflow."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import resolve_edge_artifact_filter_enabled
from .rosetta_mix_algorithms import (
    resolve_enabled_setting,
    resolve_float,
    resolve_integer,
)

DEFAULT_BASELINE_SIGMA_MULTIPLIER = 3.0


@dataclass(frozen=True)
class RosettaRunSettings:
    """Validated parameters for one fluorescence-guided scatter detection run."""

    peak_count: int
    max_events_for_analysis: int
    fit_r2_threshold: float
    baseline_sigma_multiplier: float
    fit_cv_threshold: float
    scatter_fit_r2_threshold: float
    scatter_fit_cv_threshold: float
    remove_saturated_events: bool
    table_non_fluorescent_only: bool
    saturation_guard_enabled: bool
    saturation_guard_fraction: float
    minimum_peak_fraction: float
    minimum_events_per_peak: int
    fluorescence_saturation_quantile: float
    marker_gate_sigma_multiplier: float

    @classmethod
    def from_raw_values(
        cls,
        *,
        peak_count: Any,
        max_events_for_analysis: Any,
        process_settings: dict[str, Any],
    ) -> "RosettaRunSettings":
        resolved_peak_count = resolve_integer(
            value=peak_count,
            default=10,
            minimum=1,
            maximum=20,
        )

        resolved_max_events_for_analysis = resolve_integer(
            value=max_events_for_analysis,
            default=10000,
            minimum=1,
            maximum=5_000_000,
        )

        # User-facing settings.
        fit_r2_threshold = resolve_float(
            value=process_settings.get("fit_r2_threshold"),
            default=0.85,
            minimum=0.00,
            maximum=0.999,
        )

        baseline_sigma_multiplier = resolve_float(
            value=process_settings.get("baseline_sigma_multiplier"),
            default=DEFAULT_BASELINE_SIGMA_MULTIPLIER,
            minimum=0.5,
            maximum=5.0,
        )

        fit_cv_threshold = resolve_float(
            value=process_settings.get("fit_cv_threshold"),
            default=0.60,
            minimum=0.05,
            maximum=2.0,
        )

        scatter_fit_r2_threshold = resolve_float(
            value=process_settings.get("scatter_fit_r2_threshold"),
            default=0.80,
            minimum=0.00,
            maximum=0.999,
        )

        scatter_fit_cv_threshold = resolve_float(
            value=process_settings.get("scatter_fit_cv_threshold"),
            default=1.0,
            minimum=0.05,
            maximum=3.0,
        )
        remove_saturated_events = resolve_edge_artifact_filter_enabled(
            process_settings=process_settings,
            default=True,
        )
        table_non_fluorescent_only = resolve_enabled_setting(
            value=process_settings.get("table_non_fluorescent_only"),
            default=True,
        )
        saturation_guard_enabled = resolve_enabled_setting(
            value=process_settings.get("saturation_guard_enabled"),
            default=True,
        )
        saturation_guard_fraction = resolve_float(
            value=process_settings.get("saturation_guard_fraction"),
            default=0.5,
            minimum=0.0,
            maximum=1.0,
        )

        # Internal algorithm constants (not user-configurable).
        minimum_peak_fraction = 0.03
        minimum_events_per_peak = 35
        fluorescence_saturation_quantile = 0.9995
        marker_gate_sigma_multiplier = 2.0

        return cls(
            peak_count=resolved_peak_count,
            max_events_for_analysis=resolved_max_events_for_analysis,
            fit_r2_threshold=fit_r2_threshold,
            baseline_sigma_multiplier=baseline_sigma_multiplier,
            fit_cv_threshold=fit_cv_threshold,
            scatter_fit_r2_threshold=scatter_fit_r2_threshold,
            scatter_fit_cv_threshold=scatter_fit_cv_threshold,
            remove_saturated_events=remove_saturated_events,
            table_non_fluorescent_only=table_non_fluorescent_only,
            saturation_guard_enabled=saturation_guard_enabled,
            saturation_guard_fraction=saturation_guard_fraction,
            minimum_peak_fraction=minimum_peak_fraction,
            minimum_events_per_peak=minimum_events_per_peak,
            fluorescence_saturation_quantile=fluorescence_saturation_quantile,
            marker_gate_sigma_multiplier=marker_gate_sigma_multiplier,
        )


@dataclass(frozen=True)
class RosettaEventData:
    scattering_values: np.ndarray
    fluorescence_values: np.ndarray
    removed_saturated_event_count: int


@dataclass(frozen=True)
class RosettaFluorescenceAnalysis:
    analysis: dict[str, Any]
    baseline_peak: dict[str, Any] | None
    marker_peaks: list[dict[str, Any]]
    baseline_lower_gate: float | None
    baseline_upper_gate: float | None
    saturation_intensity: float
    stop_status: str | None = None


@dataclass(frozen=True)
class RosettaMarkerScatter:
    points: list[dict[str, Any]]
    guide_positions: list[float]


@dataclass(frozen=True)
class RosettaScatterAnalysis:
    analysis: dict[str, Any]
    points: list[dict[str, Any]]
    positions: list[float]
    diagnostic: str
    stop_status: str | None = None
