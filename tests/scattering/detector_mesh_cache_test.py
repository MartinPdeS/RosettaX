"""Mesh caching respects optical configuration and protects cached coordinates."""

from unittest.mock import Mock

import numpy as np

from RosettaX.workflow.detector import mesh


def test_mesh_reuses_geometry_and_invalidates_on_each_optical_parameter(monkeypatch):
    mesh._build_cached_photodiode_mesh_coordinates.cache_clear()
    builder = Mock(wraps=mesh._build_fibonacci_cap_coordinate_array)
    monkeypatch.setattr(mesh, "_build_fibonacci_cap_coordinate_array", builder)
    parameters = dict(
        detector_numerical_aperture=0.4,
        medium_refractive_index=1.333,
        detector_phi_angle_degree=0.0,
        detector_gamma_angle_degree=0.0,
        detector_sampling=100,
    )
    first = mesh.build_pymiesim_photodiode_mesh_coordinates(**parameters)
    expected = first.copy()
    first[:] = 0
    second = mesh.build_pymiesim_photodiode_mesh_coordinates(**parameters)
    np.testing.assert_array_equal(second, expected)
    assert not np.shares_memory(first, second)
    assert builder.call_count == 1
    for key, value in (
        ("detector_numerical_aperture", 0.5),
        ("medium_refractive_index", 1.4),
        ("detector_phi_angle_degree", 20),
        ("detector_gamma_angle_degree", 30),
        ("detector_sampling", 200),
    ):
        mesh.build_pymiesim_photodiode_mesh_coordinates(**{**parameters, key: value})
    assert builder.call_count == 6
    mesh._build_cached_photodiode_mesh_coordinates.cache_clear()


def test_large_mesh_is_not_retained():
    mesh._build_cached_photodiode_mesh_coordinates.cache_clear()
    mesh.build_pymiesim_photodiode_mesh_coordinates(
        detector_numerical_aperture=0.4,
        medium_refractive_index=1.333,
        detector_phi_angle_degree=0,
        detector_gamma_angle_degree=0,
        detector_sampling=20_001,
    )
    assert mesh._build_cached_photodiode_mesh_coordinates.cache_info().currsize == 0
