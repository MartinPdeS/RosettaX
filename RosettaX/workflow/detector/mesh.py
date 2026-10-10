"""Detector mesh construction, orientation, and geometric filtering."""

import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def build_detector_mesh_coordinates(
    *,
    detector_numerical_aperture: float,
    blocker_bar_numerical_aperture: float,
    medium_refractive_index: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    detector_sampling: int = 200,
    detector_visible_mask: tuple[bool, ...] | None = None,
) -> np.ndarray:
    """
    Build detector scatter coordinates from PyMieSim's Photodiode mesh.

    The raw PyMieSim coordinates are normalized to the unit sphere for display,
    because the preview uses a unit sphere as its reference geometry.
    """
    logger.debug(
        "Building detector mesh coordinates with detector_numerical_aperture=%r, "
        "blocker_bar_numerical_aperture=%r, medium_refractive_index=%r, "
        "detector_phi_angle_degree=%r, detector_gamma_angle_degree=%r, "
        "detector_sampling=%r",
        detector_numerical_aperture,
        blocker_bar_numerical_aperture,
        medium_refractive_index,
        detector_phi_angle_degree,
        detector_gamma_angle_degree,
        detector_sampling,
    )

    coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=medium_refractive_index,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
        detector_sampling=detector_sampling,
    )

    if detector_visible_mask is not None:
        visible_mask = np.asarray(detector_visible_mask, dtype=bool).reshape(-1)

        if visible_mask.size != coordinate_array.shape[0]:
            raise ValueError(
                "detector_visible_mask size must match detector mesh coordinate count. "
                f"Got {visible_mask.size} flags for {coordinate_array.shape[0]} coordinates."
            )

        coordinate_array = coordinate_array[visible_mask]

        _log_coordinate_summary(
            name="weight_filtered_pymiesim_mesh_coordinates",
            coordinate_array=coordinate_array,
        )

    _log_coordinate_summary(
        name="raw_pymiesim_mesh_coordinates",
        coordinate_array=coordinate_array,
    )

    coordinate_array = normalize_coordinate_array_to_unit_sphere(
        coordinate_array=coordinate_array,
    )

    _log_coordinate_summary(
        name="normalized_pymiesim_mesh_coordinates",
        coordinate_array=coordinate_array,
    )

    coordinate_array = filter_coordinates_with_blocker_bar(
        coordinate_array=coordinate_array,
        blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
        medium_refractive_index=medium_refractive_index,
    )

    _log_coordinate_summary(
        name="blocker_filtered_mesh_coordinates",
        coordinate_array=coordinate_array,
    )

    finite_mask = np.all(np.isfinite(coordinate_array), axis=1)
    finite_coordinate_array = coordinate_array[finite_mask]

    logger.debug(
        "Final detector mesh coordinate count after finite filtering: before=%d, after=%d",
        coordinate_array.shape[0],
        finite_coordinate_array.shape[0],
    )

    return finite_coordinate_array


def build_pymiesim_photodiode_mesh_coordinates(
    *,
    detector_numerical_aperture: float,
    medium_refractive_index: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    detector_sampling: int = 200,
) -> np.ndarray:
    """Return owned mesh coordinates, reusing bounded geometry calculations."""
    sampling = int(detector_sampling)
    builder = (
        _build_cached_photodiode_mesh_coordinates
        if sampling <= 20_000
        else _build_cached_photodiode_mesh_coordinates.__wrapped__
    )
    return builder(
        detector_numerical_aperture=float(detector_numerical_aperture),
        medium_refractive_index=float(medium_refractive_index),
        detector_phi_angle_degree=float(detector_phi_angle_degree),
        detector_gamma_angle_degree=float(detector_gamma_angle_degree),
        detector_sampling=sampling,
    ).copy()


