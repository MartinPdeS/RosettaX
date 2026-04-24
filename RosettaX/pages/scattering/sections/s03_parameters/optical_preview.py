# -*- coding: utf-8 -*-

from functools import lru_cache
from typing import Any, Optional
import logging

import numpy as np
import plotly.graph_objects as go


logger = logging.getLogger(__name__)


def build_optical_configuration_preview_figure(
    *,
    detector_numerical_aperture: Any,
    blocker_bar_numerical_aperture: Any,
    medium_refractive_index: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
    scatter_coordinates: Any = None,
    camera: Optional[dict[str, Any]] = None,
) -> go.Figure:
    """
    Build an interactive 3D optical configuration preview.

    If scatter_coordinates is None, the scatter points are taken from
    PyMieSim's Photodiode mesh:

        detector.mesh.cartesian.x.magnitude
        detector.mesh.cartesian.y.magnitude
        detector.mesh.cartesian.z.magnitude

    The PyMieSim coordinates are normalized only for display on the unit sphere.
    """
    resolved_detector_numerical_aperture = _coerce_float(
        detector_numerical_aperture,
        default=0.2,
        name="detector_numerical_aperture",
    )
    resolved_blocker_bar_numerical_aperture = _coerce_float(
        blocker_bar_numerical_aperture,
        default=0.0,
        name="blocker_bar_numerical_aperture",
    )
    resolved_medium_refractive_index = _coerce_float(
        medium_refractive_index,
        default=1.333,
        name="medium_refractive_index",
    )
    resolved_detector_phi_angle_degree = _coerce_float(
        detector_phi_angle_degree,
        default=0.0,
        name="detector_phi_angle_degree",
    )
    resolved_detector_gamma_angle_degree = _coerce_float(
        detector_gamma_angle_degree,
        default=0.0,
        name="detector_gamma_angle_degree",
    )

    logger.debug(
        "Building optical preview figure with detector_numerical_aperture=%r, "
        "blocker_bar_numerical_aperture=%r, medium_refractive_index=%r, "
        "detector_phi_angle_degree=%r, detector_gamma_angle_degree=%r, "
        "scatter_coordinates_provided=%r",
        resolved_detector_numerical_aperture,
        resolved_blocker_bar_numerical_aperture,
        resolved_medium_refractive_index,
        resolved_detector_phi_angle_degree,
        resolved_detector_gamma_angle_degree,
        scatter_coordinates is not None,
    )

    resolved_scatter_coordinates = resolve_scatter_coordinates(
        scatter_coordinates=scatter_coordinates,
        detector_numerical_aperture=resolved_detector_numerical_aperture,
        blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
        medium_refractive_index=resolved_medium_refractive_index,
        detector_phi_angle_degree=resolved_detector_phi_angle_degree,
        detector_gamma_angle_degree=resolved_detector_gamma_angle_degree,
    )

    _log_coordinate_summary(
        name="resolved_scatter_coordinates",
        coordinate_array=resolved_scatter_coordinates,
    )

    resolved_camera = resolve_locked_camera(camera=camera)

    figure = go.Figure()

    figure.add_trace(_build_unit_sphere_trace())
    figure.add_trace(_build_center_sphere_trace())
    figure.add_trace(
        _build_scatter_points_trace(
            scatter_coordinates=resolved_scatter_coordinates,
        )
    )

    for trace in _build_incident_wave_traces():
        figure.add_trace(trace)

    figure.update_layout(
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene={
            "xaxis": _build_hidden_axis(range_limit=1.35),
            "yaxis": _build_hidden_axis(range_limit=1.35),
            "zaxis": _build_hidden_axis(range_limit=1.35),
            "aspectmode": "cube",
            "dragmode": "turntable",
            "camera": resolved_camera,
        },
        uirevision="optical-configuration-preview",
    )

    logger.debug(
        "Finished optical preview figure with trace_count=%d",
        len(figure.data),
    )

    return figure


