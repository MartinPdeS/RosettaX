# -*- coding: utf-8 -*-

import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd

from RosettaX.pages.p03_scattering.sections.s05_calibration import (
    services as calibration_services,
)
from RosettaX.workflow.apply_calibration.scattering import (
    ScatteringTargetModelParameters,
    SolidSphereTargetModel,
    apply_scattering_calibration_to_dataframe,
)


def _fake_modeled_coupling_from_diameters(*args, **kwargs) -> SimpleNamespace:
    particle_diameters_nm = np.asarray(
        kwargs["particle_diameters_nm"],
        dtype=float,
    ).reshape(-1)
    expected_coupling_values = particle_diameters_nm * 1e-8

    return SimpleNamespace(
        particle_diameters_nm=particle_diameters_nm,
        expected_coupling_values=expected_coupling_values,
    )


class Test_ScatteringRoundTrip:
    def test_synthetic_solid_sphere_calibration_roundtrips_reference_peaks(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            calibration_services.BackEnd,
            "compute_modeled_coupling_from_diameters",
            staticmethod(_fake_modeled_coupling_from_diameters),
        )
        monkeypatch.setattr(
            "RosettaX.workflow.apply_calibration.scattering.mie_relation_builder.BackEnd.compute_modeled_coupling_from_diameters",
            _fake_modeled_coupling_from_diameters,
        )

        calibration_result = calibration_services.run_scattering_calibration(
            uploaded_fcs_path="/tmp/synthetic.fcs",
            detector_column="SSC-A",
            mie_model="Solid Sphere",
            bead_table_data=[
                {
                    "particle_diameter_nm": "100",
                    "measured_peak_position": "10000",
                },
                {
                    "particle_diameter_nm": "200",
                    "measured_peak_position": "20000",
                },
            ],
            medium_refractive_index=1.333,
            particle_refractive_index=1.59,
            core_refractive_index=1.59,
            shell_refractive_index=1.59,
            wavelength_nm=405.0,
            detector_numerical_aperture=1.2,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            detector_sampling=32,
            detector_phi_angle_degree=28.0,
            detector_gamma_angle_degree=0.0,
            detector_configuration_preset="",
            simulated_curve_point_count=32,
            logger=logging.getLogger(__name__),
        )

        assert calibration_result.calibration_store is not None
        assert calibration_result.apply_status == "Instrument response fitted successfully."

        apply_result = apply_scattering_calibration_to_dataframe(
            dataframe=pd.DataFrame(
                {
                    "SSC-A": [10000.0, 20000.0],
                }
            ),
            source_channel="SSC-A",
            output_channel_names=["nm"],
            calibration_payload=calibration_result.calibration_store,
            target_model_parameters=ScatteringTargetModelParameters(
                target_model=SolidSphereTargetModel(
                    medium_refractive_index=1.333,
                    particle_refractive_index=1.59,
                    particle_diameter_min_nm=50.0,
                    particle_diameter_max_nm=250.0,
                    particle_diameter_count=201,
                )
            ),
        )

        assert apply_result.output_columns == ["", "nm"]
        assert list(apply_result.dataframe.columns) == ["SSC-A", "nm"]
        assert np.allclose(
            apply_result.dataframe["nm"].to_numpy(),
            np.asarray([100.0, 200.0], dtype=float),
            atol=1e-9,
        )
        assert any(
            "100 nm @ 10000 -> 100 nm" in warning
            and "200 nm @ 20000 -> 200 nm" in warning
            for warning in apply_result.warnings
        )

