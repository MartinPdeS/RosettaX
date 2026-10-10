"""Optical preview figures and the geometry signatures used to update them."""

import hashlib
import json
import logging
from functools import lru_cache
from typing import Any

import numpy as np
import plotly.graph_objects as go

from RosettaX.workflow.constants import (
    DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
)
from RosettaX.workflow.detector.mesh import (
    _log_coordinate_summary,
    _rotate_coordinate_array_about_y,
    build_detector_mesh_coordinates,
    normalize_coordinate_array_to_unit_sphere,
)

logger = logging.getLogger(__name__)
OPTICAL_PREVIEW_UIREVISION = "optical-configuration-preview-v2"


def resolve_optical_preview_numeric_values(values: dict[str, Any]) -> dict[str, Any]:
    """Normalize numeric controls consistently for rendering and comparison."""
    defaults = {
        "detector_numerical_aperture": 0.2,
        "blocker_bar_numerical_aperture": 0.0,
        "medium_refractive_index": 1.333,
        "detector_phi_angle_degree": 0.0,
        "detector_gamma_angle_degree": 0.0,
        "polarization_angle_degree": DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
    }
    resolved_values = {
        name: _coerce_float(values.get(name), default=default, name=name)
        for name, default in defaults.items()
    }
    resolved_values["detector_sampling"] = _coerce_int(
        values.get("detector_sampling"),
        default=200,
        name="detector_sampling",
    )
    return resolved_values


def build_optical_configuration_preview_signature(
    preview_parameters: dict[str, Any],
) -> str:
    """Identify rendered geometry, excluding camera state and unused controls."""
    include_geometry = preview_parameters["include_geometry"]
    if include_geometry:
        signature_values = resolve_optical_preview_numeric_values(preview_parameters)
        angular_weights = preview_parameters.get("detector_angular_weights")
        signature_values["detector_visible_mask"] = (
            None
            if angular_weights is None
            else (
                np.asarray(angular_weights, dtype=np.complex128).reshape(-1) != 0.0
            ).tolist()
        )
    else:
        signature_values = {
            "polarization_angle_degree": _coerce_float(
                preview_parameters.get("polarization_angle_degree"),
                default=DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
                name="polarization_angle_degree",
            ),
        }
    signature_values["include_geometry"] = include_geometry
    return hashlib.sha256(
        json.dumps(signature_values, sort_keys=True).encode("utf-8")
    ).hexdigest()


