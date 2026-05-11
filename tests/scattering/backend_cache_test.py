# -*- coding: utf-8 -*-

from unittest.mock import patch

import numpy as np

from RosettaX.pages.p03_scattering.backend import BackEnd


class Test_ScatteringBackendCache:
    def test_compute_modeled_coupling_from_diameters_reuses_cached_result(self) -> None:
        BackEnd._compute_cached_solid_sphere_coupling.cache_clear()

        with patch.object(
            BackEnd,
            "_compute_coupling_values_with_fallback",
            return_value=np.asarray([1.0, 2.0], dtype=float),
        ) as mocked_compute:
            first_result = BackEnd.compute_modeled_coupling_from_diameters(
                particle_diameters_nm=np.asarray([100.0, 200.0], dtype=float),
                wavelength_nm=488.0,
                source_numerical_aperture=0.1,
                optical_power_watt=1.0,
                detector_numerical_aperture=0.4,
                medium_refractive_index=1.33,
                particle_refractive_index=1.45,
                detector_cache_numerical_aperture=0.4,
                detector_sampling=100,
            )
            second_result = BackEnd.compute_modeled_coupling_from_diameters(
                particle_diameters_nm=np.asarray([100.0, 200.0], dtype=float),
                wavelength_nm=488.0,
                source_numerical_aperture=0.1,
                optical_power_watt=1.0,
                detector_numerical_aperture=0.4,
                medium_refractive_index=1.33,
                particle_refractive_index=1.45,
                detector_cache_numerical_aperture=0.4,
                detector_sampling=100,
            )

        assert mocked_compute.call_count == 1
        assert first_result.expected_coupling_values.tolist() == [1.0, 2.0]
        assert second_result.expected_coupling_values.tolist() == [1.0, 2.0]
