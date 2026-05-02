# -*- coding: utf-8 -*-

import logging
from types import SimpleNamespace

import numpy as np

from RosettaX.pages.p02_fluorescence.ids import Ids as FluorescenceIds
from RosettaX.pages.p02_fluorescence.sections.s04_calibration.main import Calibration
from RosettaX.workflow.calibration import scattering_services


def _collect_component_ids(component) -> set[str]:
    component_id = getattr(component, "id", None)
    collected_ids = {component_id} if isinstance(component_id, str) else set()
    children = getattr(component, "children", None)

    if children is None:
        return collected_ids

    if isinstance(children, (list, tuple)):
        for child in children:
            collected_ids.update(_collect_component_ids(child))
        return collected_ids

    collected_ids.update(_collect_component_ids(children))
    return collected_ids


class Test_FluorescenceCalibrationLayout:
    def test_layout_includes_calibration_graph_component(self) -> None:
        section = Calibration(
            page=SimpleNamespace(ids=FluorescenceIds()),
            section_number=4,
        )

        layout = section.get_layout()

        assert section.ids.graph_calibration in _collect_component_ids(layout)


class Test_ScatteringCalibrationPreviewGraph:
    def test_preview_store_is_built_from_computed_solid_sphere_rows(
        self,
        monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            scattering_services,
            "build_solid_sphere_dense_simulated_coupling_curve",
            lambda **_: (
                np.asarray([90.0, 210.0], dtype=float),
                np.asarray([0.9, 2.1], dtype=float),
            ),
        )

        figure_store = scattering_services.build_calibration_standard_mie_relation_figure_store(
            mie_model="Solid Sphere",
            current_table_rows=[
                {
                    "particle_diameter_nm": "100",
                    "expected_coupling": "1.0",
                },
                {
                    "particle_diameter_nm": "200",
                    "expected_coupling": "2.0",
                },
            ],
            medium_refractive_index=1.33,
            particle_refractive_index=1.59,
            core_refractive_index=None,
            shell_refractive_index=None,
            wavelength_nm=488.0,
            detector_numerical_aperture=0.4,
            detector_cache_numerical_aperture=0.0,
            blocker_bar_numerical_aperture=0.0,
            detector_sampling=600,
            detector_phi_angle_degree=0.0,
            detector_gamma_angle_degree=0.0,
            simulated_curve_point_count=200,
            logger=logging.getLogger(__name__),
        )

        assert figure_store["layout"]["title"]["text"] == "Calibration standard Mie relation"
        assert [trace["name"] for trace in figure_store["data"]] == [
            "Mie relation (200 points)",
            "Calibration standards",
        ]
