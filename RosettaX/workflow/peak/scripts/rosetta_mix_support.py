"""Input validation and signal helpers for Rosetta peak detection."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from RosettaX.utils.reader import FCSFile

from .base import build_edge_pileup_mask as shared_build_edge_pileup_mask

logger = logging.getLogger(__name__)


def unique_sorted_finite_values(values: list[float]) -> list[float]:
    """
    Return sorted unique finite floats with near-duplicate values collapsed.
    """
    resolved_values: list[float] = []

    for raw_value in values:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if not np.isfinite(value):
            continue

        if any(
            np.isclose(
                value,
                existing_value,
                rtol=0.0,
                atol=max(abs(existing_value) * 1e-6, 1e-9),
            )
            for existing_value in resolved_values
        ):
            continue

        resolved_values.append(value)

    return sorted(resolved_values)


def resolve_integer(
    *,
    value: Any,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Resolve a bounded integer value.
    """
    try:
        resolved_value = int(value)
    except (TypeError, ValueError):
        resolved_value = int(default)

    return max(int(minimum), min(int(maximum), int(resolved_value)))


def resolve_float(
    *,
    value: Any,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Resolve a bounded floating-point value.
    """
    try:
        resolved_value = float(value)
    except (TypeError, ValueError):
        resolved_value = float(default)

    if not np.isfinite(resolved_value):
        resolved_value = float(default)

    return max(float(minimum), min(float(maximum), float(resolved_value)))


def resolve_enabled_setting(
    *,
    value: Any,
    default: bool,
) -> bool:
    """
    Resolve one checkbox/switch style setting into a boolean.
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value == "enabled"

    if isinstance(value, (list, tuple, set)):
        return "enabled" in value

    return bool(default)


def resolve_saturation_intensity(
    *,
    values: np.ndarray,
    saturation_quantile: float,
) -> float:
    """
    Estimate saturation intensity from a high fluorescence quantile.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        return float("inf")

    return float(np.quantile(values, float(saturation_quantile)))


def build_saturated_event_mask(
    *,
    scattering_values: np.ndarray,
    fluorescence_values: np.ndarray,
) -> np.ndarray:
    """
    Return a mask for obvious detector-floor and detector-ceiling pile-up events.

    Saturation is approximated from strong pile-ups at detector edges:
    - fluorescence minimum
    - scatter minimum
    - scatter maximum
    """
    scattering_values = np.asarray(scattering_values, dtype=float)
    fluorescence_values = np.asarray(fluorescence_values, dtype=float)

    if scattering_values.size == 0 or fluorescence_values.size == 0:
        return np.zeros_like(scattering_values, dtype=bool)

    fluorescence_floor_mask = build_edge_pileup_mask(
        values=fluorescence_values,
        edge="min",
    )
    scatter_floor_mask = build_edge_pileup_mask(
        values=scattering_values,
        edge="min",
    )
    scatter_ceiling_mask = build_edge_pileup_mask(
        values=scattering_values,
        edge="max",
    )

    return fluorescence_floor_mask | scatter_floor_mask | scatter_ceiling_mask


def filter_table_points_by_saturation_guard(
    *,
    table_points: list[dict[str, float]],
    backend: Any,
    scattering_column: str,
    saturation_guard_fraction: float,
    scattering_values: np.ndarray,
    saturation_resolver: Callable[..., tuple[float | None, str | None]] | None = None,
) -> tuple[list[dict[str, float]], int, float | None, float | None, str | None]:
    if not np.isfinite(float(saturation_guard_fraction)):
        return list(table_points), 0, None, None, None

    if float(saturation_guard_fraction) <= 0.0:
        return list(table_points), 0, None, None, None

    (
        scattering_saturation_value,
        scattering_saturation_source,
    ) = (saturation_resolver or resolve_scattering_saturation_value_for_guard)(
        backend=backend,
        detector_column=scattering_column,
        scattering_values=scattering_values,
    )

    if scattering_saturation_value is None:
        return list(table_points), 0, None, None, scattering_saturation_source

    saturation_guard_threshold = float(scattering_saturation_value) * float(
        saturation_guard_fraction
    )

    if not np.isfinite(saturation_guard_threshold) or saturation_guard_threshold <= 0.0:
        return (
            list(table_points),
            0,
            None,
            float(scattering_saturation_value),
            scattering_saturation_source,
        )

    filtered_table_points: list[dict[str, float]] = []
    removed_peak_count = 0

    for table_point in table_points:
        x_value = float(table_point.get("x", 0.0))

        if np.isfinite(x_value) and x_value > saturation_guard_threshold:
            removed_peak_count += 1
            continue

        filtered_table_points.append(dict(table_point))

    return (
        filtered_table_points,
        removed_peak_count,
        saturation_guard_threshold,
        float(scattering_saturation_value),
        scattering_saturation_source,
    )


def resolve_scattering_saturation_value_for_guard(
    *,
    backend: Any,
    detector_column: str,
    scattering_values: np.ndarray,
    metadata_resolver: Callable[..., float | None] | None = None,
    data_resolver: Callable[..., float | None] | None = None,
) -> tuple[float | None, str | None]:
    resolve_metadata = (
        metadata_resolver or resolve_detector_channel_saturation_value_from_metadata
    )
    resolve_data = data_resolver or resolve_scattering_saturation_value_from_data
    metadata_saturation_value = resolve_metadata(
        backend=backend,
        detector_column=detector_column,
    )

    data_saturation_value = resolve_data(
        scattering_values=scattering_values,
    )

    if metadata_saturation_value is None:
        return None, None

    if data_saturation_value is None:
        return float(metadata_saturation_value), "metadata"

    if metadata_saturation_value <= 1.0 and data_saturation_value > 1.0:
        logger.debug(
            "Ignoring suspicious scatter metadata saturation=%r for detector=%r; using data fallback=%r.",
            metadata_saturation_value,
            detector_column,
            data_saturation_value,
        )
        return float(data_saturation_value), "data-fallback"

    if metadata_saturation_value < (data_saturation_value * 0.05):
        logger.debug(
            "Ignoring low scatter metadata saturation=%r for detector=%r compared to data scale=%r; using data fallback.",
            metadata_saturation_value,
            detector_column,
            data_saturation_value,
        )
        return float(data_saturation_value), "data-fallback"

    return float(metadata_saturation_value), "metadata"


def resolve_scattering_saturation_value_from_data(
    *,
    scattering_values: np.ndarray,
) -> float | None:
    resolved_values = np.asarray(scattering_values, dtype=float)

    if resolved_values.size == 0:
        return None

    finite_values = resolved_values[np.isfinite(resolved_values)]

    if finite_values.size == 0:
        return None

    finite_maximum = float(np.max(finite_values))

    if not np.isfinite(finite_maximum) or finite_maximum <= 0.0:
        return None

    return finite_maximum


def resolve_detector_channel_saturation_value_from_metadata(
    *,
    backend: Any,
    detector_column: str,
) -> float | None:
    uploaded_fcs_path = str(
        getattr(backend, "fcs_file_path", "") or "",
    ).strip()

    if not uploaded_fcs_path:
        return None

    normalized_detector_column = str(detector_column or "").strip().lower()

    if not normalized_detector_column:
        return None

    if not Path(uploaded_fcs_path).exists():
        logger.debug(
            "Metadata saturation source file is missing for detector_column=%r fcs=%r",
            detector_column,
            uploaded_fcs_path,
        )
        return None

    try:
        with FCSFile(uploaded_fcs_path) as fcs_file:
            metadata = fcs_file.get_metadata()
    except Exception:
        logger.debug(
            "Could not read metadata saturation for detector_column=%r fcs=%r",
            detector_column,
            uploaded_fcs_path,
            exc_info=True,
        )
        return None

    for detector in metadata.detectors.values():
        detector_name = str(detector.get("N", "")).strip().lower()

        if detector_name != normalized_detector_column:
            continue

        try:
            detector_saturation_value = float(detector.get("R"))
        except (TypeError, ValueError):
            return None

        if (
            not np.isfinite(detector_saturation_value)
            or detector_saturation_value <= 0.0
        ):
            return None

        return float(detector_saturation_value)

    return None


def build_edge_pileup_mask(
    *,
    values: np.ndarray,
    edge: str,
    quantile: float = 0.9995,
    minimum_fraction: float = 0.001,
) -> np.ndarray:
    """
    Detect a pile-up at one detector edge and return the affected-event mask.
    """
    return shared_build_edge_pileup_mask(
        values=values,
        edge=edge,
        quantile=quantile,
        minimum_fraction=minimum_fraction,
    )