@lru_cache(maxsize=32)
def _build_cached_photodiode_mesh_coordinates(
    *,
    detector_numerical_aperture: float,
    medium_refractive_index: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
    detector_sampling: int = 200,
) -> np.ndarray:
    """
    Build detector coordinates from a PyMieSim-equivalent Fibonacci mesh.

    The native PyMieSim detector mesh path currently segfaults on the
    Python 3.13 macOS build used by this application when detector mesh
    coordinate arrays are accessed. RosettaX only needs the mesh geometry for
    preview rendering and detector angular masks, so this helper mirrors the
    PyMieSim Fibonacci-cap construction in pure NumPy.
    """
    logger.debug(
        "Building detector Fibonacci mesh with detector_numerical_aperture=%r, "
        "medium=%r, gamma_offset=%r degree, phi_offset=%r degree.",
        detector_numerical_aperture,
        medium_refractive_index,
        detector_gamma_angle_degree,
        detector_phi_angle_degree,
    )

    max_angle = _build_detector_collection_max_angle(
        detector_numerical_aperture=float(detector_numerical_aperture),
        medium_refractive_index=float(medium_refractive_index),
    )

    coordinate_array = _build_fibonacci_cap_coordinate_array(
        sampling=int(detector_sampling),
        max_angle=max_angle,
        min_angle=0.0,
    )
    coordinate_array = _rotate_coordinate_array_about_x(
        coordinate_array,
        np.deg2rad(float(detector_gamma_angle_degree)),
    )
    coordinate_array = _rotate_coordinate_array_about_y(
        coordinate_array,
        np.deg2rad(float(detector_phi_angle_degree)),
    )
    coordinate_array = _map_detector_frame_to_rosettax_frame(
        coordinate_array,
    )

    x_coordinates = coordinate_array[:, 0]
    y_coordinates = coordinate_array[:, 1]
    z_coordinates = coordinate_array[:, 2]

    logger.debug(
        "Built local detector mesh coordinate arrays with sizes x=%d, y=%d, z=%d.",
        x_coordinates.size,
        y_coordinates.size,
        z_coordinates.size,
    )

    if not (x_coordinates.size == y_coordinates.size == z_coordinates.size):
        raise ValueError(
            "Detector mesh coordinate arrays have inconsistent sizes: "
            f"x={x_coordinates.size}, y={y_coordinates.size}, z={z_coordinates.size}."
        )

    if x_coordinates.size == 0:
        logger.warning(
            "Detector Fibonacci mesh is empty after local construction. "
            "Check the sampling size and collection-angle bounds."
        )

    coordinate_array = np.column_stack(
        [
            x_coordinates,
            y_coordinates,
            z_coordinates,
        ]
    )

    _log_coordinate_summary(
        name="pymiesim_setup_initialized_photodiode_mesh_coordinates",
        coordinate_array=coordinate_array,
    )

    coordinate_array.setflags(write=False)
    return coordinate_array


def _build_detector_collection_max_angle(
    *,
    detector_numerical_aperture: float,
    medium_refractive_index: float,
) -> float:
    detector_medium_refractive_index = float(medium_refractive_index)

    if detector_medium_refractive_index <= 0.0:
        raise ValueError("medium_refractive_index must be positive.")

    normalized_numerical_aperture = np.clip(
        float(detector_numerical_aperture) / detector_medium_refractive_index,
        -1.0,
        1.0,
    )
    return float(np.arcsin(normalized_numerical_aperture))


