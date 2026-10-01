"""Scattering application."""

import logging
from typing import Any

import numpy as np

from .calibration_models import ScatteringApplicationResult, ScatteringCalibration
from .mie_relation import MieRelation

logger = logging.getLogger(__name__)


def apply_scattering_calibration(
    *,
    calibration: ScatteringCalibration,
    measured_values: np.ndarray,
    target_mie_relation: MieRelation,
    metadata: dict[str, Any] | None = None,
) -> ScatteringApplicationResult:
    """
    Apply a scattering calibration using a target particle Mie relation.
    """
    logger.debug(
        "apply_scattering_calibration called with calibration_source_channel=%r metadata_keys=%r",
        calibration.source_channel,
        sorted((metadata or {}).keys()),
    )

    application_payload = calibration.apply_to_measured_values(
        measured_values=measured_values,
        target_mie_relation=target_mie_relation,
    )

    estimated_coupling = application_payload["estimated_coupling"]
    mie_equivalent_diameter_nm = application_payload["mie_equivalent_diameter_nm"]

    warnings: list[str] = []

    if not target_mie_relation.is_monotonic:
        warnings.append(
            "Target Mie relation is not monotonic. Diameter inversion may be ambiguous."
        )

    if np.any(
        ~np.isfinite(
            mie_equivalent_diameter_nm,
        )
    ):
        warnings.append(
            "Some measured values are outside the valid target Mie relation range."
        )

    logger.debug(
        "apply_scattering_calibration produced estimated_coupling_count=%r "
        "mie_equivalent_diameter_count=%r warnings=%r",
        len(estimated_coupling),
        len(mie_equivalent_diameter_nm),
        warnings,
    )

    return ScatteringApplicationResult(
        estimated_coupling=[
            float(value)
            for value in estimated_coupling
        ],
        mie_equivalent_diameter_nm=[
            float(value)
            if np.isfinite(
                value,
            )
            else np.nan
            for value in mie_equivalent_diameter_nm
        ],
        target_mie_relation=target_mie_relation,
        warnings=warnings,
        metadata=dict(
            metadata or {},
        ),
    )