def resolve_scatter_coordinates(
    *,
    scatter_coordinates: Any,
    detector_numerical_aperture: float,
    blocker_bar_numerical_aperture: float,
    medium_refractive_index: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
) -> np.ndarray:
    """
    Resolve scatter coordinates for the optical preview.

    Explicit coordinates are accepted for tests or custom overlays. Otherwise,
    coordinates are generated from the PyMieSim Photodiode mesh.
    """
    if scatter_coordinates is None:
        logger.debug("No explicit scatter coordinates provided. Building PyMieSim detector mesh.")
        return build_detector_mesh_coordinates(
            detector_numerical_aperture=detector_numerical_aperture,
            blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
        )

    logger.debug(
        "Explicit scatter coordinates provided with type=%s",
        type(scatter_coordinates).__name__,
    )

    if isinstance(scatter_coordinates, dict):
        return resolve_scatter_coordinates_from_mapping(scatter_coordinates)

    coordinate_array = np.asarray(scatter_coordinates, dtype=float)

    logger.debug(
        "Converted explicit scatter coordinates to array with shape=%r",
        coordinate_array.shape,
    )

    if coordinate_array.ndim != 2 or coordinate_array.shape[1] != 3:
        raise ValueError(
            "scatter_coordinates must be None, a mapping with x/y/z, "
            "or an array-like object with shape (N, 3)."
        )

    finite_mask = np.all(np.isfinite(coordinate_array), axis=1)
    coordinate_array = coordinate_array[finite_mask]

    logger.debug(
        "Explicit scatter coordinates after finite filtering: count=%d",
        coordinate_array.shape[0],
    )

    normalized_coordinates = normalize_coordinate_array_to_unit_sphere(
        coordinate_array=coordinate_array,
    )

    _log_coordinate_summary(
        name="explicit_normalized_scatter_coordinates",
        coordinate_array=normalized_coordinates,
    )

    return normalized_coordinates