def build_optical_configuration_preview_figure(
    *,
    detector_numerical_aperture: Any,
    blocker_bar_numerical_aperture: Any,
    medium_refractive_index: Any,
    detector_phi_angle_degree: Any,
    detector_gamma_angle_degree: Any,
    polarization_angle_degree: Any = DEFAULT_SOURCE_POLARIZATION_ANGLE_DEGREE,
    scatter_coordinates: Any = None,
    camera: dict[str, Any] | None = None,
    detector_sampling: Any = 200,
    detector_angular_weights: np.ndarray | None = None,
    include_geometry: bool = True,
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
    numeric_values = resolve_optical_preview_numeric_values(
        {
            "detector_numerical_aperture": detector_numerical_aperture,
            "blocker_bar_numerical_aperture": blocker_bar_numerical_aperture,
            "medium_refractive_index": medium_refractive_index,
            "detector_phi_angle_degree": detector_phi_angle_degree,
            "detector_gamma_angle_degree": detector_gamma_angle_degree,
            "polarization_angle_degree": polarization_angle_degree,
            "detector_sampling": detector_sampling,
        }
    )
    resolved_detector_numerical_aperture = numeric_values["detector_numerical_aperture"]
    resolved_blocker_bar_numerical_aperture = numeric_values[
        "blocker_bar_numerical_aperture"
    ]
    resolved_medium_refractive_index = numeric_values["medium_refractive_index"]
    resolved_detector_phi_angle_degree = numeric_values["detector_phi_angle_degree"]
    resolved_detector_gamma_angle_degree = numeric_values["detector_gamma_angle_degree"]
    resolved_polarization_angle_degree = numeric_values["polarization_angle_degree"]
    resolved_detector_sampling = numeric_values["detector_sampling"]

    logger.debug(
        "Building optical preview figure with detector_numerical_aperture=%r, "
        "blocker_bar_numerical_aperture=%r, medium_refractive_index=%r, "
        "detector_phi_angle_degree=%r, detector_gamma_angle_degree=%r, "
        "polarization_angle_degree=%r, detector_sampling=%r, detector_angular_weights_provided=%r, "
        "scatter_coordinates_provided=%r, include_geometry=%r",
        resolved_detector_numerical_aperture,
        resolved_blocker_bar_numerical_aperture,
        resolved_medium_refractive_index,
        resolved_detector_phi_angle_degree,
        resolved_detector_gamma_angle_degree,
        resolved_polarization_angle_degree,
        resolved_detector_sampling,
        detector_angular_weights is not None,
        scatter_coordinates is not None,
        include_geometry,
    )

    resolved_camera = resolve_locked_camera(camera=camera)

    figure = go.Figure()

    figure.add_trace(_build_unit_sphere_trace())
    figure.add_trace(_build_center_sphere_trace())

    if include_geometry:
        detector_visible_mask: tuple[bool, ...] | None = None

        if detector_angular_weights is not None:
            detector_visible_mask = tuple(
                bool(value != 0.0)
                for value in np.asarray(
                    detector_angular_weights,
                    dtype=np.complex128,
                ).reshape(-1)
            )

        resolved_scatter_coordinates = resolve_scatter_coordinates(
            scatter_coordinates=scatter_coordinates,
            detector_numerical_aperture=resolved_detector_numerical_aperture,
            blocker_bar_numerical_aperture=resolved_blocker_bar_numerical_aperture,
            medium_refractive_index=resolved_medium_refractive_index,
            detector_phi_angle_degree=resolved_detector_phi_angle_degree,
            detector_gamma_angle_degree=resolved_detector_gamma_angle_degree,
            detector_sampling=resolved_detector_sampling,
            detector_visible_mask=detector_visible_mask,
        )

        _log_coordinate_summary(
            name="resolved_scatter_coordinates",
            coordinate_array=resolved_scatter_coordinates,
        )

        figure.add_trace(
            _build_scatter_points_trace(
                scatter_coordinates=resolved_scatter_coordinates,
            )
        )

    for trace in _build_incident_wave_traces(
        polarization_angle_degree=resolved_polarization_angle_degree,
    ):
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
        uirevision=OPTICAL_PREVIEW_UIREVISION,
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
    detector_sampling: int,
    detector_visible_mask: tuple[bool, ...] | None,
) -> np.ndarray:
    """
    Resolve scatter coordinates for the optical preview.

    Explicit coordinates are accepted for tests or custom overlays. Otherwise,
    coordinates are generated from the PyMieSim Photodiode mesh.
    """
    if scatter_coordinates is None:
        logger.debug(
            "No explicit scatter coordinates provided. Building PyMieSim detector mesh."
        )
        return build_detector_mesh_coordinates(
            detector_numerical_aperture=detector_numerical_aperture,
            blocker_bar_numerical_aperture=blocker_bar_numerical_aperture,
            medium_refractive_index=medium_refractive_index,
            detector_phi_angle_degree=detector_phi_angle_degree,
            detector_gamma_angle_degree=detector_gamma_angle_degree,
            detector_sampling=detector_sampling,
            detector_visible_mask=detector_visible_mask,
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


def _rotate_preview_display_coordinate_array(
    coordinate_array: np.ndarray,
) -> np.ndarray:
    """
    Rotate display coordinates so model +x renders as display +z.
    """
    return _rotate_coordinate_array_about_y(
        np.asarray(coordinate_array, dtype=float),
        -np.pi / 2.0,
    )


def _rotate_preview_display_surface_coordinates(
    x_coordinates: np.ndarray,
    y_coordinates: np.ndarray,
    z_coordinates: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Rotate one surface grid into the preview display orientation.
    """
    stacked_coordinates = np.stack(
        [
            np.asarray(x_coordinates, dtype=float),
            np.asarray(y_coordinates, dtype=float),
            np.asarray(z_coordinates, dtype=float),
        ],
        axis=-1,
    )
    rotated_coordinates = _rotate_preview_display_coordinate_array(
        stacked_coordinates.reshape(-1, 3),
    ).reshape(stacked_coordinates.shape)

    return (
        rotated_coordinates[..., 0],
        rotated_coordinates[..., 1],
        rotated_coordinates[..., 2],
    )


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


def build_default_optical_preview_camera() -> dict[str, Any]:
    """
    Build the default camera for the optical configuration preview.

    The preview display coordinates are already rotated so the incident
    propagation vector k appears along +z on screen.
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
    camera: dict[str, Any] | None,
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
    x_coordinates, y_coordinates, z_coordinates = (
        _rotate_preview_display_surface_coordinates(
            x_coordinates,
            y_coordinates,
            z_coordinates,
        )
    )

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
    x_coordinates, y_coordinates, z_coordinates = (
        _rotate_preview_display_surface_coordinates(
            x_coordinates,
            y_coordinates,
            z_coordinates,
        )
    )

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

    scatter_coordinates = _rotate_preview_display_coordinate_array(
        np.asarray(scatter_coordinates, dtype=float).reshape(-1, 3)
        if np.asarray(scatter_coordinates).size
        else np.empty((0, 3), dtype=float)
    )

    if scatter_coordinates.size == 0:
        logger.warning(
            "Scatter coordinate array is empty. The preview will show no detector points."
        )
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
            "color": "black",
            "opacity": 1.0,
            "line": {
                "width": 0.0,
            },
        },
        hoverinfo="skip",
    )


