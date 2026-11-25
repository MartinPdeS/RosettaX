"""Settings and structured results for the Rosetta bead workflow."""

import numpy as np
from .base import resolve_edge_artifact_filter_enabled, resolve_peak_event_limit
from .rosetta_mix_support import (
    resolve_enabled_setting,
    resolve_float,
    resolve_integer,
)
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypedDict

DEFAULT_BASELINE_SIGMA_MULTIPLIER = 3.0
DEFAULT_SATURATION_GUARD_FRACTION = 0.8


class RosettaDetectionIssue(StrEnum):
    """The stage at which Rosetta detection stopped."""

    EVENTS_MISSING = "events_missing"
    FLUORESCENCE_MISSING = "fluorescence_missing"
    MARKER_MISSING = "marker_missing"
    MARKER_AMBIGUOUS = "marker_ambiguous"
    SCATTER_MISSING = "scatter_missing"
    GATE_AMBIGUOUS = "gate_ambiguous"


class RosettaAssignmentState(StrEnum):
    """Whether sizing can be used and whether measured rows are retained."""

    ASSIGNED = "assigned"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"
    FAILED = "failed"


@dataclass(frozen=True, kw_only=True)
class RosettaSizeAssignment:
    """Resolved rows, validation outcome, and evidence for a size assignment."""

    rows: list[dict[str, Any]] = field(default_factory=list)
    state: RosettaAssignmentState = RosettaAssignmentState.ASSIGNED
    detail: str = ""
    summary: str = ""
    notices: tuple[str, ...] = ()
    rejection_reasons: tuple[str, ...] = ()
    needs_confirmation: bool = False
    clipped_marker_nm: int | None = None
    failure_code: str | None = None
    unsized_reasons: dict[float, str] = field(default_factory=dict)

    @property
    def status(self) -> str:
        """Render the assignment outcome in the process status area."""
        prefix = {
            RosettaAssignmentState.PARTIAL: "Partial result:",
            RosettaAssignmentState.FAILED: "Warning:",
        }.get(self.state, "")
        return " ".join(filter(None, (prefix, self.detail, *self.rejection_reasons, *self.notices)))

    def to_diagnostics(self) -> dict[str, Any]:
        """Serialize the sizing state for the graph, UI, and regression tests."""
        return {
            "state": self.state.value,
            "summary": self.summary or next(iter(self.rejection_reasons), self.detail),
            "assigned_row_count": sum(bool(row.get("particle_diameter_nm")) for row in self.rows),
            "measured_row_count": len(self.rows),
            "needs_confirmation": self.needs_confirmation,
            "rejection_reasons": list(self.rejection_reasons),
            "clipped_marker_nm": self.clipped_marker_nm,
            "failure_code": self.failure_code,
            "unsized_peaks": [{"position": x, "reason": reason} for x, reason in self.unsized_reasons.items()],
        }