@lru_cache(maxsize=256)
def build_detector_mesh_coordinates(
    *,
    detector_numerical_aperture: float,
    blocker_bar_numerical_aperture: float,
    medium_refractive_index: float,
    detector_phi_angle_degree: float,
    detector_gamma_angle_degree: float,
) -> np.ndarray:
    """
    Build detector scatter coordinates from PyMieSim's Photodiode mesh.

    The raw PyMieSim coordinates are normalized to the unit sphere for display,
    because the preview uses a unit sphere as its reference geometry.
    """
    logger.debug(
        "Building detector mesh coordinates with detector_numerical_aperture=%r, "
        "blocker_bar_numerical_aperture=%r, medium_refractive_index=%r, "
        "detector_phi_angle_degree=%r, detector_gamma_angle_degree=%r",
        detector_numerical_aperture,
        blocker_bar_numerical_aperture,
        medium_refractive_index,
        detector_phi_angle_degree,
        detector_gamma_angle_degree,
    )

    coordinate_array = build_pymiesim_photodiode_mesh_coordinates(
        detector_numerical_aperture=detector_numerical_aperture,
        medium_refractive_index=medium_refractive_index,
        detector_phi_angle_degree=detector_phi_angle_degree,
        detector_gamma_angle_degree=detector_gamma_angle_degree,
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
) -> np.ndarray:
    """
    Build detector coordinates from PyMieSim's Photodiode mesh.

    Important
    ---------
    PyMieSim's detector mesh is populated after the detector is attached to a
    Setup. Constructing Photodiode alone can leave:

        detector.mesh.cartesian.x
        detector.mesh.cartesian.y
        detector.mesh.cartesian.z

    empty.

    This mirrors the working PyMieSim usage pattern:

        setup = Setup(scatterer=scatterer, source=source, detector=detector)
        detector.mesh.cartesian.x
        detector.mesh.cartesian.y
        detector.mesh.cartesian.z
    """
    logger.debug("Importing PyMieSim objects for detector mesh construction.")

    from PyMieSim.units import ureg
    from PyMieSim.single.scatterer import InfiniteCylinder
    from PyMieSim.single.source import Gaussian
    from PyMieSim.polarization import PolarizationState
    from PyMieSim.single.detector import Photodiode
    from PyMieSim.single import Setup

    logger.debug(
        "Constructing PyMieSim setup with detector_numerical_aperture=%r, "
        "block medium=%r, gamma_offset=%r degree, phi_offset=%r degree.",
        detector_numerical_aperture,
        medium_refractive_index,
        detector_gamma_angle_degree,
        detector_phi_angle_degree,
    )

    polarization_state = PolarizationState(
        angle=0.0 * ureg.degree,
    )

    source = Gaussian(
        wavelength=1550.0 * ureg.nanometer,
        polarization=polarization_state,
        optical_power=1.0 * ureg.watt,
        numerical_aperture=0.3,
    )

    scatterer = InfiniteCylinder(
        diameter=1800.0 * ureg.nanometer,
        medium=float(medium_refractive_index),
        material=1.5,
    )

    detector = Photodiode(
        numerical_aperture=float(detector_numerical_aperture),
        gamma_offset=float(detector_gamma_angle_degree) * ureg.degree,
        phi_offset=float(detector_phi_angle_degree) * ureg.degree,
        polarization_filter=0.0 * ureg.degree,
        medium=float(medium_refractive_index),
    )

    setup = Setup(
        scatterer=scatterer,
        source=source,
        detector=detector,
    )

    logger.debug(
        "Constructed PyMieSim setup=%r. Reading detector mesh coordinates.",
        setup,
    )

    x_coordinates = np.asarray(
        detector.mesh.cartesian.x.magnitude,
        dtype=float,
    ).reshape(-1)

    y_coordinates = np.asarray(
        detector.mesh.cartesian.y.magnitude,
        dtype=float,
    ).reshape(-1)

    z_coordinates = np.asarray(
        detector.mesh.cartesian.z.magnitude,
        dtype=float,
    ).reshape(-1)

    logger.debug(
        "Extracted PyMieSim setup-initialized mesh coordinate arrays with sizes "
        "x=%d, y=%d, z=%d.",
        x_coordinates.size,
        y_coordinates.size,
        z_coordinates.size,
    )

    if not (x_coordinates.size == y_coordinates.size == z_coordinates.size):
        raise ValueError(
            "PyMieSim detector mesh coordinate arrays have inconsistent sizes: "
            f"x={x_coordinates.size}, y={y_coordinates.size}, z={z_coordinates.size}."
        )

    if x_coordinates.size == 0:
        logger.warning(
            "PyMieSim detector mesh is still empty after Setup construction. "
            "Check whether Photodiode requires an explicit sampling parameter or "
            "whether Setup initialization changed."
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

    return coordinate_array


def resolve_scatter_coordinates_from_mapping(
    scatter_coordinates: dict[str, Any],
) -> np.ndarray:
    """
    Resolve scatter coordinates from a mapping containing x, y, and z arrays.
    """
    logger.debug(
        "Resolving scatter coordinates from mapping with keys=%r",
        sorted(scatter_coordinates.keys()),
    )

    missing_keys = {"x", "y", "z"}.difference(scatter_coordinates)

    if missing_keys:
        raise ValueError(
            f"scatter coordinate mapping is missing keys: {sorted(missing_keys)}"
        )

    x_coordinates = np.asarray(scatter_coordinates["x"], dtype=float).reshape(-1)
    y_coordinates = np.asarray(scatter_coordinates["y"], dtype=float).reshape(-1)
    z_coordinates = np.asarray(scatter_coordinates["z"], dtype=float).reshape(-1)

    logger.debug(
        "Mapping scatter coordinate sizes: x=%d, y=%d, z=%d",
        x_coordinates.size,
        y_coordinates.size,
        z_coordinates.size,
    )

    if not (x_coordinates.size == y_coordinates.size == z_coordinates.size):
        raise ValueError(
            "scatter coordinate mapping must contain x, y, and z arrays "
            "with the same length."
        )

    coordinate_array = np.column_stack(
        [
            x_coordinates,
            y_coordinates,
            z_coordinates,
        ]
    )

    finite_mask = np.all(np.isfinite(coordinate_array), axis=1)
    coordinate_array = coordinate_array[finite_mask]

    logger.debug(
        "Mapping scatter coordinates after finite filtering: count=%d",
        coordinate_array.shape[0],
    )

    normalized_coordinates = normalize_coordinate_array_to_unit_sphere(
        coordinate_array=coordinate_array,
    )

    _log_coordinate_summary(
        name="mapping_normalized_scatter_coordinates",
        coordinate_array=normalized_coordinates,
    )

    return normalized_coordinates


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

    normalized_coordinate_array = (
        coordinate_array[valid_mask] / norms[valid_mask, None]
    )

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
        coordinate_array[:, 1] ** 2
        + coordinate_array[:, 2] ** 2
    )

    local_numerical_aperture = float(medium_refractive_index) * radial_coordinate

    valid_mask = (
        local_numerical_aperture >= float(blocker_bar_numerical_aperture)
    )

    filtered_coordinate_array = coordinate_array[valid_mask]

    logger.debug(
        "Blocker filtering result: before=%d, after=%d, removed=%d, "
        "local_na_min=%r, local_na_max=%r",
        coordinate_array.shape[0],
        filtered_coordinate_array.shape[0],
        coordinate_array.shape[0] - filtered_coordinate_array.shape[0],
        float(np.min(local_numerical_aperture)) if local_numerical_aperture.size else None,
        float(np.max(local_numerical_aperture)) if local_numerical_aperture.size else None,
    )

    return filtered_coordinate_array