def _build_incident_wave_traces(
    *,
    polarization_angle_degree: float,
) -> list[Any]:
    """
    Build incident wave annotation traces.

    k:
        Red propagation vector coming from negative x toward the origin.

    E:
        Blue electric field vector, perpendicular to k.
        Since k is along +x here, E is rotated in the y-z plane according to
        the source polarization angle in degrees.
    """
    shared_origin = np.asarray(
        [-0.78, 0.0, 0.0],
        dtype=float,
    )
    polarization_radians = np.deg2rad(float(polarization_angle_degree))
    electric_field_direction = np.asarray(
        [
            0.0,
            float(np.cos(polarization_radians)),
            float(np.sin(polarization_radians)),
        ],
        dtype=float,
    )

    k_traces = _build_incident_vector_traces(
        label="k",
        origin=shared_origin,
        tip=np.asarray([-0.14, 0.0, 0.0], dtype=float),
        color="#d62728",
        label_offset=np.asarray([0.03, 0.0, 0.08], dtype=float),
        cone_size_reference=0.17,
    )

    electric_field_traces = _build_incident_vector_traces(
        label="E",
        origin=shared_origin,
        tip=shared_origin + (electric_field_direction * 0.52),
        color="#1f77b4",
        label_offset=np.asarray(
            [
                0.06,
                float(0.07 * np.cos(polarization_radians)),
                float(0.07 * np.sin(polarization_radians)),
            ],
            dtype=float,
        ),
        cone_size_reference=0.15,
    )

    return [
        *k_traces,
        *electric_field_traces,
    ]


def _build_incident_vector_traces(
    *,
    label: str,
    origin: np.ndarray,
    tip: np.ndarray,
    color: str,
    label_offset: np.ndarray,
    cone_size_reference: float,
) -> list[Any]:
    """
    Build matched shaft, cone head, and label traces for one incident vector.
    """
    origin = np.asarray(origin, dtype=float).reshape(3)
    tip = np.asarray(tip, dtype=float).reshape(3)
    label_offset = np.asarray(label_offset, dtype=float).reshape(3)
    origin = _rotate_preview_display_coordinate_array(origin.reshape(1, 3)).reshape(3)
    tip = _rotate_preview_display_coordinate_array(tip.reshape(1, 3)).reshape(3)
    label_offset = _rotate_preview_display_coordinate_array(
        label_offset.reshape(1, 3)
    ).reshape(3)

    vector = tip - origin
    vector_length = float(np.linalg.norm(vector))

    if vector_length == 0.0:
        raise ValueError("Incident vector origin and tip must not be identical.")

    unit_vector = vector / vector_length
    cone_vector = unit_vector * min(0.22, vector_length * 0.34)
    shaft_tip = tip - cone_vector * 0.62
    label_position = tip + label_offset

    shaft_trace = go.Scatter3d(
        x=[float(origin[0]), float(shaft_tip[0])],
        y=[float(origin[1]), float(shaft_tip[1])],
        z=[float(origin[2]), float(shaft_tip[2])],
        mode="lines",
        line={
            "width": 9,
            "color": color,
        },
        hoverinfo="skip",
    )

    arrow_trace = go.Cone(
        x=[float(tip[0])],
        y=[float(tip[1])],
        z=[float(tip[2])],
        u=[float(cone_vector[0])],
        v=[float(cone_vector[1])],
        w=[float(cone_vector[2])],
        sizemode="absolute",
        sizeref=cone_size_reference,
        anchor="tip",
        showscale=False,
        colorscale=[
            [0.0, color],
            [1.0, color],
        ],
        hoverinfo="skip",
    )

    label_trace = go.Scatter3d(
        x=[float(label_position[0])],
        y=[float(label_position[1])],
        z=[float(label_position[2])],
        mode="text",
        text=[label],
        textfont={
            "size": 18,
            "color": color,
        },
        hoverinfo="skip",
    )

    return [
        shaft_trace,
        arrow_trace,
        label_trace,
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
        "showline": False,
        "showbackground": False,
        "showticklabels": False,
        "showspikes": False,
        "zeroline": False,
        "ticks": "",
        "backgroundcolor": "rgba(0,0,0,0)",
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


def _coerce_int(
    value: Any,
    *,
    default: int,
    name: str,
) -> int:
    """
    Convert a value to int, falling back to a default when conversion fails.
    """
    try:
        resolved_value = int(value)
        logger.debug("Coerced %s=%r to int=%r", name, value, resolved_value)
        return resolved_value
    except (TypeError, ValueError):
        logger.warning(
            "Could not coerce %s=%r to int. Using default=%r",
            name,
            value,
            default,
        )
        return int(default)
