# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AxisOptions:
    """Scale options shared by histogram and scatter plots."""

    x_log: bool = False
    y_log: bool = False
    color_log: bool = False


@dataclass(frozen=True)
class PlotStyleOptions:
    """Visual defaults shared by every plot family."""

    marker_size: float = 7.0
    marker_opacity: float = 0.72
    line_width: float = 2.0
    font_size: float = 14.0
    tick_size: float = 12.0
    show_grid: bool = True
    height_px: Optional[int] = None

    def __post_init__(self) -> None:
        if float(self.marker_size) <= 0.0:
            raise ValueError("Plot marker_size must be greater than zero.")
        if not 0.0 <= float(self.marker_opacity) <= 1.0:
            raise ValueError("Plot marker_opacity must be between 0 and 1.")
        if float(self.line_width) <= 0.0:
            raise ValueError("Plot line_width must be greater than zero.")
        if float(self.font_size) <= 0.0 or float(self.tick_size) <= 0.0:
            raise ValueError("Plot font and tick sizes must be greater than zero.")
        if self.height_px is not None and int(self.height_px) <= 0:
            raise ValueError("Plot height_px must be greater than zero.")


@dataclass(frozen=True)
class HistogramOptions:
    """Validated options for a 1D histogram plot."""

    bin_count: int = 180
    max_events: Optional[int] = None
    axes: AxisOptions = field(default_factory=AxisOptions)
    style: PlotStyleOptions = field(default_factory=PlotStyleOptions)

    def __post_init__(self) -> None:
        if int(self.bin_count) < 1:
            raise ValueError("Histogram bin_count must be at least 1.")
        if self.max_events is not None and int(self.max_events) < 1:
            raise ValueError("Histogram max_events must be at least 1.")


@dataclass(frozen=True)
class SmoothingOptions:
    """Validated options for smoothed histogram counts."""

    sigma_points: float = 2.0

    def __post_init__(self) -> None:
        if float(self.sigma_points) < 0.0:
            raise ValueError("Smoothing sigma_points cannot be negative.")


@dataclass(frozen=True)
class SmoothedHistogramOptions(HistogramOptions):
    """Options for the smoothed 1D histogram plot family."""

    smoothing: SmoothingOptions = field(default_factory=SmoothingOptions)


@dataclass(frozen=True)
class ScatterOptions:
    """Shared visual options for a 2D scatter plot."""

    max_events: Optional[int] = None
    marker_size: float = 5.0
    marker_opacity: float = 0.72
    density_bin_count: int = 120
    axes: AxisOptions = field(default_factory=AxisOptions)
    style: PlotStyleOptions = field(default_factory=PlotStyleOptions)

    def __post_init__(self) -> None:
        if float(self.marker_size) <= 0.0:
            raise ValueError("Scatter marker_size must be greater than zero.")
        if not 0.0 <= float(self.marker_opacity) <= 1.0:
            raise ValueError("Scatter marker_opacity must be between 0 and 1.")
        if self.max_events is not None and int(self.max_events) < 1:
            raise ValueError("Scatter max_events must be at least 1.")
        if int(self.density_bin_count) < 1:
            raise ValueError("Scatter density_bin_count must be at least 1.")
