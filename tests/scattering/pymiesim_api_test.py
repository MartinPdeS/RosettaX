"""Coupling extraction for both supported PyMieSim result APIs."""

if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))

from types import SimpleNamespace

import numpy as np
import pytest
from pint import UnitRegistry

from RosettaX.workflow.scattering import backend


@pytest.mark.parametrize("labeled_result", [False, True])
def test_coupling_extraction_preserves_values_across_pymiesim_apis(
    monkeypatch, labeled_result
):
    """Extract the same coupling values from the legacy and labeled result APIs."""
    monkeypatch.setattr(backend, "ureg", UnitRegistry())
    expected = np.array([[[1.25, 2.5]]])
    calls = []

    def get(measure, *, as_numpy):
        """Emulate the older NumPy-returning API."""
        assert as_numpy is True
        calls.append(measure)
        return expected

    def run(measure):
        """Emulate the newer labeled result API."""
        calls.append(measure)
        return SimpleNamespace(as_numpy=lambda: expected)

    def build_set(**kwargs):
        """Accept the optical parameters passed to the native set constructors."""
        return kwargs

    experiment = (
        SimpleNamespace(run=run) if labeled_result else SimpleNamespace(get=get)
    )
    monkeypatch.setattr(
        backend,
        "PyMieSim",
        SimpleNamespace(
            polarization_set=SimpleNamespace(PolarizationSet=build_set),
            source_set=SimpleNamespace(GaussianSet=build_set),
            detector_set=SimpleNamespace(PhotodiodeSet=build_set),
            Setup=build_set,
        ),
    )
    monkeypatch.setattr(backend.PyMieSim, "Setup", lambda **kwargs: experiment)
    actual = backend.BackEnd._run_coupling_simulation(
        scatterer_set_builder=lambda: object(),
        wavelength_nm=488.0,
        source_numerical_aperture=0.1,
        optical_power_watt=1.0,
        detector_numerical_aperture=0.4,
        detector_cache_numerical_aperture=0.0,
        detector_phi_offset_degree=0.0,
        detector_gamma_offset_degree=0.0,
        polarization_angle_degree=0.0,
        detector_sampling=100,
    )
    np.testing.assert_array_equal(actual, expected.reshape(-1))
    assert calls == ["coupling"]