def _build_fibonacci_cap_coordinate_array(
    *,
    sampling: int,
    max_angle: float,
    min_angle: float,
) -> np.ndarray:
    if sampling <= 0:
        raise ValueError("detector_sampling must be a positive integer.")

    if sampling == 1:
        return np.asarray([[0.0, 0.0, 1.0]], dtype=float)

    solid_angle = 2.0 * np.pi * abs(np.cos(min_angle) - np.cos(max_angle))

    if solid_angle <= 0.0:
        raise ValueError("Detector collection solid angle must be positive.")

    sampling_ratio = (4.0 * np.pi) / solid_angle
    true_number_of_sample = max(int(sampling * sampling_ratio), sampling)
    golden_angle = np.pi * (3.0 - np.sqrt(5.0))

    coordinate_rows: list[list[float]] = []

    for index in range(true_number_of_sample):
        denominator = max(true_number_of_sample - 1, 1)
        z_coordinate = 1.0 - (2.0 * index) / denominator
        azimuthal_angle = golden_angle * index
        radial_distance = np.sqrt(max(0.0, 1.0 - z_coordinate * z_coordinate))
        polar_angle = (np.pi / 2.0) - np.arcsin(np.clip(z_coordinate, -1.0, 1.0))

        if polar_angle < min_angle:
            continue

        coordinate_rows.append(
            [
                float(np.cos(azimuthal_angle) * radial_distance),
                float(np.sin(azimuthal_angle) * radial_distance),
                float(z_coordinate),
            ]
        )

        if len(coordinate_rows) >= sampling:
            break

    if len(coordinate_rows) != sampling:
        raise ValueError(
            "Could not construct the requested number of detector mesh coordinates. "
            f"Expected {sampling}, built {len(coordinate_rows)}."
        )

    return np.asarray(coordinate_rows, dtype=float)


def _rotate_coordinate_array_about_x(
    coordinate_array: np.ndarray,
    angle_radian: float,
) -> np.ndarray:
    if angle_radian == 0.0:
        return np.asarray(coordinate_array, dtype=float)

    cosine = float(np.cos(angle_radian))
    sine = float(np.sin(angle_radian))
    rotation_matrix = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, cosine, -sine],
            [0.0, sine, cosine],
        ],
        dtype=float,
    )
    return np.asarray(coordinate_array, dtype=float) @ rotation_matrix.T


def _rotate_coordinate_array_about_y(
    coordinate_array: np.ndarray,
    angle_radian: float,
) -> np.ndarray:
    if angle_radian == 0.0:
        return np.asarray(coordinate_array, dtype=float)

    cosine = float(np.cos(angle_radian))
    sine = float(np.sin(angle_radian))
    rotation_matrix = np.asarray(
        [
            [cosine, 0.0, sine],
            [0.0, 1.0, 0.0],
            [-sine, 0.0, cosine],
        ],
        dtype=float,
    )
    return np.asarray(coordinate_array, dtype=float) @ rotation_matrix.T


