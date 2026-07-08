# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CrossCalibrationPoint:
    """
    One paired primary and secondary bead reference point.
    """

    bead_index: int
    x_value: float
    y_value: float
    primary_reference_value: float
    primary_measured_value: float | None = None
    secondary_measured_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bead_index": int(self.bead_index),
            "x_value": float(self.x_value),
            "y_value": float(self.y_value),
            "primary_reference_value": float(self.primary_reference_value),
            "primary_measured_value": self.primary_measured_value,
            "secondary_measured_value": self.secondary_measured_value,
        }


@dataclass(frozen=True)
class CrossCalibrationResult:
    """
    Result of fitting one transfer calibration from secondary to primary scale.
    """

    primary_file_name: str
    secondary_file_name: str
    calibration_type: str
    source_channel: str
    x_quantity: str
    x_axis_label: str
    y_quantity: str
    y_axis_label: str
    fit_model: str
    slope: float
    intercept: float
    r_squared: float
    point_count: int
    warnings: list[str] = field(default_factory=list)
    points: list[CrossCalibrationPoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_file_name": str(self.primary_file_name),
            "secondary_file_name": str(self.secondary_file_name),
            "calibration_type": str(self.calibration_type),
            "source_channel": str(self.source_channel),
            "x_quantity": str(self.x_quantity),
            "x_axis_label": str(self.x_axis_label),
            "y_quantity": str(self.y_quantity),
            "y_axis_label": str(self.y_axis_label),
            "fit_model": str(self.fit_model),
            "slope": float(self.slope),
            "intercept": float(self.intercept),
            "r_squared": float(self.r_squared),
            "point_count": int(self.point_count),
            "warnings": [str(item) for item in self.warnings],
            "points": [point.to_dict() for point in self.points],
        }