def build_default_optical_preview_camera() -> dict[str, Any]:
    """
    Build the default camera for the optical configuration preview.
    """
    camera = {
        "eye": {
            "x": 1.15,
            "y": 1.05,
            "z": 0.85,
        },
        "center": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
        },
        "up": {
            "x": 0.0,
            "y": 0.0,
            "z": 1.0,
        },
    }

    logger.debug("Using default optical preview camera=%r", camera)

    return camera


def resolve_locked_camera(
    *,
    camera: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """
    Preserve camera rotation while forcing the camera center to remain fixed.
    """
    default_camera = build_default_optical_preview_camera()

    if not isinstance(camera, dict):
        logger.debug("No valid camera provided. Using default camera.")
        return default_camera

    eye = camera.get("eye", default_camera["eye"])
    up = camera.get("up", default_camera["up"])

    resolved_camera = {
        "eye": eye if isinstance(eye, dict) else default_camera["eye"],
        "up": up if isinstance(up, dict) else default_camera["up"],
        "center": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
        },
    }

    logger.debug(
        "Resolved locked camera from input camera=%r to resolved_camera=%r",
        camera,
        resolved_camera,
    )

    return resolved_camera


def resolve_locked_camera_from_relayout_data(
    *,
    relayout_data: Any,
) -> dict[str, Any]:
    """
    Extract a Plotly camera from relayoutData and lock its center.
    """
    logger.debug("Resolving locked camera from relayout_data=%r", relayout_data)

    if not isinstance(relayout_data, dict):
        return build_default_optical_preview_camera()

    camera = relayout_data.get("scene.camera")

    if not isinstance(camera, dict):
        logger.debug("No scene.camera found in relayoutData. Using default camera.")
        return build_default_optical_preview_camera()

    return resolve_locked_camera(camera=camera)


def _build_unit_sphere_trace() -> go.Surface:
    """
    Build a transparent unit sphere centered at the origin.
    """
    x_coordinates, y_coordinates, z_coordinates = get_unit_sphere_coordinates()

    return go.Surface(
        x=x_coordinates,
        y=y_coordinates,
        z=z_coordinates,
        showscale=False,
        opacity=0.07,
        colorscale=[
            [0.0, "#9ecae1"],
            [1.0, "#9ecae1"],
        ],
        hoverinfo="skip",
    )


def _build_center_sphere_trace() -> go.Surface:
    """
    Build a small black sphere centered at the origin.
    """
    x_coordinates, y_coordinates, z_coordinates = get_center_sphere_coordinates()

    return go.Surface(
        x=x_coordinates,
        y=y_coordinates,
        z=z_coordinates,
        showscale=False,
        opacity=1.0,
        colorscale=[
            [0.0, "#111111"],
            [1.0, "#111111"],
        ],
        hoverinfo="skip",
    )


@lru_cache(maxsize=1)
def get_unit_sphere_coordinates() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return cached unit sphere surface coordinates.
    """
    logger.debug("Building cached unit sphere coordinates.")

    azimuth_values = np.linspace(0.0, 2.0 * np.pi, 48)
    polar_values = np.linspace(0.0, np.pi, 32)

    x_coordinates = np.outer(
        np.cos(azimuth_values),
        np.sin(polar_values),
    )
    y_coordinates = np.outer(
        np.sin(azimuth_values),
        np.sin(polar_values),
    )
    z_coordinates = np.outer(
        np.ones_like(azimuth_values),
        np.cos(polar_values),
    )

    return x_coordinates, y_coordinates, z_coordinates


@lru_cache(maxsize=1)
def get_center_sphere_coordinates() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return cached center sphere surface coordinates.
    """
    logger.debug("Building cached center sphere coordinates.")

    azimuth_values = np.linspace(0.0, 2.0 * np.pi, 24)
    polar_values = np.linspace(0.0, np.pi, 16)

    radius = 0.08

    x_coordinates = radius * np.outer(
        np.cos(azimuth_values),
        np.sin(polar_values),
    )
    y_coordinates = radius * np.outer(
        np.sin(azimuth_values),
        np.sin(polar_values),
    )
    z_coordinates = radius * np.outer(
        np.ones_like(azimuth_values),
        np.cos(polar_values),
    )

    return x_coordinates, y_coordinates, z_coordinates