def _map_detector_frame_to_rosettax_frame(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    coordinate_array = np.asarray(coordinate_array, dtype=float)

    return np.column_stack(
        [
            coordinate_array[:, 2],
            coordinate_array[:, 1],
            coordinate_array[:, 0],
        ]
    )


def normalize_coordinate_array_to_unit_sphere(
    *,
    coordinate_array: np.ndarray,
) -> np.ndarray:
    """
    Normalize coordinates row wise so all points lie on the unit sphere.
    """
    coordinate_array = np.asarray(coordinate_array, dtype=float)

    logger.debug(
        "Normalizing coordinate array to unit sphere with shape=%r",
        coordinate_array.shape,
    )

    if coordinate_array.size == 0:
        logger.debug("Coordinate array is empty. Returning empty (0, 3) array.")
        return np.empty((0, 3), dtype=float)

    if coordinate_array.ndim != 2 or coordinate_array.shape[1] != 3:
        raise ValueError("coordinate_array must have shape (N, 3).")

    norms = np.linalg.norm(coordinate_array, axis=1)
    valid_mask = norms > 0.0

    valid_count = int(np.count_nonzero(valid_mask))

    logger.debug(
        "Coordinate normalization norms summary: total=%d, valid=%d, "
        "min_norm=%r, max_norm=%r",
        norms.size,
        valid_count,
        float(np.min(norms)) if norms.size else None,
        float(np.max(norms)) if norms.size else None,
    )

    normalized_coordinate_array = coordinate_array[valid_mask] / norms[valid_mask, None]

    return normalized_coordinate_array


def filter_coordinates_with_blocker_bar(
    *,
    coordinate_array: np.ndarray,
    blocker_bar_numerical_aperture: float,
    medium_refractive_index: float,
) -> np.ndarray:
    """
    Remove points inside the blocker bar NA.

    Assumes coordinate_array already lies on the unit sphere.
    """
    if blocker_bar_numerical_aperture <= 0.0:
        logger.debug(
            "Blocker bar NA is <= 0. No blocker filtering applied. "
            "blocker_bar_numerical_aperture=%r",
            blocker_bar_numerical_aperture,
        )
        return coordinate_array

    coordinate_array = np.asarray(coordinate_array, dtype=float)

    logger.debug(
        "Filtering coordinates with blocker bar: coordinate_count=%d, "
        "blocker_bar_numerical_aperture=%r, medium_refractive_index=%r",
        coordinate_array.shape[0],
        blocker_bar_numerical_aperture,
        medium_refractive_index,
    )

    if coordinate_array.size == 0:
        logger.debug("Coordinate array is empty before blocker filtering.")
        return np.empty((0, 3), dtype=float)

    radial_coordinate = np.sqrt(
        coordinate_array[:, 1] ** 2 + coordinate_array[:, 2] ** 2
    )

    local_numerical_aperture = float(medium_refractive_index) * radial_coordinate

    valid_mask = local_numerical_aperture >= float(blocker_bar_numerical_aperture)

    filtered_coordinate_array = coordinate_array[valid_mask]

    logger.debug(
        "Blocker filtering result: before=%d, after=%d, removed=%d, "
        "local_na_min=%r, local_na_max=%r",
        coordinate_array.shape[0],
        filtered_coordinate_array.shape[0],
        coordinate_array.shape[0] - filtered_coordinate_array.shape[0],
        float(np.min(local_numerical_aperture))
        if local_numerical_aperture.size
        else None,
        float(np.max(local_numerical_aperture))
        if local_numerical_aperture.size
        else None,
    )

    return filtered_coordinate_array


def _log_coordinate_summary(
    *,
    name: str,
    coordinate_array: np.ndarray,
) -> None:
    """
    Log useful coordinate diagnostics without dumping full arrays.
    """
    coordinate_array = np.asarray(coordinate_array)

    if coordinate_array.size == 0:
        logger.debug(
            "%s summary: empty array with shape=%r", name, coordinate_array.shape
        )
        return

    if coordinate_array.ndim != 2 or coordinate_array.shape[1] != 3:
        logger.debug(
            "%s summary: non-coordinate array with shape=%r",
            name,
            coordinate_array.shape,
        )
        return

    finite_mask = np.all(np.isfinite(coordinate_array), axis=1)
    finite_coordinates = coordinate_array[finite_mask]

    if finite_coordinates.size == 0:
        logger.debug(
            "%s summary: shape=%r, finite_count=0",
            name,
            coordinate_array.shape,
        )
        return

    norms = np.linalg.norm(finite_coordinates, axis=1)

    logger.debug(
        "%s summary: shape=%r, finite_count=%d, "
        "x_range=(%.6g, %.6g), y_range=(%.6g, %.6g), z_range=(%.6g, %.6g), "
        "norm_range=(%.6g, %.6g)",
        name,
        coordinate_array.shape,
        finite_coordinates.shape[0],
        float(np.min(finite_coordinates[:, 0])),
        float(np.max(finite_coordinates[:, 0])),
        float(np.min(finite_coordinates[:, 1])),
        float(np.max(finite_coordinates[:, 1])),
        float(np.min(finite_coordinates[:, 2])),
        float(np.max(finite_coordinates[:, 2])),
        float(np.min(norms)),
        float(np.max(norms)),
    )
