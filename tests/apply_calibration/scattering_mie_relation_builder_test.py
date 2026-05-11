# -*- coding: utf-8 -*-

from types import SimpleNamespace

import numpy as np
import pytest

from RosettaX.workflow.apply_calibration.scattering.mie_relation_builder import (
    build_target_mie_relation,
)
from RosettaX.workflow.apply_calibration.scattering.models import (
    CoreShellSphereTargetModel,
    ScatteringTargetModelParameters,
    SolidSphereTargetModel,
)


class Test_ApplyCalibrationScatteringMieRelationBuilder:
    def test_build_target_mie_relation_for_solid_sphere(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            "RosettaX.workflow.apply_calibration.scattering.mie_relation_builder.BackEnd.compute_modeled_coupling_from_diameters",
            lambda **kwargs: SimpleNamespace(
                particle_diameters_nm=np.asarray(
                    kwargs["particle_diameters_nm"], dtype=float
                ),
                expected_coupling_values=np.asarray([10.0, 20.0, 30.0], dtype=float),
            ),
        )

        relation = build_target_mie_relation(
            calibration_payload={
                "metadata": {
                    "calibration_standard_parameters": {
                        "wavelength_nm": 488.0,
                        "detector_numerical_aperture": 0.4,
                    }
                }
            },
            target_model_parameters=ScatteringTargetModelParameters(
                target_model=SolidSphereTargetModel(
                    medium_refractive_index=1.33,
                    particle_refractive_index=1.45,
                    particle_diameter_min_nm=100.0,
                    particle_diameter_max_nm=300.0,
                    particle_diameter_count=3,
                )
            ),
        )

        assert relation.relation_role == "target_particle"
        assert relation.mie_model == "Solid Sphere"
        assert relation.theoretical_coupling == [10.0, 20.0, 30.0]

    def test_build_target_mie_relation_for_core_shell(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            "RosettaX.workflow.apply_calibration.scattering.mie_relation_builder.BackEnd.compute_modeled_coupling_from_core_shell_dimensions",
            lambda **kwargs: SimpleNamespace(
                expected_coupling_values=np.asarray([5.0, 6.0, 7.0], dtype=float),
            ),
        )

        relation = build_target_mie_relation(
            calibration_payload={
                "metadata": {
                    "calibration_standard_parameters": {
                        "wavelength_nm": 488.0,
                        "detector_numerical_aperture": 0.4,
                    }
                }
            },
            target_model_parameters=ScatteringTargetModelParameters(
                target_model=CoreShellSphereTargetModel(
                    medium_refractive_index=1.33,
                    core_refractive_index=1.45,
                    shell_refractive_index=1.38,
                    shell_thickness_nm=10.0,
                    core_diameter_min_nm=100.0,
                    core_diameter_max_nm=300.0,
                    core_diameter_count=3,
                )
            ),
        )

        assert relation.relation_role == "target_particle"
        assert relation.mie_model == "Core/Shell Sphere"
        assert relation.theoretical_coupling == [5.0, 6.0, 7.0]

    def test_build_target_mie_relation_rejects_unknown_target_model(self) -> None:
        with pytest.raises(TypeError, match="Unsupported target model type"):
            build_target_mie_relation(
                calibration_payload={
                    "metadata": {
                        "calibration_standard_parameters": {
                            "wavelength_nm": 488.0,
                            "detector_numerical_aperture": 0.4,
                        }
                    }
                },
                target_model_parameters=ScatteringTargetModelParameters(
                    target_model=object(),
                ),
            )
