# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from RosettaX.workflow import scattering

from .mie_relation_builder import build_target_mie_relation
from .models import ScatteringApplyResult
from .models import ScatteringOutputColumns
from .models import ScatteringTargetModelParameters
from .monotonic import coupling_to_diameter_with_linear_extrapolation
from .monotonic import resolve_monotonic_target_mie_relation


logger = logging.getLogger(__name__)


def calibration_is_scattering_v2(
    calibration_payload: dict[str, Any],
) -> bool:
    """
    Return whether the payload is a scattering version 2 calibration.
    """
    if not isinstance(calibration_payload, dict):
        logger.debug(
            "calibration_is_scattering_v2 returning False because payload is not a dict. "
            "payload_type=%s",
            type(calibration_payload).__name__,
        )
        return False

    calibration_type = str(
        calibration_payload.get(
            "calibration_type",
            "",
        )
    ).strip()

    calibration_version = int(
        calibration_payload.get(
            "version",
            0,
        )
        or 0
    )

    result = calibration_type == "scattering" and calibration_version >= 2

    logger.debug(
        "calibration_is_scattering_v2 calibration_type=%r calibration_version=%r result=%r",
        calibration_type,
        calibration_version,
        result,
    )

    return result


def build_scattering_output_columns(
    *,
    source_channel: str,
) -> ScatteringOutputColumns:
    """
    Build scattering output column names.
    """
    source_channel_string = str(
        source_channel,
    )

    output_columns = ScatteringOutputColumns(
        estimated_coupling=f"{source_channel_string}_estimated_coupling",
        mie_equivalent_diameter_nm=f"{source_channel_string}_mie_equivalent_diameter_nm",
    )

    logger.debug(
        "build_scattering_output_columns returning output_columns=%r",
        output_columns,
    )

    return output_columns


def apply_scattering_calibration_to_dataframe(
    *,
    dataframe: Any,
    source_channel: str,
    output_channel_names: list[str] | None = None,
    calibration_payload: dict[str, Any],
    target_model_parameters: ScatteringTargetModelParameters,
    metadata: Optional[dict[str, Any]] = None,
) -> ScatteringApplyResult:
    """
    Apply a scattering calibration to a dataframe.

    The source channel is preserved. Two derived columns are added:

    - estimated coupling
    - target model Mie equivalent diameter

    If the full target Mie relation is not strictly monotonic, the widest
    strictly monotonic branch is selected automatically. Diameter inversion uses
    linear extrapolation outside the selected branch coupling range.
    """
    logger.debug(
        "apply_scattering_calibration_to_dataframe called with source_channel=%r "
        "dataframe_shape=%r target_model_parameters=%r metadata_keys=%r",
        source_channel,
        getattr(dataframe, "shape", None),
        target_model_parameters,
        sorted((metadata or {}).keys()),
    )

    if source_channel not in dataframe.columns:
        raise ValueError(
            f'Source channel "{source_channel}" is missing from the input dataframe.'
        )

    full_target_mie_relation = build_target_mie_relation(
        calibration_payload=calibration_payload,
        target_model_parameters=target_model_parameters,
    )

    relation_resolution = resolve_monotonic_target_mie_relation(
        target_mie_relation=full_target_mie_relation,
    )

    scattering_calibration = scattering.ScatteringCalibration.from_dict(
        calibration_payload,
    )

    source_values = dataframe[source_channel].to_numpy(
        copy=True,
    )

    _log_array_summary(
        name="apply_source_values",
        values=source_values,
    )

    estimated_coupling = scattering_calibration.measured_to_coupling(
        source_values,
    )

    _log_array_summary(
        name="apply_estimated_coupling",
        values=estimated_coupling,
    )

    mie_equivalent_diameter_nm = coupling_to_diameter_with_linear_extrapolation(
        target_mie_relation=relation_resolution.target_mie_relation,
        coupling_values=estimated_coupling,
    )

    _log_array_summary(
        name="apply_mie_equivalent_diameter_nm",
        values=mie_equivalent_diameter_nm,
    )

    if output_channel_names is None:
        output_columns = build_scattering_output_columns(
            source_channel=source_channel,
        )
    else:
        if len(output_channel_names) != 1:
            raise ValueError(
                "Scattering output_channel_names must contain exactly 1 entry."
            )

        output_columns = ScatteringOutputColumns(
            estimated_coupling="",
            mie_equivalent_diameter_nm=str(output_channel_names[0]).strip(),
        )

    output_dataframe = dataframe.copy(
        deep=True,
    )

    output_dataframe[output_columns.mie_equivalent_diameter_nm] = np.asarray(
        mie_equivalent_diameter_nm,
        dtype=float,
    )

    logger.debug(
        "apply_scattering_calibration_to_dataframe returning output_dataframe_shape=%r "
        "output_columns=%r warning_count=%r",
        getattr(output_dataframe, "shape", None),
        output_columns.as_list(),
        len(relation_resolution.warnings),
    )

    warnings = list(
        relation_resolution.warnings,
    )
    reference_peak_roundtrip_warning = _build_reference_peak_roundtrip_warning(
        scattering_calibration=scattering_calibration,
        target_mie_relation=relation_resolution.target_mie_relation,
    )

    if reference_peak_roundtrip_warning:
        warnings.append(
            reference_peak_roundtrip_warning,
        )

    return ScatteringApplyResult(
        dataframe=output_dataframe,
        output_columns=output_columns.as_list(),
        warnings=warnings,
        target_mie_relation=relation_resolution.target_mie_relation,
    )