ROSETTA_SETTINGS = {setting["name"]: setting for setting in [
    {
        "name": "peak_count",
        "kind": "integer",
        "label": "Maximum number of scatter peaks",
        "default_value": 10,
        "min_value": 1,
        "max_value": 20,
        "step": 1,
    },
    {
        "name": "fit_r2_threshold",
        "kind": "float",
        "label": "Minimum fit R\u00b2",
        "help": (
            "Minimum Gaussian fit quality for a peak to be accepted. "
            "Lower values accept noisier peaks."
        ),
        "default_value": 0.85,
        "min_value": 0.00,
        "max_value": 0.999,
        "step": 0.01,
    },
    {
        "name": "baseline_sigma_multiplier",
        "kind": "float",
        "label": "Baseline gate width (\u03c3)",
        "help": (
            "Events within this many standard deviations of the baseline "
            "fluorescence peak are treated as non-fluorescent."
        ),
        "default_value": DEFAULT_BASELINE_SIGMA_MULTIPLIER,
        "min_value": 0.5,
        "max_value": 5.0,
        "step": 0.5,
    },
    {
        "name": "fit_cv_threshold",
        "kind": "float",
        "label": "Maximum fluorescence peak CV",
        "help": (
            "Maximum width allowed for fluorescence peaks during Rosetta "
            "marker validation. CV is represented as std/mean, so 0.10 "
            "corresponds to 10%."
        ),
        "default_value": 0.60,
        "min_value": 0.05,
        "max_value": 2.0,
        "step": 0.01,
    },
    {
        "name": "scatter_fit_r2_threshold",
        "kind": "float",
        "label": "Minimum scatter fit R\u00b2",
        "help": (
            "Minimum Gaussian fit quality for scatter peaks. This is kept "
            "separate from fluorescence so partially resolved scatter peaks "
            "can still be accepted without relaxing fluorescence validation."
        ),
        "default_value": 0.70,
        "min_value": 0.00,
        "max_value": 0.999,
        "step": 0.01,
    },
    {
        "name": "scatter_fit_cv_threshold",
        "kind": "float",
        "label": "Maximum scatter peak CV",
        "help": (
            "Maximum width allowed for scatter peaks during Rosetta "
            "validation. CV is represented as std/mean, so 0.10 "
            "corresponds to 10%."
        ),
        "default_value": 1.0,
        "min_value": 0.05,
        "max_value": 3.0,
        "step": 0.01,
    },
    {
        "name": "table_non_fluorescent_only",
        "kind": "boolean",
        "label": "Only output non-fluorescent peaks",
        "help": (
            "When enabled, only baseline-gated non-fluorescent scatter peaks "
            "are inserted into the table. Disable this to also insert "
            "fluorescent marker-associated scatter peaks."
        ),
        "default_value": True,
    },
    {
        "name": "saturation_guard_enabled",
        "kind": "boolean",
        "label": "Enable saturation guard",
        "help": (
            "When enabled, table peaks above saturation guard threshold "
            "are excluded. Disable to keep all table peaks regardless of "
            "saturation metadata."
        ),
        "default_value": True,
    },
    {
        "name": "saturation_guard_fraction",
        "kind": "float",
        "label": "Saturation guard (max / saturation)",
        "help": (
            "Exclude table peaks above detector_saturation * this fraction "
            "for the selected scatter channel when metadata includes "
            "detector range values. This guard does not change detected "
            "peaks or plotted events. Example: 0.6 means 4,000,000 "
            "saturation becomes a 2,400,000 table threshold."
        ),
        "default_value": DEFAULT_SATURATION_GUARD_FRACTION,
        "min_value": 0.0,
        "max_value": 1.0,
        "step": 0.01,
    },
]}

MIXTURE_MARKER_STRICTNESS = {
    "name": "marker_fit_strictness",
    "kind": "slider",
    "label": "Marker fit strictness",
    "help": (
        "0 accepts broader or noisier fluorescence marker peaks. "
        "1 requires narrower peaks and better Gaussian fits. "
        "0.5 is the standard setting."
    ),
    "default_value": 0.5,
    "min_value": 0.0,
    "max_value": 1.0,
    "step": 0.05,
    "marks": {0.0: "Sensitive", 0.5: "Default", 1.0: "Strict"},
}


def resolve_rosetta_setting(
    *, definition: dict[str, Any], value: Any, default: Any = None,
) -> int | float | bool:
    """Coerce a saved setting using the control's declared bounds and default."""
    fallback = definition["default_value"] if default is None else default
    if definition["kind"] == "boolean":
        return resolve_enabled_setting(value=value, default=fallback)
    resolver = resolve_integer if definition["kind"] == "integer" else resolve_float
    return resolver(
        value=value, default=fallback, minimum=definition["min_value"], maximum=definition["max_value"],
    )


class RosettaPeakPoint(TypedDict, total=False):
    """Scatter and fluorescence coordinates in detector arbitrary units."""

    x: float
    y: float
    kind: str
    label: str


