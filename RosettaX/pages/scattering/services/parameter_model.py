# -*- coding: utf-8 -*-

from typing import Any, Optional

import numpy as np

from RosettaX.pages.scattering.backend import BackEnd
from RosettaX.utils.casting import as_optional_float, as_required_float, as_required_int
from RosettaX.pages.scattering.services.parameter_table import normalize_table_rows


def compute_model_for_rows(
    *,
    mie_model: str,
    current_rows: Optional[list[dict[str, Any]]],
    medium_refractive_index: Any,
    particle_refractive_index: Any,
    core_refractive_index: Any,
    shell_refractive_index: Any,
    wavelength_nm: Any,
    detector_numerical_aperture: Any,
    detector_cache_numerical_aperture: Any,
    detector_sampling: Any,
    logger: Any,
) -> list[dict[str, str]]:
    resolved_rows = [dict(row) for row in (current_rows or [])]

    if not resolved_rows:
        return []

    try:
        resolved_medium_refractive_index = as_required_float(
            medium_refractive_index,
            "medium_refractive_index",
        )
        resolved_wavelength_nm = as_required_float(
            wavelength_nm,
            "wavelength_nm",
        )
        resolved_detector_numerical_aperture = as_required_float(
            detector_numerical_aperture,
            "detector_numerical_aperture",
        )
        resolved_detector_cache_numerical_aperture = as_required_float(
            detector_cache_numerical_aperture,
            "detector_cache_numerical_aperture",
        )
        resolved_detector_sampling = as_required_int(
            detector_sampling,
            "detector_sampling",
        )
    except Exception:
        logger.exception("compute_model_for_rows aborted because optical parameters are invalid.")
        return normalize_table_rows(
            mie_model=mie_model,
            current_rows=resolved_rows,
        )

    logger.debug(
        "compute_model_for_rows resolved optical parameters medium_refractive_index=%r wavelength_nm=%r detector_numerical_aperture=%r detector_cache_numerical_aperture=%r detector_sampling=%r",
        resolved_medium_refractive_index,
        resolved_wavelength_nm,
        resolved_detector_numerical_aperture,
        resolved_detector_cache_numerical_aperture,
        resolved_detector_sampling,
    )

    if mie_model == "Core/Shell Sphere":
        logger.debug("compute_model_for_rows running in Core/Shell Sphere mode.")
        try:
            _resolved_core_refractive_index = as_required_float(
                core_refractive_index,
                "core_refractive_index",
            )
            resolved_shell_refractive_index = as_required_float(
                shell_refractive_index,
                "shell_refractive_index",
            )
        except Exception:
            logger.exception("compute_model_for_rows aborted because core/shell refractive indices are invalid.")
            return normalize_table_rows(
                mie_model=mie_model,
                current_rows=resolved_rows,
            )

        valid_row_indices: list[int] = []
        outer_diameters_nm: list[float] = []

        updated_rows = normalize_table_rows(
            mie_model=mie_model,
            current_rows=resolved_rows,
        )

        for row_index, row in enumerate(updated_rows):
            outer_diameter_nm = as_optional_float(row.get("outer_diameter_nm"))
            if outer_diameter_nm is None or outer_diameter_nm <= 0.0:
                updated_rows[row_index]["expected_coupling"] = ""
                continue

            valid_row_indices.append(row_index)
            outer_diameters_nm.append(float(outer_diameter_nm))

        logger.debug(
            "compute_model_for_rows core-shell valid_row_indices=%r outer_diameters_nm=%r",
            valid_row_indices,
            outer_diameters_nm,
        )

        if not outer_diameters_nm:
            logger.debug("compute_model_for_rows found no valid core-shell rows.")
            return updated_rows

        try:
            modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
                particle_diameters_nm=np.asarray(outer_diameters_nm, dtype=float),
                wavelength_nm=resolved_wavelength_nm,
                source_numerical_aperture=0.1,
                optical_power_watt=1.0,
                detector_numerical_aperture=resolved_detector_numerical_aperture,
                medium_refractive_index=resolved_medium_refractive_index,
                particle_refractive_index=resolved_shell_refractive_index,
                detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
                detector_phi_offset_degree=0.0,
                detector_gamma_offset_degree=0.0,
                polarization_angle_degree=0.0,
                detector_sampling=resolved_detector_sampling,
            )
        except Exception:
            logger.exception("compute_model_for_rows failed during core-shell outer-diameter approximation.")
            return updated_rows

        for row_index, expected_coupling in zip(
            valid_row_indices,
            modeled_coupling_result.expected_coupling_values,
            strict=False,
        ):
            updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

        logger.debug("compute_model_for_rows returning updated core-shell rows=%r", updated_rows)
        return updated_rows

    logger.debug("compute_model_for_rows running in Solid Sphere mode.")

    try:
        resolved_particle_refractive_index = as_required_float(
            particle_refractive_index,
            "particle_refractive_index",
        )
    except Exception:
        logger.exception("compute_model_for_rows aborted because particle refractive index is invalid.")
        return normalize_table_rows(
            mie_model=mie_model,
            current_rows=resolved_rows,
        )

    valid_row_indices: list[int] = []
    particle_diameters_nm: list[float] = []

    updated_rows = normalize_table_rows(
        mie_model=mie_model,
        current_rows=resolved_rows,
    )

    for row_index, row in enumerate(updated_rows):
        particle_diameter_nm = as_optional_float(row.get("particle_diameter_nm"))
        if particle_diameter_nm is None or particle_diameter_nm <= 0.0:
            updated_rows[row_index]["expected_coupling"] = ""
            continue

        valid_row_indices.append(row_index)
        particle_diameters_nm.append(float(particle_diameter_nm))

    logger.debug(
        "compute_model_for_rows solid-sphere valid_row_indices=%r particle_diameters_nm=%r",
        valid_row_indices,
        particle_diameters_nm,
    )

    if not particle_diameters_nm:
        logger.debug("compute_model_for_rows found no valid solid-sphere rows.")
        return updated_rows

    try:
        modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
            particle_diameters_nm=np.asarray(particle_diameters_nm, dtype=float),
            wavelength_nm=resolved_wavelength_nm,
            source_numerical_aperture=0.1,
            optical_power_watt=1.0,
            detector_numerical_aperture=resolved_detector_numerical_aperture,
            medium_refractive_index=resolved_medium_refractive_index,
            particle_refractive_index=resolved_particle_refractive_index,
            detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
            detector_phi_offset_degree=0.0,
            detector_gamma_offset_degree=0.0,
            polarization_angle_degree=0.0,
            detector_sampling=resolved_detector_sampling,
        )
    except Exception:
        logger.exception("compute_model_for_rows failed during solid-sphere coupling computation.")
        return updated_rows

    for row_index, expected_coupling in zip(
        valid_row_indices,
        modeled_coupling_result.expected_coupling_values,
        strict=False,
    ):
        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

    logger.debug("compute_model_for_rows returning updated solid-sphere rows=%r", updated_rows)
    return updated_rows