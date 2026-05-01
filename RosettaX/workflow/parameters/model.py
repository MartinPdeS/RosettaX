# -*- coding: utf-8 -*-

from typing import Any, Optional
import logging

import numpy as np

from RosettaX.pages.p03_scattering.backend import BackEnd
from RosettaX.utils.casting import as_optional_float, as_required_float, as_required_int
from . import table


SOLID_SPHERE_MODEL_NAME = "Solid Sphere"
CORE_SHELL_SPHERE_MODEL_NAME = "Core/Shell Sphere"


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
    blocker_bar_numerical_aperture: Any,
    detector_sampling: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
    logger: logging.Logger,
) -> list[dict[str, str]]:
    """
    Compute Mie scattering model values for all rows in the parameter table.

    The function validates the shared optical parameters, normalizes the table
    rows, then delegates to the solid sphere or core shell sphere computation
    branch.

    Rows with missing, invalid, or non positive geometric parameters are kept
    in the table but their ``expected_coupling`` cell is cleared.

    Parameters
    ----------
    mie_model:
        Mie model variant. Supported values are ``"Solid Sphere"`` and
        ``"Core/Shell Sphere"``.

    current_rows:
        Current table rows from a Dash DataTable.

    medium_refractive_index:
        Real part of the medium refractive index.

    particle_refractive_index:
        Real part of the particle refractive index for the solid sphere model.

    core_refractive_index:
        Real part of the core refractive index for the core shell sphere model.

    shell_refractive_index:
        Real part of the shell refractive index for the core shell sphere model.

    wavelength_nm:
        Laser wavelength in nanometers.

    detector_numerical_aperture:
        Numerical aperture of the main detector.

    detector_cache_numerical_aperture:
        Numerical aperture used by the detector cache.

    blocker_bar_numerical_aperture:
        Numerical aperture of the blocker bar. This parameter is validated here
        because it belongs to the optical parameter set, but the current
        PyMieSim photodiode coupling call does not consume it directly.

    detector_sampling:
        Number of angular sampling points for the detector integration.

    detector_phi_angle_degree:
        Detector phi offset angle in degrees.

    detector_gamma_angle_degree:
        Detector gamma offset angle in degrees.

    logger:
        Logger instance for debug and exception messages.

    Returns
    -------
    list[dict[str, str]]
        Updated rows with the ``expected_coupling`` column populated when the
        row geometry is valid and the PyMieSim computation succeeds.
    """
    resolved_rows = [dict(row) for row in (current_rows or [])]

    if not resolved_rows:
        return []

    resolved_mie_model = _normalize_mie_model(mie_model)

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
        resolved_blocker_bar_numerical_aperture = as_required_float(
            blocker_bar_numerical_aperture,
            "blocker_bar_numerical_aperture",
        )
        resolved_detector_sampling = as_required_int(
            detector_sampling,
            "detector_sampling",
        )
        resolved_detector_phi_angle_degree = as_required_float(
            detector_phi_angle_degree,
            "detector_phi_angle_degree",
        )
        resolved_detector_gamma_angle_degree = as_required_float(
            detector_gamma_angle_degree,
            "detector_gamma_angle_degree",
        )
    except Exception:
        logger.exception(
            "compute_model_for_rows aborted because optical parameters are invalid."
        )
        return table.normalize_table_rows(
            mie_model=resolved_mie_model,
            current_rows=resolved_rows,
        )

    logger.debug(
        "compute_model_for_rows resolved optical parameters "
        "mie_model=%r medium_refractive_index=%r wavelength_nm=%r "
        "detector_numerical_aperture=%r detector_cache_numerical_aperture=%r "
        "blocker_bar_numerical_aperture=%r detector_sampling=%r "
        "detector_phi_angle_degree=%r detector_gamma_angle_degree=%r",
        resolved_mie_model,
        resolved_medium_refractive_index,
        resolved_wavelength_nm,
        resolved_detector_numerical_aperture,
        resolved_detector_cache_numerical_aperture,
        resolved_blocker_bar_numerical_aperture,
        resolved_detector_sampling,
        resolved_detector_phi_angle_degree,
        resolved_detector_gamma_angle_degree,
    )

    if resolved_mie_model == CORE_SHELL_SPHERE_MODEL_NAME:
        return _compute_core_shell_model_for_rows(
            current_rows=resolved_rows,
            mie_model=resolved_mie_model,
            medium_refractive_index=resolved_medium_refractive_index,
            core_refractive_index=core_refractive_index,
            shell_refractive_index=shell_refractive_index,
            wavelength_nm=resolved_wavelength_nm,
            detector_numerical_aperture=resolved_detector_numerical_aperture,
            detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
            detector_sampling=resolved_detector_sampling,
            detector_phi_angle_degree=resolved_detector_phi_angle_degree,
            detector_gamma_angle_degree=resolved_detector_gamma_angle_degree,
            logger=logger,
        )

    return _compute_solid_sphere_model_for_rows(
        current_rows=resolved_rows,
        mie_model=resolved_mie_model,
        medium_refractive_index=resolved_medium_refractive_index,
        particle_refractive_index=particle_refractive_index,
        wavelength_nm=resolved_wavelength_nm,
        detector_numerical_aperture=resolved_detector_numerical_aperture,
        detector_cache_numerical_aperture=resolved_detector_cache_numerical_aperture,
        detector_sampling=resolved_detector_sampling,
        detector_phi_angle_degree=resolved_detector_phi_angle_degree,
        detector_gamma_angle_degree=resolved_detector_gamma_angle_degree,
        logger=logger,
    )


