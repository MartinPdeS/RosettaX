# -*- coding: utf-8 -*-

import importlib
import logging
from types import SimpleNamespace

import dash
import numpy as np

from RosettaX.pages.p00_sidebar.main import Sidebar
from RosettaX.pages.p02_fluorescence.ids import Ids as FluorescenceIds
from RosettaX.pages.p02_fluorescence.sections.s04_calibration.main import Calibration
from RosettaX.pages.p03_scattering.ids import Ids as ScatteringIds
from RosettaX.pages.p03_scattering.sections.s03_model.main import Model as ScatteringModel
from RosettaX.pages.p03_scattering.sections.s05_calibration import services as scattering_services


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


def _collect_component_hrefs(component) -> set[str]:
    href = getattr(component, "href", None)
    collected_hrefs = {href} if isinstance(href, str) else set()
    children = getattr(component, "children", None)

    if children is None:
        return collected_hrefs

    if isinstance(children, (list, tuple)):
        for child in children:
            collected_hrefs.update(_collect_component_hrefs(child))
        return collected_hrefs

    collected_hrefs.update(_collect_component_hrefs(children))
    return collected_hrefs


def _find_component_by_id(component, target_id: str):
    component_id = getattr(component, "id", None)

    if component_id == target_id:
        return component

    children = getattr(component, "children", None)

    if children is None:
        return None

    if isinstance(children, (list, tuple)):
        for child in children:
            found_component = _find_component_by_id(child, target_id)

            if found_component is not None:
                return found_component

        return None

    return _find_component_by_id(children, target_id)


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


class Test_ScatteringModelLayout:
    def test_layout_includes_detector_brand_and_model_controls(self) -> None:
        section = ScatteringModel(
            page=SimpleNamespace(ids=ScatteringIds()),
            section_number=3,
        )

        layout = section.get_layout()
        component_ids = _collect_component_ids(layout)

        assert section.ids.detector_configuration_brand in component_ids
        assert section.ids.detector_configuration_model in component_ids
        assert section.ids.detector_configuration_preset in component_ids

        custom_values_container = _find_component_by_id(
            layout,
            section.ids.detector_configuration_custom_values_container,
        )

        assert custom_values_container is not None
        assert section.ids.wavelength_nm in _collect_component_ids(custom_values_container)


class Test_DocumentationPage:
    def test_layout_includes_core_documentation_sections(self, monkeypatch) -> None:
        monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)

        documentation_main = importlib.import_module(
            "RosettaX.pages.p07_documentation.main"
        )
        page = documentation_main.DocumentationPage()

        layout = page.layout()
        component_ids = _collect_component_ids(layout)

        assert page._id("hero") in component_ids
        assert page._id("system-model") in component_ids
        assert page._id("supported-cytometers") in component_ids
        assert page._id("refractive-index") in component_ids
        assert page._id("regression-models") in component_ids
        assert page._id("calibration-files") in component_ids
        assert page._id("apply-checks") in component_ids
        assert page._id("reports") in component_ids


class Test_SidebarNavigation:
    def test_navigation_includes_documentation_link(self) -> None:
        sidebar = Sidebar()

        navigation = sidebar._build_navigation_section()

        assert "/documentation" in _collect_component_hrefs(navigation)