class MarkerScatterDiagnostic(TypedDict, total=False):
    """Fit outcome for the scatter events gated by a fluorescence marker."""

    marker_role: str
    fluorescence_position: float
    gated_event_count: int
    validated: bool
    recovered_from_clipped_fluorescence: bool
    scatter_boundary: float
    gate_overlap: float
    above_baseline_fraction: float
    selected_peak: dict[str, Any]
    rejected_peaks: list[dict[str, Any]]


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
        """Normalize external controls while preserving direct-call defaults."""
        resolved_settings = {
            name: resolve_rosetta_setting(
                definition=definition,
                value=peak_count if name == "peak_count" else process_settings.get(name),
                # Older direct calls without a scatter threshold use 0.80.
                default=0.80 if name == "scatter_fit_r2_threshold" else None,
            )
            for name, definition in ROSETTA_SETTINGS.items()
        }
        return cls(
            **resolved_settings,
            max_events_for_analysis=resolve_peak_event_limit(analysis_limit=max_events_for_analysis),
            remove_saturated_events=resolve_edge_artifact_filter_enabled(process_settings=process_settings),
            minimum_peak_fraction=0.03,
            minimum_events_per_peak=35,
            fluorescence_saturation_quantile=0.9995,
            marker_gate_sigma_multiplier=2.0,
        )


class RosettaPlotSource(TypedDict):
    """FCS selection needed to reproduce the event cloud from a detection."""

    fcs_file_path: str
    scattering_column: str
    green_fluorescence_column: str
    max_events_for_analysis: int
    remove_saturated_events: bool


@dataclass(frozen=True)
class RosettaEventData:
    """Paired detector signals and the filtering applied to them."""

    scattering_values: np.ndarray
    fluorescence_values: np.ndarray
    removed_saturated_event_count: int
    scatter_edge_values: dict[str, float] = field(default_factory=dict)
    scatter_edge_fluorescence: dict[str, np.ndarray] = field(default_factory=dict)
    fluorescence_with_scatter_edges: np.ndarray | None = None
    removed_nonfinite_event_count: int = 0
    plot_source: RosettaPlotSource | None = None

    def plot_payload(self) -> dict[str, Any]:
        """Serialize the event cloud and its reproducible FCS selection.

        Returns
        -------
        dict
            Paired scattering and fluorescence values in detector units.
        """
        payload: dict[str, Any] = {
            "plot_x_values": np.asarray(self.scattering_values, dtype=float).tolist(),
            "plot_y_values": np.asarray(self.fluorescence_values, dtype=float).tolist(),
        }
        if self.plot_source is not None:
            payload["rosetta_plot_source"] = dict(self.plot_source)
        return payload

    def event_counts(self) -> dict[str, int]:
        """Return the total and stage-by-stage counts of paired FCS events."""
        retained_count = self.scattering_values.size
        return {
            "read": retained_count + self.removed_nonfinite_event_count + self.removed_saturated_event_count,
            "removed_nonfinite": self.removed_nonfinite_event_count,
            "removed_at_detector_edges": self.removed_saturated_event_count,
            "retained": retained_count,
        }


@dataclass(frozen=True)
class RosettaFluorescenceAnalysis:
    analysis: dict[str, Any]
    baseline_peak: dict[str, Any] | None
    marker_peaks: list[dict[str, Any]]
    baseline_lower_gate: float | None
    baseline_upper_gate: float | None
    saturation_intensity: float
    stop_status: str | None = None
    issue: RosettaDetectionIssue | None = None


@dataclass(frozen=True)
class RosettaMarkerScatter:
    points: list[RosettaPeakPoint]
    guide_positions: list[float]
    diagnostics: list[MarkerScatterDiagnostic] = field(default_factory=list)


@dataclass(frozen=True)
class RosettaScatterAnalysis:
    analysis: dict[str, Any]
    points: list[RosettaPeakPoint]
    positions: list[float]
    diagnostic: str
    stop_status: str | None = None
    gated_event_count: int | None = None