def _compute_core_shell_model_for_rows(
    *,
    current_rows: list[dict[str, Any]],
    mie_model: str,
    medium_refractive_index: float,
    core_refractive_index: Any,
    shell_refractive_index: Any,
    wavelength_nm: float,
    detector_numerical_aperture: float,
    detector_cache_numerical_aperture: float,
    detector_sampling: int,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    logger: logging.Logger,
) -> list[dict[str, str]]:
    """
    Compute expected coupling values for the core shell sphere Mie model.

    Each valid row must provide:

    - ``core_diameter_nm``
    - ``shell_thickness_nm``

    The physical model is evaluated with ``CoreShellSet`` in the scattering
    backend. The ``outer_diameter_nm`` column is kept synchronized by
    ``table.normalize_table_rows`` and is used only as a derived display value.

    Parameters
    ----------
    current_rows:
        Table rows containing core shell geometry values.

    mie_model:
        Mie model label passed through to ``table.normalize_table_rows``.

    medium_refractive_index:
        Real part of the medium refractive index.

    core_refractive_index:
        Real part of the core refractive index.

    shell_refractive_index:
        Real part of the shell refractive index.

    wavelength_nm:
        Laser wavelength in nanometers.

    detector_numerical_aperture:
        Numerical aperture of the main detector.

    detector_cache_numerical_aperture:
        Numerical aperture used by the detector cache.

    detector_sampling:
        Angular sampling resolution.

    detector_phi_angle_degree:
        Detector phi offset angle in degrees.

    detector_gamma_angle_degree:
        Detector gamma offset angle in degrees.

    logger:
        Logger instance for debug and exception messages.

    Returns
    -------
    list[dict[str, str]]
        Updated rows with ``expected_coupling`` populated for valid entries.
    """
    logger.debug("compute_model_for_rows running in Core/Shell Sphere mode.")

    try:
        resolved_core_refractive_index = as_required_float(
            core_refractive_index,
            "core_refractive_index",
        )
        resolved_shell_refractive_index = as_required_float(
            shell_refractive_index,
            "shell_refractive_index",
        )
    except Exception:
        logger.exception(
            "compute_model_for_rows aborted because core shell refractive indices are invalid."
        )
        return table.normalize_table_rows(
            mie_model=mie_model,
            current_rows=current_rows,
        )

    valid_row_indices: list[int] = []
    core_diameters_nm: list[float] = []
    shell_thicknesses_nm: list[float] = []

    updated_rows = table.normalize_table_rows(
        mie_model=mie_model,
        current_rows=current_rows,
    )

    for row_index, row in enumerate(updated_rows):
        core_diameter_nm = as_optional_float(row.get("core_diameter_nm"))
        shell_thickness_nm = as_optional_float(row.get("shell_thickness_nm"))

        if core_diameter_nm is None or core_diameter_nm <= 0.0:
            updated_rows[row_index]["expected_coupling"] = ""
            continue

        if shell_thickness_nm is None or shell_thickness_nm <= 0.0:
            updated_rows[row_index]["expected_coupling"] = ""
            continue

        valid_row_indices.append(row_index)
        core_diameters_nm.append(float(core_diameter_nm))
        shell_thicknesses_nm.append(float(shell_thickness_nm))

    logger.debug(
        "compute_model_for_rows core-shell valid_row_indices=%r "
        "core_diameters_nm=%r shell_thicknesses_nm=%r",
        valid_row_indices,
        core_diameters_nm,
        shell_thicknesses_nm,
    )

    if not core_diameters_nm:
        logger.debug("compute_model_for_rows found no valid core shell rows.")
        return updated_rows

    try:
        modeled_coupling_result = BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
            core_diameters_nm=np.asarray(core_diameters_nm, dtype=float),
            shell_thicknesses_nm=np.asarray(shell_thicknesses_nm, dtype=float),
            wavelength_nm=wavelength_nm,
            source_numerical_aperture=0.1,
            optical_power_watt=1.0,
            detector_numerical_aperture=detector_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            core_refractive_index=resolved_core_refractive_index,
            shell_refractive_index=resolved_shell_refractive_index,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            detector_phi_offset_degree=detector_phi_angle_degree,
            detector_gamma_offset_degree=detector_gamma_angle_degree,
            polarization_angle_degree=0.0,
            detector_sampling=detector_sampling,
        )
    except Exception:
        logger.exception(
            "compute_model_for_rows failed during core shell coupling computation."
        )
        return updated_rows

    for row_index, expected_coupling in zip(
        valid_row_indices,
        modeled_coupling_result.expected_coupling_values,
        strict=False,
    ):
        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

    logger.debug(
        "compute_model_for_rows returning updated core shell rows=%r",
        updated_rows,
    )

    return updated_rows