def _build_reference_peak_roundtrip_warning(
    *,
    scattering_calibration: scattering.ScatteringCalibration,
    target_mie_relation: scattering.MieRelation,
) -> str:
    """
    Build a compact round-trip diagnostic for saved calibration centroids.
    """
    reference_rows = getattr(
        scattering_calibration,
        "reference_table",
        [],
    )

    roundtrip_entries: list[tuple[float, float, float]] = []

    for row in reference_rows:
        if not isinstance(row, dict):
            continue

        try:
            nominal_diameter_nm = float(
                row.get("particle_diameter_nm", ""),
            )
            measured_peak_position = float(
                row.get("measured_peak_position", ""),
            )
        except (TypeError, ValueError):
            continue

        if not np.isfinite(nominal_diameter_nm) or not np.isfinite(measured_peak_position):
            continue

        estimated_coupling = scattering_calibration.measured_to_coupling(
            np.asarray([measured_peak_position], dtype=float),
        )
        roundtrip_diameter_nm = coupling_to_diameter_with_linear_extrapolation(
            target_mie_relation=target_mie_relation,
            coupling_values=estimated_coupling,
        )

        if roundtrip_diameter_nm.size != 1 or not np.isfinite(roundtrip_diameter_nm[0]):
            continue

        roundtrip_entries.append(
            (
                nominal_diameter_nm,
                measured_peak_position,
                float(roundtrip_diameter_nm[0]),
            )
        )

    if not roundtrip_entries:
        return ""

    roundtrip_entries.sort(
        key=lambda entry: entry[0],
    )
    preview_entries = roundtrip_entries[:6]
    formatted_entries = "; ".join(
        (
            f"{nominal_diameter_nm:.6g} nm @ {measured_peak_position:.6g} -> "
            f"{roundtrip_diameter_nm:.6g} nm"
        )
        for nominal_diameter_nm, measured_peak_position, roundtrip_diameter_nm in preview_entries
    )

    if len(roundtrip_entries) > len(preview_entries):
        formatted_entries = (
            f"{formatted_entries}; ... ({len(roundtrip_entries)} reference peaks total)"
        )

    return (
        "Reference peak round-trip check on saved calibration centroids: "
        f"{formatted_entries}."
    )


def _log_array_summary(
    *,
    name: str,
    values: Any,
) -> None:
    """
    Log a compact numerical summary of an array.
    """
    try:
        array = np.asarray(
            values,
            dtype=float,
        ).reshape(-1)
    except Exception:
        logger.debug(
            "%s summary unavailable because conversion to float array failed. raw_type=%s",
            name,
            type(values).__name__,
        )
        return

    finite_mask = np.isfinite(
        array,
    )

    finite_values = array[finite_mask]

    if finite_values.size == 0:
        logger.debug(
            "%s summary: size=%r finite_count=0 nan_count=%r inf_count=%r values=%r",
            name,
            array.size,
            int(np.sum(np.isnan(array))),
            int(np.sum(np.isinf(array))),
            array.tolist(),
        )
        return

    logger.debug(
        "%s summary: size=%r finite_count=%r nan_count=%r inf_count=%r min=%r max=%r first_values=%r",
        name,
        array.size,
        finite_values.size,
        int(np.sum(np.isnan(array))),
        int(np.sum(np.isinf(array))),
        float(np.min(finite_values)),
        float(np.max(finite_values)),
        array[:10].tolist(),
    )