def _build_scatter_points_trace(
    *,
    scatter_coordinates: np.ndarray,
) -> go.Scatter3d:
    """
    Build scatter points from explicit 3D coordinates.
    """
    _log_coordinate_summary(
        name="scatter_points_trace_input",
        coordinate_array=scatter_coordinates,
    )

    if scatter_coordinates.size == 0:
        logger.warning("Scatter coordinate array is empty. The preview will show no detector points.")
        x_coordinates = np.array([], dtype=float)
        y_coordinates = np.array([], dtype=float)
        z_coordinates = np.array([], dtype=float)
    else:
        x_coordinates = scatter_coordinates[:, 0]
        y_coordinates = scatter_coordinates[:, 1]
        z_coordinates = scatter_coordinates[:, 2]

    return go.Scatter3d(
        x=x_coordinates,
        y=y_coordinates,
        z=z_coordinates,
        mode="markers",
        marker={
            "size": 5.0,
            "color": "#0057ff",
            "opacity": 1.0,
            "line": {
                "width": 0.0,
            },
        },
        hoverinfo="skip",
    )


def _build_incident_wave_traces() -> list[Any]:
    """
    Build incident wave annotation traces.

    k:
        Red propagation vector coming from the bottom toward the origin.

    E:
        Blue electric field vector, perpendicular to k.
        Since k is along +z here, E is drawn along +x.
    """
    k_shaft_trace = go.Scatter3d(
        x=[0.0, 0.0],
        y=[0.0, 0.0],
        z=[-1.20, -0.18],
        mode="lines",
        line={
            "width": 8,
            "color": "#d62728",
        },
        hoverinfo="skip",
    )

    k_arrow_trace = go.Cone(
        x=[0.0],
        y=[0.0],
        z=[-0.10],
        u=[0.0],
        v=[0.0],
        w=[0.22],
        sizemode="absolute",
        sizeref=0.18,
        anchor="tip",
        showscale=False,
        colorscale=[
            [0.0, "#d62728"],
            [1.0, "#d62728"],
        ],
        hoverinfo="skip",
    )

    electric_field_shaft_trace = go.Scatter3d(
        x=[-0.34, 0.24],
        y=[0.0, 0.0],
        z=[-0.72, -0.72],
        mode="lines",
        line={
            "width": 8,
            "color": "#1f77b4",
        },
        hoverinfo="skip",
    )

    electric_field_arrow_trace = go.Cone(
        x=[0.32],
        y=[0.0],
        z=[-0.72],
        u=[0.18],
        v=[0.0],
        w=[0.0],
        sizemode="absolute",
        sizeref=0.16,
        anchor="tip",
        showscale=False,
        colorscale=[
            [0.0, "#1f77b4"],
            [1.0, "#1f77b4"],
        ],
        hoverinfo="skip",
    )

    electric_field_label_trace = go.Scatter3d(
        x=[0.42],
        y=[0.0],
        z=[-0.72],
        mode="text",
        text=["E"],
        textfont={
            "size": 16,
            "color": "#1f77b4",
        },
        hoverinfo="skip",
    )

    return [
        k_shaft_trace,
        k_arrow_trace,
        electric_field_shaft_trace,
        electric_field_arrow_trace,
        electric_field_label_trace,
    ]


def _build_hidden_axis(
    *,
    range_limit: float,
) -> dict[str, Any]:
    """
    Build a hidden Plotly 3D axis with a fixed symmetric range.
    """
    return {
        "visible": False,
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "title": "",
        "range": [-range_limit, range_limit],
    }


def _coerce_float(
    value: Any,
    default: float,
    name: str,
) -> float:
    """
    Convert a value to float, falling back to a default when conversion fails.
    """
    try:
        resolved_value = float(value)
        logger.debug("Coerced %s=%r to float=%r", name, value, resolved_value)
        return resolved_value
    except (TypeError, ValueError):
        logger.warning(
            "Could not coerce %s=%r to float. Using default=%r",
            name,
            value,
            default,
        )
        return default


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
        logger.debug("%s summary: empty array with shape=%r", name, coordinate_array.shape)
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