"""Profile state preserves control values and the registered Dash output order."""

# Run pytest before application imports so the suite loads its own dependency setup.
if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-o", "addopts=", "-v"]))


import pytest

from RosettaX.pages.p03_scattering.sections.s03_model.services import (
    resolve_profile_parameter_state,
)


def test_custom_profile_preserves_values_and_clamps_cache_aperture():
    """Check custom profile preserves values and clamps cache aperture."""
    state = resolve_profile_parameter_state(
        {
            "optics": {
                "detector_configuration_preset": "Generic detector",
                "wavelength_nm": 532.0,
                "medium_refractive_index": 1.4,
                "detector_numerical_aperture": 0.4,
                "detector_cache_numerical_aperture": 0.8,
                "blocker_bar_numerical_aperture": 0.1,
                "detector_sampling": 250,
                "detector_phi_angle_degree": 20.0,
                "detector_gamma_angle_degree": 30.0,
            },
            "particle_model": {
                "scatterer_preset": "Custom",
                "mie_model": "Solid Sphere",
                "particle_refractive_index": 1.6,
                "core_refractive_index": 1.5,
                "shell_refractive_index": 1.45,
            },
        }
    )

    assert state.values.detector_cache_numerical_aperture == pytest.approx(0.399999)
    assert state.to_callback_values() == (
        "Generic detector",
        "Custom",
        "Solid Sphere",
        1.4,
        1.6,
        1.5,
        1.45,
        532.0,
        0.4,
        pytest.approx(0.399999),
        0.1,
        250,
        20.0,
        30.0,
    )