def _compute_solid_sphere_model_for_rows(
    *,
    current_rows: list[dict[str, Any]],
    mie_model: str,
    medium_refractive_index: float,
    particle_refractive_index: Any,
    wavelength_nm: float,
    detector_numerical_aperture: float,
    detector_cache_numerical_aperture: float,
    detector_sampling: int,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    logger: logging.Logger,
) -> list[dict[str, str]]:
    """
    Compute expected coupling values for the solid sphere Mie model.

    Uses the particle diameter from each row and the particle refractive index
    to evaluate the scattering coupling.

    Parameters
    ----------
    current_rows:
        Table rows containing ``particle_diameter_nm`` values.

    mie_model:
        Mie model label passed through to ``table.normalize_table_rows``.

    medium_refractive_index:
        Real part of the medium refractive index.

    particle_refractive_index:
        Real part of the particle refractive index.

    wavelength_nm:
        Laser wavelength in nanometers.

    detector_numerical_aperture:
        Numerical aperture of the main detector.

    detector_cache_numerical_aperture:
        Numerical aperture used by the detector cache.

    detector_sampling:
        Angular sampling resolution.

    detector_phi_angle_degree:
        Detector phi offset angle in degrees.

    detector_gamma_angle_degree:
        Detector gamma offset angle in degrees.

    logger:
        Logger instance for debug and exception messages.

    Returns
    -------
    list[dict[str, str]]
        Updated rows with ``expected_coupling`` populated for valid entries.
    """
    logger.debug("compute_model_for_rows running in Solid Sphere mode.")

    try:
        resolved_particle_refractive_index = as_required_float(
            particle_refractive_index,
            "particle_refractive_index",
        )
    except Exception:
        logger.exception(
            "compute_model_for_rows aborted because particle refractive index is invalid."
        )
        return table.normalize_table_rows(
            mie_model=mie_model,
            current_rows=current_rows,
        )

    valid_row_indices: list[int] = []
    particle_diameters_nm: list[float] = []

    updated_rows = table.normalize_table_rows(
        mie_model=mie_model,
        current_rows=current_rows,
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
        logger.debug("compute_model_for_rows found no valid solid sphere rows.")
        return updated_rows

    try:
        modeled_coupling_result = BackEnd.compute_modeled_coupling_from_diameters(
            particle_diameters_nm=np.asarray(particle_diameters_nm, dtype=float),
            wavelength_nm=wavelength_nm,
            source_numerical_aperture=0.1,
            optical_power_watt=1.0,
            detector_numerical_aperture=detector_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            particle_refractive_index=resolved_particle_refractive_index,
            detector_cache_numerical_aperture=detector_cache_numerical_aperture,
            detector_phi_offset_degree=detector_phi_angle_degree,
            detector_gamma_offset_degree=detector_gamma_angle_degree,
            polarization_angle_degree=0.0,
            detector_sampling=detector_sampling,
        )
    except Exception:
        logger.exception(
            "compute_model_for_rows failed during solid sphere coupling computation."
        )
        return updated_rows

    for row_index, expected_coupling in zip(
        valid_row_indices,
        modeled_coupling_result.expected_coupling_values,
        strict=False,
    ):
        updated_rows[row_index]["expected_coupling"] = f"{float(expected_coupling):.6g}"

    logger.debug(
        "compute_model_for_rows returning updated solid sphere rows=%r",
        updated_rows,
    )

    return updated_rows


def _normalize_mie_model(mie_model: str) -> str:
    """
    Normalize supported scattering model names.
    """
    if mie_model is None:
        return SOLID_SPHERE_MODEL_NAME

    normalized_mie_model = str(mie_model).strip().lower()

    if normalized_mie_model in {"solid sphere", "sphere", "solid_sphere"}:
        return SOLID_SPHERE_MODEL_NAME

    if normalized_mie_model in {
        "core/shell sphere",
        "core-shell sphere",
        "core shell sphere",
        "coreshell sphere",
        "core_shell_sphere",
    }:
        return CORE_SHELL_SPHERE_MODEL_NAME

    return SOLID_SPHERE_MODEL_NAME