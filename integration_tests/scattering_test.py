"""Numerical contracts exercised through the installed native PyMieSim API."""

import numpy as np
import pytest

from RosettaX.workflow.scattering.backend import BackEnd
from RosettaX.workflow.scattering.mie_relation import build_mie_relation_from_arrays


@pytest.fixture
def optical_parameters():
    return {
        "wavelength_nm": 488.0,
        "source_numerical_aperture": 0.1,
        "optical_power_watt": 1.0,
        "detector_numerical_aperture": 0.4,
        "medium_refractive_index": 1.33,
        # An unobstructed detector: the cache aperture must be below its aperture.
        "detector_cache_numerical_aperture": 0.0,
        "detector_sampling": 100,
    }


def test_solid_sphere_power_scaling_and_cross_section(optical_parameters):
    diameters = np.array([80.0, 120.0, 160.0])
    first = BackEnd.compute_modeled_coupling_from_diameters(
        diameters, particle_refractive_index=1.45, **optical_parameters,
    )
    second = BackEnd.compute_modeled_coupling_from_diameters(
        diameters, particle_refractive_index=1.45,
        **{**optical_parameters, "optical_power_watt": 2.0},
    )
    for result in (first, second):
        np.testing.assert_array_equal(result.particle_diameters_nm, diameters)
        for values in (result.expected_coupling_values, result.expected_cross_section_nm2_values):
            assert values.shape == diameters.shape
            assert np.all(np.isfinite(values))
            assert np.all(values > 0)
    np.testing.assert_allclose(second.expected_coupling_values, 2 * first.expected_coupling_values, rtol=1e-10)
    np.testing.assert_allclose(second.expected_cross_section_nm2_values, first.expected_cross_section_nm2_values, rtol=1e-10)


def test_homogeneous_core_shell_matches_solid_sphere(optical_parameters):
    core_diameters = np.array([60.0, 120.0])
    thicknesses = np.array([10.0, 20.0])
    core_shell = BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
        core_diameters, thicknesses, core_refractive_index=1.45,
        shell_refractive_index=1.45, **optical_parameters,
    )
    solid = BackEnd.compute_modeled_coupling_from_diameters(
        core_diameters + 2 * thicknesses, particle_refractive_index=1.45,
        **optical_parameters,
    )
    np.testing.assert_array_equal(core_shell.particle_diameters_nm, solid.particle_diameters_nm)
    np.testing.assert_allclose(core_shell.expected_coupling_values, solid.expected_coupling_values, rtol=1e-8)
    np.testing.assert_allclose(core_shell.expected_cross_section_nm2_values, solid.expected_cross_section_nm2_values, rtol=1e-8)


def test_core_shell_geometry_is_paired_per_row(optical_parameters):
    cores = np.array([70.0, 130.0])
    shells = np.array([12.0, 24.0])
    parameters = {**optical_parameters, "core_refractive_index": 1.50, "shell_refractive_index": 1.40}
    paired = BackEnd.compute_modeled_coupling_from_core_shell_dimensions(cores, shells, **parameters)
    assert paired.expected_coupling_values.shape == (2,)
    for index in range(2):
        individual = BackEnd.compute_modeled_coupling_from_core_shell_dimensions(
            cores[index:index + 1], shells[index:index + 1], **parameters,
        )
        np.testing.assert_allclose(paired.expected_coupling_values[index], individual.expected_coupling_values[0], rtol=1e-10)
        np.testing.assert_allclose(paired.expected_cross_section_nm2_values[index], individual.expected_cross_section_nm2_values[0], rtol=1e-10)


def test_real_mie_relation_inverts_modeled_diameters(optical_parameters):
    diameters = np.linspace(60.0, 160.0, 11)
    modeled = BackEnd.compute_modeled_coupling_from_diameters(
        diameters, particle_refractive_index=1.45, **optical_parameters,
    )
    relation = build_mie_relation_from_arrays(
        diameter_nm=modeled.particle_diameters_nm,
        theoretical_coupling=modeled.expected_coupling_values,
        mie_model="Solid Sphere", parameters=optical_parameters,
        relation_role="target_particle",
    )
    assert relation.is_monotonic
    np.testing.assert_allclose(relation.coupling_to_diameter(modeled.expected_coupling_values), diameters, rtol=1e-10)
    assert np.isnan(relation.coupling_to_diameter(np.array([0.0]))[0])
